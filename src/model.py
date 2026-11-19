import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import cv2
import numpy as np

from src.preprocessing import RoadImagePreprocessor
from src.severity import SeverityScoringEngine

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

class PotholeDetector:
    """
    Main inference interface for RoadSense AI pothole detection.
    Combines input preprocessing, YOLOv8 object detection, and severity assessment.
    """
    def __init__(
        self,
        weights_path: str = "yolov8s.pt",
        conf_threshold: float = 0.40,
        iou_threshold: float = 0.45,
        device: str = "cpu",
        use_preprocessing: bool = True
    ):
        self.weights_path = weights_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.use_preprocessing = use_preprocessing

        self.preprocessor = RoadImagePreprocessor()
        self.severity_engine = SeverityScoringEngine()
        self.model = None

        self._load_model()

    def _load_model(self):
        """Loads YOLOv8 model weights or initial architecture."""
        if not HAS_ULTRALYTICS:
            print("Warning: ultralytics package not detected. Running in mock/fallback mode.")
            return

        try:
            self.model = YOLO(self.weights_path)
            print(f"Loaded YOLOv8 model from {self.weights_path} on {self.device}.")
        except Exception as e:
            print(f"Could not load weights from {self.weights_path}: {e}")
            print("Attempting to load default yolov8n.pt...")
            try:
                self.model = YOLO("yolov8n.pt")
            except Exception as inner_e:
                print(f"Failed to load fallback model: {inner_e}")
                self.model = None

    def detect(
        self,
        image_input: Union[str, np.ndarray],
        return_annotated: bool = True
    ) -> Dict[str, Any]:
        """
        Runs complete detection and severity scoring pipeline on an input image.
        Accepts file path or BGR numpy array.
        """
        if isinstance(image_input, str):
            image = cv2.imread(image_input)
            if image is None:
                raise ValueError(f"Unable to read image at path: {image_input}")
        else:
            image = image_input.copy()

        orig_h, orig_w = image.shape[:2]

        # Contrast enhancement and filtering
        if self.use_preprocessing:
            processed_img, _, _, _ = self.preprocessor.process(image)
        else:
            processed_img = image

        detections: List[Dict[str, Any]] = []

        if self.model is not None:
            # Model inference
            results = self.model.predict(
                source=processed_img,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False
            )

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names.get(cls_id, "pothole")

                    # Severity assessment
                    sev = self.severity_engine.evaluate(
                        bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                        frame_shape=(orig_h, orig_w),
                        confidence=conf,
                        full_image=image
                    )

                    detections.append({
                        "class_id": cls_id,
                        "class_name": class_name,
                        "confidence": round(conf, 3),
                        "bbox": [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
                        "severity": sev
                    })
        else:
            # Fallback heuristic detector for development testing without model weights
            detections = self._heuristic_fallback(image)

        # Sort detections by severity score descending
        detections.sort(key=lambda x: x["severity"]["severity_score"], reverse=True)

        # Build composite status
        highest_priority = detections[0]["severity"]["priority"] if detections else "NO_DAMAGE_DETECTED"

        annotated_image = None
        if return_annotated:
            annotated_image = self.render_annotations(image, detections)

        return {
            "total_detections": len(detections),
            "highest_priority": highest_priority,
            "detections": detections,
            "annotated_image": annotated_image,
            "image_dimensions": {"height": orig_h, "width": orig_w}
        }

    def _heuristic_fallback(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Lightweight contour detector for testing when neural weights are not yet trained.
        Flags dark irregular depressions on road surface.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = image.shape[:2]
        min_area = (h * w) * 0.005
        max_area = (h * w) * 0.25

        fallback_results = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                x, y, bw, bh = cv2.boundingRect(cnt)
                conf = 0.55
                sev = self.severity_engine.evaluate(
                    bbox=(x, y, x + bw, y + bh),
                    frame_shape=(h, w),
                    confidence=conf,
                    full_image=image
                )
                fallback_results.append({
                    "class_id": 0,
                    "class_name": "pothole",
                    "confidence": conf,
                    "bbox": [x, y, x + bw, y + bh],
                    "severity": sev
                })
        return fallback_results

    def render_annotations(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Draws bounding boxes, priority tags, and severity labels on the image."""
        canvas = image.copy()
        palette = {
            "P1_CRITICAL": (0, 0, 220), # Red
            "P2_HIGH": (0, 140, 255), # Orange
            "P3_MEDIUM": (0, 215, 255), # Yellow
            "P4_MINOR": (0, 200, 0) # Green
        }

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            priority = det["severity"]["priority"]
            score = det["severity"]["severity_score"]
            conf = det["confidence"]

            color = palette.get(priority, (255, 255, 255))

            # Bounding box
            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

            # Label banner
            label = f"{det['class_name']} {conf:.2f} | {priority} ({score:.2f})"
            (lw, lh), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(canvas, (x1, max(0, y1 - lh - 8)), (x1 + lw + 6, max(0, y1)), color, -1)
            cv2.putText(
                canvas,
                label,
                (x1 + 3, max(0, y1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return canvas

    def export_onnx(self, output_path: str = "weights/pothole_yolov8s.onnx") -> Optional[str]:
        """Exports the loaded PyTorch model to ONNX format for deployment."""
        if self.model is None:
            print("Cannot export: model is not loaded.")
            return None
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            path = self.model.export(format="onnx", dynamic=True)
            print(f"Model successfully exported to: {path}")
            return path
        except Exception as e:
            print(f"ONNX export error: {e}")
            return None

