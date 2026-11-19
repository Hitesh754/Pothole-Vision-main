import numpy as np
import pytest
from src.severity import SeverityScoringEngine

def test_critical_severity_large_pothole():
    engine = SeverityScoringEngine()
    # Pothole taking up large portion of frame (e.g. 300x300 in 640x640)
    bbox = (100, 100, 400, 400)
    frame_shape = (640, 640)
    conf = 0.92

    result = engine.evaluate(bbox, frame_shape, conf)
    assert result["priority"] in ["P1_CRITICAL", "P2_HIGH"]
    assert result["severity_score"] >= 0.50
    assert result["area_ratio"] > 0.10

def test_minor_severity_small_pothole():
    engine = SeverityScoringEngine()
    # Small pitting defect (20x20 in 640x640)
    bbox = (50, 50, 70, 70)
    frame_shape = (640, 640)
    conf = 0.45

    result = engine.evaluate(bbox, frame_shape, conf)
    assert result["priority"] == "P4_MINOR"
    assert result["severity_score"] < 0.40

def test_depth_cue_dark_contrast():
    engine = SeverityScoringEngine()
    # Frame with light asphalt background and dark pothole center
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 160
    frame[80:120, 80:120] = 30 # Dark crater
    bbox = (80, 80, 120, 120)

    cue = engine.compute_depth_cue(frame, bbox)
    assert cue > 0.30

