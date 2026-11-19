import os
import cv2
import numpy as np
import pytest
from src.authenticity import AuthenticityVerifier

def test_ela_computation(tmp_path):
    verifier = AuthenticityVerifier()
    # Create test image
    img_path = str(tmp_path / "test_road.jpg")
    img = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
    cv2.imwrite(img_path, img)

    result = verifier.compute_ela(img_path)
    assert "mean_error" in result
    assert "suspected_tampering" in result
    assert result["status"] in ["PASSED", "FLAGGED"]

def test_phash_computation(tmp_path):
    verifier = AuthenticityVerifier()
    img_path = str(tmp_path / "test_hash.jpg")
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    cv2.imwrite(img_path, img)

    phash = verifier.compute_phash(img_path)
    if phash is not None:
        assert isinstance(phash, str)
        assert len(phash) > 0

