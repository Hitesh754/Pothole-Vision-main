"""
checks.py - Heuristic Verification Checks for PotholeVerify
Contains 8 standalone, modular verification checks:

PIXEL-LEVEL ANALYSIS (works on ANY image, even stripped metadata):
1. Camera EXIF & AI Generator Tag Detection
2. GPS Location & Proximity Verification
3. Freshness / Capture Timestamp Check
4. Duplicate Image Detection via Perceptual Hashing (pHash)
5. Error Level Analysis (ELA) for Tampering / Splicing Detection
6. Noise Consistency Analysis - detects splicing via noise variance patterns
7. JPEG Quantization Table Analysis - detects double compression / editing
8. AI-Typical Dimension Check - flags standard AI generator resolutions
"""

import io
import math
from datetime import datetime
from PIL import Image
import exifread
import imagehash
import numpy as np

# Keywords used to flag AI-generated images
AI_KEYWORDS = [
    "stable diffusion",
    "midjourney",
    "dall-e",
    "firefly",
    "comfyui",
    "automatic1111",
]

# Common AI generator output resolutions (width x height)
AI_TYPICAL_DIMENSIONS = {
    (256, 256), (512, 512), (768, 768), (1024, 1024), (2048, 2048),
    (512, 768), (768, 512),
    (768, 1024), (1024, 768),
    (768, 1344), (1344, 768),
    (896, 1152), (1152, 896),
    (1024, 1536), (1536, 1024),
    (1024, 1792), (1792, 1024),
    (1024, 1820), (1820, 1024),
}


def check_camera_exif(
    image_bytes: bytes, pil_img: Image.Image
) -> tuple[bool | None, int, str, bool]:
    """
    Check 1: Camera EXIF Metadata and AI Generation Signatures.
    - Scans for Camera Make and Model -> bonus +10 points if present.
    - Scans EXIF Software tag, raw XMP bytes, and PNG text chunks for
      AI generation signatures. If found: ai_tag_found = True, penalty -50.

    Returns:
        (passed: bool | None, points: int, reason: str, ai_tag_found: bool)
    """
    ai_tag_found = False
    ai_detected_keyword = None

    # Step A: Scan raw image bytes (covers XMP packets, embedded metadata, PNG chunks)
    raw_text = image_bytes.lower()
    for kw in AI_KEYWORDS:
        if kw.encode("utf-8") in raw_text:
            ai_tag_found = True
            ai_detected_keyword = kw
            break

    # Step B: Scan PNG metadata dictionary / text chunks if applicable
    if not ai_tag_found and hasattr(pil_img, "info") and pil_img.info:
        for k, v in pil_img.info.items():
            combined = f"{k} {v}".lower()
            for kw in AI_KEYWORDS:
                if kw in combined:
                    ai_tag_found = True
                    ai_detected_keyword = kw
                    break
            if ai_tag_found:
                break

    # Step C: Read EXIF tags with exifread on original bytes (for JPEG/TIFF)
    tags = {}
    if not image_bytes.startswith(b"\x89PNG"):
        try:
            tags = exifread.process_file(io.BytesIO(image_bytes), details=True)
        except Exception:
            tags = {}

    # Check EXIF Software tag specifically
    if not ai_tag_found:
        software_tag = str(
            tags.get("Image Software") or tags.get("EXIF Software") or ""
        ).lower()
        for kw in AI_KEYWORDS:
            if kw in software_tag:
                ai_tag_found = True
                ai_detected_keyword = kw
                break

    # If AI generator footprint is detected -> hard penalty
    if ai_tag_found:
        return (
            False,
            -50,
            f"AI generator footprint detected: '{ai_detected_keyword}' found in image metadata.",
            True,
        )

    # Step D: Check for Make & Model
    make = tags.get("Image Make") or tags.get("EXIF Make")
    model = tags.get("Image Model") or tags.get("EXIF Model")

    # Pillow EXIF fallback
    if not (make or model):
        try:
            exif = pil_img.getexif()
            if exif:
                make = exif.get(0x010F)  # Make
                model = exif.get(0x0110)  # Model
        except Exception:
            pass

    make_str = str(make).strip() if make else ""
    model_str = str(model).strip() if model else ""

    if make_str or model_str:
        device_name = f"{make_str} {model_str}".strip()
        return (
            True,
            10,
            f"Camera hardware metadata verified: {device_name} (bonus points)",
            False,
        )
    else:
        return (
            None,
            0,
            "Camera Make/Model not in metadata (stripped by web/social media — does not reduce score)",
            False,
        )


