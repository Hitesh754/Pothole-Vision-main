import cv2
import numpy as np
from typing import Tuple, Optional

class RoadImagePreprocessor:
    """
    Standardizes citizen-captured road imagery before model inference.
    Handles contrast variations, road glare, and sensor noise.
    """
    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        apply_clahe: bool = True,
        clahe_clip_limit: float = 2.0,
        clahe_grid_size: Tuple[int, int] = (8, 8),
        apply_bilateral: bool = True
    ):
        self.target_size = target_size
        self.apply_clahe = apply_clahe
        self.apply_bilateral = apply_bilateral
        self.clahe = cv2.createCLAHE(
            clipLimit=clahe_clip_limit,
            tileGridSize=clahe_grid_size
        ) if apply_clahe else None

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Applies CLAHE on the luminance channel to reveal texture in shadowed road areas."""
        if not self.apply_clahe or self.clahe is None:
            return image
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = self.clahe.apply(l)
        lab_enhanced = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    def denoise_asphalt(self, image: np.ndarray) -> np.ndarray:
        """Smooths high-frequency asphalt noise while retaining sharp edge boundaries."""
        if not self.apply_bilateral:
            return image
        return cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

    def letterbox(
        self,
        image: np.ndarray,
        new_shape: Tuple[int, int] = (640, 640),
        color: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[int, int]]:
        """
        Resizes and pads image to target size while preserving original aspect ratio.
        Returns padded image, scale ratio, and pad dimensions (dw, dh).
        """
        shape = image.shape[:2] # current [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Compute padding
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2 # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:
            image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        image = cv2.copyMakeBorder(
            image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )
        return image, r, (dw, dh)

    def process(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, Tuple[int, int]]:
        """
        Full preprocessing pipeline.
        Returns:
            - preprocessed_display: contrast-enhanced BGR image
            - letterboxed: resized and padded tensor-ready image
            - ratio: scaling factor
            - padding: (dw, dh) padding offsets
        """
        enhanced = self.enhance_contrast(image)
        filtered = self.denoise_asphalt(enhanced)
        letterboxed, ratio, padding = self.letterbox(filtered, self.target_size)
        return filtered, letterboxed, ratio, padding

