import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional

class SeverityScoringEngine:
    """
    Evaluates physical damage severity of detected potholes.
    Combines normalized surface area, estimated cavity darkness/depth,
    and detector confidence to assign maintenance priority tiers.
    """
    def __init__(
        self,
        area_weight: float = 0.50,
        depth_weight: float = 0.30,
        confidence_weight: float = 0.20,
        critical_threshold: float = 0.70,
        high_threshold: float = 0.50,
        medium_threshold: float = 0.30
    ):
        self.area_weight = area_weight
        self.depth_weight = depth_weight
        self.conf_weight = confidence_weight
        self.critical_thresh = critical_threshold
        self.high_thresh = high_threshold
        self.medium_thresh = medium_threshold

    def compute_depth_cue(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> float:
        """
        Estimates depth cue using interior darkness contrast against asphalt perimeter.
        Deeper craters and water-filled voids exhibit lower diffuse reflectance.
        """
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]

        # Clamp coordinates
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if (x2 - x1) < 5 or (y2 - y1) < 5:
            return 0.0

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        roi = gray[y1:y2, x1:x2]

        # Surround margin to calculate local asphalt baseline
        pad_x = max(5, int((x2 - x1) * 0.2))
        pad_y = max(5, int((y2 - y1) * 0.2))
        sx1, sy1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
        sx2, sy2 = min(w, x2 + pad_x), min(h, y2 + pad_y)

        surround_roi = gray[sy1:sy2, sx1:sx2]
        surround_mean = float(np.mean(surround_roi)) if surround_roi.size > 0 else 128.0
        roi_mean = float(np.mean(roi))

        if surround_mean <= 1.0:
            return 0.0

        # Relative darkness ratio clamped between 0 and 1
        contrast = max(0.0, (surround_mean - roi_mean) / surround_mean)
        return float(np.clip(contrast * 1.5, 0.0, 1.0))

    def evaluate(
        self,
        bbox: Tuple[int, int, int, int],
        frame_shape: Tuple[int, int],
        confidence: float,
        full_image: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Calculates severity index and maps to standard PWD repair priority tiers.
        """
        x1, y1, x2, y2 = bbox
        img_h, img_w = frame_shape[:2]
        frame_area = float(img_h * img_w)

        box_w = max(0, x2 - x1)
        box_h = max(0, y2 - y1)
        box_area = float(box_w * box_h)

        # Fraction of frame occupied by the defect
        area_ratio = box_area / frame_area if frame_area > 0 else 0.0

        # Normalize area score (capped at 15% of frame for 1.0 score)
        norm_area_score = float(np.clip(area_ratio / 0.15, 0.0, 1.0))

        # Compute depth cue if image is supplied
        depth_score = self.compute_depth_cue(full_image, bbox) if full_image is not None else 0.40

        # Weighted composite severity index
        severity_score = (
            self.area_weight * norm_area_score +
            self.depth_weight * depth_score +
            self.conf_weight * float(np.clip(confidence, 0.0, 1.0))
        )
        severity_score = round(float(np.clip(severity_score, 0.0, 1.0)), 3)

        # Tier classification
        if severity_score >= self.critical_thresh or area_ratio >= 0.10:
            priority = "P1_CRITICAL"
            action = "Immediate hazard to traffic. Emergency asphalt cold-mix patching within 24-48 hours."
            est_repair_urgency = "URGENT"
        elif severity_score >= self.high_thresh or area_ratio >= 0.05:
            priority = "P2_HIGH"
            action = "High risk of vehicle damage and water pooling. Scheduled repair within 3-7 days."
            est_repair_urgency = "HIGH"
        elif severity_score >= self.medium_thresh:
            priority = "P3_MEDIUM"
            action = "Moderate surface disintegration. Include in weekly municipal maintenance batch."
            est_repair_urgency = "MEDIUM"
        else:
            priority = "P4_MINOR"
            action = "Early stage surface wear. Log coordinates and monitor progression."
            est_repair_urgency = "LOW"

        return {
            "severity_score": severity_score,
            "priority": priority,
            "urgency": est_repair_urgency,
            "area_ratio": round(area_ratio, 4),
            "depth_factor": round(depth_score, 3),
            "recommended_action": action
        }
