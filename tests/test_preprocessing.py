import numpy as np
import pytest
from src.preprocessing import RoadImagePreprocessor

def test_letterbox_dimensions():
    preprocessor = RoadImagePreprocessor(target_size=(640, 640))
    # Test rectangular aspect ratio
    test_img = np.zeros((480, 720, 3), dtype=np.uint8)
    letterboxed, ratio, (dw, dh) = preprocessor.letterbox(test_img, new_shape=(640, 640))

    assert letterboxed.shape == (640, 640, 3)
    assert ratio > 0.0
    assert dw >= 0
    assert dh >= 0

def test_clahe_enhancement():
    preprocessor = RoadImagePreprocessor(apply_clahe=True)
    test_img = np.ones((100, 100, 3), dtype=np.uint8) * 50
    enhanced = preprocessor.enhance_contrast(test_img)

    assert enhanced.shape == test_img.shape
    assert enhanced.dtype == np.uint8

def test_full_pipeline_output():
    preprocessor = RoadImagePreprocessor(target_size=(640, 640))
    test_img = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    filtered, letterboxed, ratio, padding = preprocessor.process(test_img)

    assert filtered.shape == (300, 400, 3)
    assert letterboxed.shape == (640, 640, 3)