def _ratio_to_float(ratio) -> float:
    """Helper to convert exifread Ratio or number to float."""
    try:
        return float(ratio.num) / float(ratio.den)
    except AttributeError:
        return float(ratio)


def _extract_gps_coordinates(
    image_bytes: bytes, pil_img: Image.Image
) -> tuple[float | None, float | None]:
    """Extract latitude and longitude in decimal degrees from EXIF."""
    # Attempt 1: exifread (for JPEG/TIFF)
    if not image_bytes.startswith(b"\x89PNG"):
        try:
            tags = exifread.process_file(io.BytesIO(image_bytes), details=False)
            lat_tag = tags.get("GPS GPSLatitude")
            lat_ref = tags.get("GPS GPSLatitudeRef")
            lon_tag = tags.get("GPS GPSLongitude")
            lon_ref = tags.get("GPS GPSLongitudeRef")

            if lat_tag and lat_ref and lon_tag and lon_ref:
                lat_vals = lat_tag.values
                lon_vals = lon_tag.values
                lat = (
                    _ratio_to_float(lat_vals[0])
                    + (_ratio_to_float(lat_vals[1]) / 60.0)
                    + (_ratio_to_float(lat_vals[2]) / 3600.0)
                )
                lon = (
                    _ratio_to_float(lon_vals[0])
                    + (_ratio_to_float(lon_vals[1]) / 60.0)
                    + (_ratio_to_float(lon_vals[2]) / 3600.0)
                )
                if str(lat_ref).strip().upper() == "S":
                    lat = -lat
                if str(lon_ref).strip().upper() == "W":
                    lon = -lon
                return lat, lon
        except Exception:
            pass

    # Attempt 2: Pillow getexif IFD 0x8825 fallback
    try:
        exif = pil_img.getexif()
        if exif:
            gps_ifd = exif.get_ifd(0x8825)
            if gps_ifd:
                lat_vals = gps_ifd.get(2)
                lat_ref = gps_ifd.get(1)
                lon_vals = gps_ifd.get(4)
                lon_ref = gps_ifd.get(3)
                if lat_vals and lat_ref and lon_vals and lon_ref:
                    lat = (
                        float(lat_vals[0])
                        + float(lat_vals[1]) / 60.0
                        + float(lat_vals[2]) / 3600.0
                    )
                    lon = (
                        float(lon_vals[0])
                        + float(lon_vals[1]) / 60.0
                        + float(lon_vals[2]) / 3600.0
                    )
                    if str(lat_ref).strip().upper() == "S":
                        lat = -lat
                    if str(lon_ref).strip().upper() == "W":
                        lon = -lon
                    return lat, lon
    except Exception:
        pass

    return None, None


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two coordinates."""
    R = 6371000.0  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def check_gps(
    image_bytes: bytes, pil_img: Image.Image, user_lat: float, user_lon: float
) -> tuple[bool | None, int, str]:
    """
    Check 2: GPS Location Verification (bonus).
    Reads GPS from EXIF, calculates Haversine distance to user-entered coordinates.
    Distance <= 500m -> +10 bonus points.
    Missing GPS -> 0 points (no penalty).
    Distance > 500m -> 0 points.
    """
    img_lat, img_lon = _extract_gps_coordinates(image_bytes, pil_img)

    if img_lat is None or img_lon is None:
        return None, 0, "GPS not in metadata (stripped by web/social media — does not reduce score)."

    distance = haversine_distance_m(img_lat, img_lon, user_lat, user_lon)

    if distance <= 500.0:
        return (
            True,
            10,
            f"GPS verified: image location ({img_lat:.4f}, {img_lon:.4f}) is {distance:.1f} m from reported coordinates (<= 500 m, bonus points).",
        )
    else:
        return (
            False,
            0,
            f"GPS mismatch: image location ({img_lat:.4f}, {img_lon:.4f}) is {distance:.1f} m away from reported coordinates (> 500 m limit).",
        )


def check_freshness(
    image_bytes: bytes, pil_img: Image.Image, max_age_hours: float = 48.0
) -> tuple[bool | None, int, str]:
    """
    Check 3: Freshness / Timestamp Verification (bonus).
    Checks EXIF DateTimeOriginal is within 48 hours of now -> +5 bonus points.
    Missing -> 0 points (no penalty).
    """
    date_str = None

    # Step 1: Check exifread tags (for JPEG/TIFF)
    if not image_bytes.startswith(b"\x89PNG"):
        try:
            tags = exifread.process_file(io.BytesIO(image_bytes), details=False)
            date_tag = (
                tags.get("EXIF DateTimeOriginal")
                or tags.get("EXIF DateTimeDigitized")
                or tags.get("Image DateTime")
            )
            if date_tag:
                date_str = str(date_tag).strip()
        except Exception:
            pass

    # Step 2: Pillow fallback
    if not date_str:
        try:
            exif = pil_img.getexif()
            if exif:
                # 36867: DateTimeOriginal, 36868: DateTimeDigitized, 306: DateTime
                date_str = exif.get(36867) or exif.get(36868) or exif.get(306)
                if date_str:
                    date_str = str(date_str).strip()
        except Exception:
            pass

    if not date_str:
        return None, 0, "Timestamp not in metadata (stripped by web/social media — does not reduce score)."

    # Parse date format "YYYY:MM:DD HH:MM:SS"
    try:
        cleaned_str = date_str[:19]
        dt = datetime.strptime(cleaned_str, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return (
            False,
            0,
            f"Unparseable timestamp in EXIF: '{date_str}' (expected YYYY:MM:DD HH:MM:SS).",
        )

    now = datetime.now()
    diff_seconds = (now - dt).total_seconds()
    age_hours = diff_seconds / 3600.0

    # Clock skew tolerance: allow up to 1 hour in the future
    if age_hours < -1.0:
        return (
            False,
            0,
            f"Future timestamp detected: {dt.strftime('%Y-%m-%d %H:%M:%S')} is ahead of current time.",
        )
    elif age_hours <= max_age_hours:
        return (
            True,
            5,
            f"Fresh photo: taken {max(0.0, age_hours):.1f} hours ago on {dt.strftime('%Y-%m-%d %H:%M:%S')} (<= 48 h, bonus points).",
        )
    else:
        return (
            False,
            0,
            f"Outdated photo: taken {age_hours:.1f} hours ago on {dt.strftime('%Y-%m-%d %H:%M:%S')} (> 48 h limit).",
        )


def check_duplicate(
    pil_img: Image.Image,
    known_hashes: list[tuple[int, str]],
    distance_threshold: int = 5,
) -> tuple[bool, int, str, str]:
    """
    Check 4: Duplicate Image Detection via Perceptual Hash (pHash).
    Compares pHash against hashes in SQLite (Hamming distance <= 5 = duplicate).
    Not duplicate -> +15 points.

    Returns:
        (passed: bool, points: int, reason: str, hex_hash: str)
    """
    img_hash = imagehash.phash(pil_img)
    hash_str = str(img_hash)

    if not known_hashes:
        return (
            True,
            15,
            f"No existing reports to compare with. Image hash registered: {hash_str}",
            hash_str,
        )

    min_distance = 999999
    matched_id = None

    for rep_id, h_str in known_hashes:
        try:
            stored_hash = imagehash.hex_to_hash(h_str)
            dist = img_hash - stored_hash
            if dist < min_distance:
                min_distance = dist
                matched_id = rep_id
        except Exception:
            continue

    if min_distance <= distance_threshold:
        return (
            False,
            0,
            f"Duplicate or reused image detected! Matches existing report #{matched_id} with Hamming distance {min_distance} (threshold <= {distance_threshold}).",
            hash_str,
        )
    else:
        return (
            True,
            15,
            f"Unique image: closest stored report match distance is {min_distance} (threshold <= {distance_threshold}).",
            hash_str,
        )


def check_ela(
    pil_img: Image.Image,
    quality: int = 90,
    threshold: int = 15,
    max_suspicious_ratio: float = 0.05,
    scale: int = 15,
) -> tuple[bool, int, str, Image.Image]:
    """
    Check 5: Error Level Analysis (ELA).
    Re-saves image as JPEG at quality 90, computes absolute difference, amplifies
    differences for visualization.
    If more than 5% of pixels have difference above threshold 15 -> suspicious (0 points),
    else -> +20 points.

    Returns:
        (passed: bool, points: int, reason: str, heatmap_img: Image.Image)
    """
    # Convert image to RGB
    orig_rgb = pil_img.convert("RGB")

    # Re-save to JPEG in memory
    buffer = io.BytesIO()
    orig_rgb.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    resaved_rgb = Image.open(buffer)

    # Compute absolute difference
    orig_arr = np.array(orig_rgb, dtype=np.int16)
    resaved_arr = np.array(resaved_rgb, dtype=np.int16)
    diff = np.abs(orig_arr - resaved_arr)

    # Max difference per pixel across channels (R, G, B)
    max_diff_per_pixel = np.max(diff, axis=2)
    suspicious_pixels = int(np.sum(max_diff_per_pixel > threshold))
    total_pixels = int(max_diff_per_pixel.size)
    suspicious_ratio = suspicious_pixels / total_pixels
    suspicious_pct = suspicious_ratio * 100.0

    # Amplify difference for heatmap visualization
    amplified = np.clip(diff.astype(np.float32) * scale, 0, 255).astype(np.uint8)
    heatmap_img = Image.fromarray(amplified)

    if suspicious_ratio > max_suspicious_ratio:
        return (
            False,
            0,
            f"Suspicious compression discrepancies: {suspicious_pct:.2f}% of pixels exceed error threshold {threshold} (> 5.0% limit, potential editing or splicing).",
            heatmap_img,
        )
    else:
        return (
            True,
            20,
            f"Uniform compression profile: only {suspicious_pct:.2f}% of pixels exceed error threshold (<= 5.0% limit).",
            heatmap_img,
        )


# =========================================================================
# NEW PIXEL-LEVEL CHECKS (work on any image, no EXIF metadata required)
# =========================================================================

def check_noise_consistency(
    pil_img: Image.Image,
    grid_size: int = 8,
    max_cv: float = 0.45,
) -> tuple[bool, int, str]:
    """
    Check 6: Noise Consistency Analysis.
    Divides the image into a grid of blocks, computes local noise level
    (high-pass filter standard deviation) in each block, then checks how
    uniform the noise is across all blocks.

    Real camera photos have consistent sensor noise across the frame.
    Spliced / composited images have regions with different noise levels
    (e.g., a pasted object from a different camera or compression level).

    Uses coefficient of variation (CV = std / mean) of block noise levels.
    CV <= max_cv (0.45) -> consistent noise -> +20 points.
    CV > max_cv -> inconsistent noise -> 0 points.

    Returns:
        (passed: bool, points: int, reason: str)
    """
    gray = np.array(pil_img.convert("L"), dtype=np.float64)
    h, w = gray.shape

    # Need a minimum size to get meaningful blocks
    if h < 64 or w < 64:
        return (True, 20, "Image too small for noise grid analysis; assumed consistent.")

    block_h = h // grid_size
    block_w = w // grid_size

    # Simple Laplacian-like high-pass kernel convolution via numpy
    # This extracts noise/texture by subtracting a local average
    block_noises = []
    for row in range(grid_size):
        for col in range(grid_size):
            y_start = row * block_h
            x_start = col * block_w
            block = gray[y_start : y_start + block_h, x_start : x_start + block_w]

            # High-pass: subtract blurred version (simple 3x3 average)
            # Using numpy convolution with a simple kernel
            if block.shape[0] < 3 or block.shape[1] < 3:
                continue
            # Compute local noise as standard deviation of Laplacian approximation
            # Laplacian: center pixel * 4 - top - bottom - left - right
            center = block[1:-1, 1:-1]
            top = block[:-2, 1:-1]
            bottom = block[2:, 1:-1]
            left = block[1:-1, :-2]
            right = block[1:-1, 2:]
            laplacian = (4.0 * center) - top - bottom - left - right
            noise_level = np.std(laplacian)
            block_noises.append(noise_level)

    if len(block_noises) < 4:
        return (True, 20, "Not enough blocks for noise analysis; assumed consistent.")

    block_noises = np.array(block_noises)
    mean_noise = np.mean(block_noises)
    std_noise = np.std(block_noises)

    # Avoid division by zero
    if mean_noise < 0.01:
        return (True, 20, "Very low noise level (smooth/synthetic image); noise analysis inconclusive — assumed OK.")

    cv = std_noise / mean_noise  # Coefficient of Variation

    if cv <= max_cv:
        return (
            True,
            20,
            f"Consistent noise profile across {len(block_noises)} image blocks (CV = {cv:.3f} <= {max_cv}). "
            f"Suggests single-source capture without splicing.",
        )
    else:
        return (
            False,
            0,
            f"Inconsistent noise levels detected across image blocks (CV = {cv:.3f} > {max_cv}). "
            f"This may indicate spliced regions from different sources or heavy local editing.",
        )


def check_jpeg_quality_consistency(
    pil_img: Image.Image,
    image_bytes: bytes,
) -> tuple[bool, int, str]:
    """
    Check 7: JPEG Double-Compression / Quality Consistency Analysis.
    Detects if an image has been re-saved (double-compressed) by checking
    the error profile across multiple JPEG quality levels.

    Method: re-save at qualities 50-95 in steps, measure the total absolute
    difference at each level. For a single-compressed JPEG, the minimum error
    occurs near the original save quality. For images that were saved multiple
    times (edited + re-saved), the error curve shows a distinctive dip at a
    quality different from the final save quality, indicating tampering.

    For non-JPEG images (PNG), this check evaluates the overall error
    smoothness as a measure of whether the image was originally a JPEG
    that was converted.

    Returns:
        (passed: bool, points: int, reason: str)
    """
    orig_rgb = pil_img.convert("RGB")
    orig_arr = np.array(orig_rgb, dtype=np.float64)

    # Re-save at multiple quality levels and find error at each
    qualities = list(range(50, 96, 5))
    errors = []
    for q in qualities:
        buf = io.BytesIO()
        orig_rgb.save(buf, format="JPEG", quality=q)
        buf.seek(0)
        resaved = np.array(Image.open(buf), dtype=np.float64)
        mean_abs_error = np.mean(np.abs(orig_arr - resaved))
        errors.append(mean_abs_error)

    errors = np.array(errors)
    min_idx = int(np.argmin(errors))
    min_quality = qualities[min_idx]
    min_error = errors[min_idx]

    # For genuine single-save JPEG: the error minimum is near the high end
    # (quality 85-95) and the curve is smooth and monotonically decreasing
    # toward the original quality. For double-compressed: there's a local
    # minimum at a *lower* quality than expected.

    # Check 1: Is the minimum error very low? (matches original compression)
    # Check 2: Is the curve smooth? (compute second derivative roughness)

    # Compute smoothness: sum of absolute second differences
    if len(errors) >= 3:
        second_diff = np.diff(np.diff(errors))
        roughness = np.mean(np.abs(second_diff))
    else:
        roughness = 0.0

    # Normalize roughness relative to error magnitude
    norm_roughness = roughness / (np.mean(errors) + 0.001)

    # Heuristic thresholds derived from forensic analysis patterns:
    # - Single-compressed: smooth curve, min at high quality, low roughness
    # - Double-compressed: bumpy curve with local minimum at unexpected quality
    is_suspicious = False
    reasons = []

    # Flag if minimum error is at an unusually low quality AND the min error
    # is very close to zero (suggesting the image was saved at that quality)
    if min_quality <= 70 and min_error < 1.0:
        is_suspicious = True
        reasons.append(
            f"error minimum at quality {min_quality} with near-zero error ({min_error:.2f}), "
            f"suggesting re-save from a low-quality JPEG"
        )

    # Flag if the curve is unusually rough (double-compression artifact)
    if norm_roughness > 0.15:
        is_suspicious = True
        reasons.append(
            f"compression curve roughness ({norm_roughness:.3f}) exceeds threshold (0.15), "
            f"suggesting multiple JPEG save cycles"
        )

    if is_suspicious:
        reason_str = "; ".join(reasons)
        return (
            False,
            0,
            f"Double-compression artifacts detected: {reason_str}. "
            f"Image may have been edited and re-saved.",
        )
    else:
        return (
            True,
            15,
            f"Compression profile consistent with single-save image "
            f"(best match at Q{min_quality}, curve roughness {norm_roughness:.3f}). "
            f"No double-compression artifacts found.",
        )


def check_image_dimensions(
    pil_img: Image.Image,
) -> tuple[bool, int, str]:
    """
    Check 8: AI-Typical Image Dimension Detection.
    Many AI image generators (Stable Diffusion, DALL-E, Midjourney) produce
    images at characteristic resolutions like 512x512, 1024x1024, 768x1344,
    etc. Real camera photos have sensor-specific resolutions (e.g., 4032x3024,
    4000x3000, 6000x4000) that rarely match these exact AI dimensions.

    Also checks if width and height are both exact powers of 2 or exact
    multiples of 64 within typical AI ranges.

    Returns:
        (passed: bool, points: int, reason: str)
    """
    w, h = pil_img.size

    # Check 1: Exact match to known AI resolutions
    if (w, h) in AI_TYPICAL_DIMENSIONS:
        return (
            False,
            0,
            f"Image dimensions ({w} × {h}) exactly match a known AI generator output resolution. "
            f"Real camera photos rarely have these exact dimensions.",
        )

    # Check 2: Both dimensions are multiples of 64 AND within AI-typical range
    # (AI generators work in 64-pixel blocks; cameras don't produce such neat numbers)
    both_mult_64 = (w % 64 == 0) and (h % 64 == 0)
    in_ai_range = (256 <= w <= 2048) and (256 <= h <= 2048)

    if both_mult_64 and in_ai_range and w == h:
        # Perfect square with both sides multiple of 64 in AI range
        return (
            False,
            0,
            f"Image dimensions ({w} × {h}) are a perfect square with both sides "
            f"as multiples of 64 — a strong AI generator signature.",
        )

    # Check 3: Very common real-camera resolutions or reasonable aspect ratios
    total_pixels = w * h
    if total_pixels > 2_000_000:  # > 2 megapixels suggests real camera
        return (
            True,
            10,
            f"Image resolution ({w} × {h}, {total_pixels/1_000_000:.1f} MP) is consistent "
            f"with a real camera sensor output.",
        )

    # Smaller images: neutral — could be resized from camera or AI
    return (
        None,
        5,
        f"Image resolution ({w} × {h}, {total_pixels/1_000_000:.1f} MP) is relatively small. "
        f"Could be a resized camera photo or generated image — inconclusive.",
    )
