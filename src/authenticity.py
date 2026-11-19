import os
import io
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from typing import Dict, Any, Optional

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

class AuthenticityVerifier:
    """
    Multi-layer authenticity and anti-spoofing checker for citizen road reports.
    Implements Error Level Analysis (ELA) and Perceptual Hashing (pHash).
    """
    def __init__(
        self,
        ela_quality: int = 90,
        ela_threshold: float = 35.0,
        duplicate_distance_threshold: int = 5
    ):
        self.ela_quality = ela_quality
        self.ela_threshold = ela_threshold
        self.duplicate_distance_threshold = duplicate_distance_threshold

    def compute_ela(self, image_path: str, scale: float = 15.0) -> Dict[str, Any]:
        """
        Calculates Error Level Analysis (ELA) score.
        High average error indicates image tampering or composite splicing.
        """
        try:
            original = Image.open(image_path).convert("RGB")
            buffer = io.BytesIO()
            original.save(buffer, "JPEG", quality=self.ela_quality)
            buffer.seek(0)
            resaved = Image.open(buffer)

            # Difference between original and recompressed image
            diff = ImageChops.difference(original, resaved)
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema]) if extrema else 0

            # Scale error for quantitative evaluation
            scale_factor = scale if max_diff == 0 else max(1.0, 255.0 / max_diff)
            enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale_factor)

            diff_arr = np.array(diff, dtype=np.float32)
            mean_error = float(np.mean(diff_arr))

            is_tampered = mean_error > self.ela_threshold
            return {
                "mean_error": round(mean_error, 3),
                "max_diff": int(max_diff),
                "suspected_tampering": is_tampered,
                "status": "FLAGGED" if is_tampered else "PASSED"
            }
        except Exception as e:
            return {
                "error": str(e),
                "suspected_tampering": False,
                "status": "ERROR"
            }

    def compute_phash(self, image_path: str) -> Optional[str]:
        """Calculates 64-bit perceptual hash to identify duplicate submissions."""
        if not HAS_IMAGEHASH:
            return None
        try:
            with Image.open(image_path) as img:
                return str(imagehash.phash(img))
        except Exception:
            return None

    def is_duplicate(self, target_hash_hex: str, known_hashes: list) -> Dict[str, Any]:
        """Compares target pHash against known database hashes using Hamming distance."""
        if not HAS_IMAGEHASH or not target_hash_hex:
            return {"is_duplicate": False, "min_distance": None}

        try:
            target_hash = imagehash.hex_to_hash(target_hash_hex)
            min_dist = 999
            matched_hash = None

            for known_hex in known_hashes:
                kh = imagehash.hex_to_hash(known_hex)
                dist = target_hash - kh # Hamming distance
                if dist < min_dist:
                    min_dist = dist
                    matched_hash = known_hex

            is_dup = min_dist <= self.duplicate_distance_threshold
            return {
                "is_duplicate": is_dup,
                "min_distance": int(min_dist) if min_dist != 999 else None,
                "matched_hash": matched_hash if is_dup else None
            }
        except Exception as e:
            return {"is_duplicate": False, "error": str(e)}

    def extract_metadata(self, image_path: str) -> Dict[str, Any]:
        """Checks for EXIF metadata presence (timestamp, GPS coordinates)."""
        try:
            with Image.open(image_path) as img:
                exif = img.getexif()
                if not exif:
                    return {"has_exif": False, "gps_present": False}
                
                # Check for standard GPS Info IFD tag (0x8825)
                has_gps = 0x8825 in exif or 34853 in exif
                return {
                    "has_exif": True,
                    "gps_present": bool(has_gps),
                    "tags_count": len(exif)
                }
        except Exception:
            return {"has_exif": False, "gps_present": False}

    def verify_all(self, image_path: str, known_hashes: Optional[list] = None) -> Dict[str, Any]:
        """Runs complete verification suite on submitted image."""
        ela_res = self.compute_ela(image_path)
        phash_val = self.compute_phash(image_path)
        dup_res = self.is_duplicate(phash_val, known_hashes or []) if phash_val else {"is_duplicate": False}
        meta_res = self.extract_metadata(image_path)

        passed = (not ela_res.get("suspected_tampering", False)) and (not dup_res.get("is_duplicate", False))

        return {
            "verified": passed,
            "ela": ela_res,
            "phash": phash_val,
            "duplicate_check": dup_res,
            "metadata": meta_res
        }

