"""
test_pothole_verify.py - Unit and Integration Tests for PotholeVerify
Tests all 8 checks, scoring calculations, hard reject rules, and database functions.
"""

import os
import io
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

import checks
import scoring
import db

TEST_DB = "test_pothole.db"


def clean_test_db():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass


def create_test_image(
    add_camera=True,
    add_gps=True,
    add_time=True,
    ai_software=None,
    width=3000,
    height=4000,
    lat=12.9716,
    lon=77.5946,
    hours_ago=2.0,
) -> tuple[bytes, Image.Image]:
    """Helper to synthesize test images with specific properties."""
    img = Image.new("RGB", (width, height), color=(120, 140, 160))
    draw = ImageDraw.Draw(img)
    # Draw shapes to simulate a pothole scene
    draw.ellipse([80, 80, 220, 220], fill=(40, 40, 40), outline=(20, 20, 20))
    # Add some texture variation for realistic noise patterns
    for y in range(0, height, 50):
        for x in range(0, width, 50):
            if (x + y) % 100 == 0:
                draw.rectangle([x, y, x + 20, y + 20], fill=(110, 130, 150))

    exif = img.getexif()

    if add_camera:
        exif[0x010F] = "Nikon"  # Make
        exif[0x0110] = "D850"   # Model

    if ai_software:
        exif[0x0131] = ai_software  # Software tag

    if add_time:
        target_time = datetime.now() - timedelta(hours=hours_ago)
        time_str = target_time.strftime("%Y:%m:%d %H:%M:%S")
        exif_ifd = exif.get_ifd(0x8769)
        exif_ifd[0x9003] = time_str  # DateTimeOriginal
        exif[0x0132] = time_str       # Image DateTime fallback

    if add_gps:
        gps_ifd = exif.get_ifd(0x8825)
        gps_ifd[1] = "N" if lat >= 0 else "S"
        lat_d = int(abs(lat))
        lat_m = int((abs(lat) - lat_d) * 60)
        lat_s = round(((abs(lat) - lat_d) * 60 - lat_m) * 60, 2)
        gps_ifd[2] = (lat_d, lat_m, lat_s)

        gps_ifd[3] = "E" if lon >= 0 else "W"
        lon_d = int(abs(lon))
        lon_m = int((abs(lon) - lon_d) * 60)
        lon_s = round(((abs(lon) - lon_d) * 60 - lon_m) * 60, 2)
        gps_ifd[4] = (lon_d, lon_m, lon_s)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif, quality=95)
    img_bytes = buf.getvalue()
    buf.seek(0)
    pil_loaded = Image.open(buf)

    return img_bytes, pil_loaded


def run_tests():
    print("=" * 60)
    print("Running PotholeVerify Test Suite (v2 — Pixel-Level Focus)")
    print("=" * 60)
    clean_test_db()
    db.init_db(TEST_DB)

    # ----------------------------------------------------
    # Test 1: Camera EXIF Check & AI Penalty
    # ----------------------------------------------------
    print("\n[Test 1] Camera EXIF & AI Generator Tag Check")
    # A: Genuine Camera -> +10 bonus
    bytes1, img1 = create_test_image(add_camera=True)
    c1_pass, c1_pts, c1_reason, ai_found = checks.check_camera_exif(bytes1, img1)
    assert c1_pass is True and c1_pts == 10 and not ai_found, f"FAIL: {c1_reason}"
    print(f"  ✓ Genuine camera -> +10 bonus ({c1_reason})")

    # B: AI-Tagged image -> -50
    bytes_ai, img_ai = create_test_image(ai_software="Stable Diffusion v2.1")
    _, c1_ai_pts, _, ai_found = checks.check_camera_exif(bytes_ai, img_ai)
    assert ai_found is True and c1_ai_pts == -50, f"FAIL AI detection"
    print(f"  ✓ AI tag detected -> -50 penalty, ai_tag_found=True")

    # C: Stripped metadata (web download) -> 0 bonus, NOT a penalty
    bytes_no_exif, img_no_exif = create_test_image(add_camera=False, add_gps=False, add_time=False)
    c1_no_pass, c1_no_pts, c1_no_reason, _ = checks.check_camera_exif(bytes_no_exif, img_no_exif)
    assert c1_no_pass is None and c1_no_pts == 0, f"FAIL: {c1_no_reason}"
    print(f"  ✓ Missing EXIF -> 0 bonus (no penalty)")

    # ----------------------------------------------------
    # Test 2: GPS Check
    # ----------------------------------------------------
    print("\n[Test 2] GPS Proximity Check (Bonus)")
    c2_pass, c2_pts, _ = checks.check_gps(bytes1, img1, 12.9716, 77.5946)
    assert c2_pass is True and c2_pts == 10
    print(f"  ✓ GPS match -> +10 bonus")

    c2_no_pass, c2_no_pts, _ = checks.check_gps(bytes_no_exif, img_no_exif, 12.9716, 77.5946)
    assert c2_no_pass is None and c2_no_pts == 0
    print(f"  ✓ Missing GPS -> 0 bonus (no penalty)")

    # ----------------------------------------------------
    # Test 3: Freshness Check
    # ----------------------------------------------------
    print("\n[Test 3] Freshness Check (Bonus)")
    c3_pass, c3_pts, _ = checks.check_freshness(bytes1, img1)
    assert c3_pass is True and c3_pts == 5
    print(f"  ✓ Fresh (2h old) -> +5 bonus")

    c3_no_pass, c3_no_pts, _ = checks.check_freshness(bytes_no_exif, img_no_exif)
    assert c3_no_pass is None and c3_no_pts == 0
    print(f"  ✓ Missing timestamp -> 0 bonus (no penalty)")

    # ----------------------------------------------------
    # Test 4: Duplicate Detection (pHash)
    # ----------------------------------------------------
    print("\n[Test 4] Duplicate Check via pHash")
    known_hashes = db.get_known_hashes(TEST_DB)
    c4_pass, c4_pts, _, hash1 = checks.check_duplicate(img1, known_hashes)
    assert c4_pass is True and c4_pts == 15
    print(f"  ✓ Unique photo -> +15 pts (hash: {hash1})")

    db.save_report("test1.jpg", hash1, 12.97, 77.59, 85, "Accept", [], TEST_DB)
    known_hashes = db.get_known_hashes(TEST_DB)
    c4_dup_pass, c4_dup_pts, _, _ = checks.check_duplicate(img1, known_hashes)
    assert c4_dup_pass is False and c4_dup_pts == 0
    print(f"  ✓ Duplicate detected -> 0 pts")

    # ----------------------------------------------------
    # Test 5: Error Level Analysis (ELA)
    # ----------------------------------------------------
    print("\n[Test 5] Error Level Analysis")
    c5_pass, c5_pts, c5_reason, heatmap = checks.check_ela(img1)
    assert isinstance(heatmap, Image.Image)
    print(f"  ✓ ELA on clean image: pts={c5_pts} ({c5_reason})")

    # Spliced image: low-quality base + high-contrast patch
    base = Image.new("RGB", (200, 200), (150, 150, 150))
    buf_low = io.BytesIO()
    base.save(buf_low, format="JPEG", quality=40)
    buf_low.seek(0)
    spliced = Image.open(buf_low).copy()
    draw_sp = ImageDraw.Draw(spliced)
    for i in range(20, 180, 10):
        draw_sp.line([(i, 20), (i, 180)], fill=(255, 0, 255), width=5)
    c5_sp_pass, c5_sp_pts, c5_sp_reason, _ = checks.check_ela(spliced)
    assert c5_sp_pts == 0
    print(f"  ✓ ELA on spliced image: pts={c5_sp_pts} ({c5_sp_reason})")

    # ----------------------------------------------------
    # Test 6: Noise Consistency Analysis (NEW)
    # ----------------------------------------------------
    print("\n[Test 6] Noise Consistency Analysis")
    c6_pass, c6_pts, c6_reason = checks.check_noise_consistency(img1)
    print(f"  ✓ Noise analysis on camera photo: pts={c6_pts} ({c6_reason})")

    # Test on a small image (should handle gracefully)
    tiny = Image.new("RGB", (32, 32), (100, 100, 100))
    c6_tiny_pass, c6_tiny_pts, c6_tiny_reason = checks.check_noise_consistency(tiny)
    assert c6_tiny_pts == 20
    print(f"  ✓ Tiny image handled gracefully: pts={c6_tiny_pts}")

    # ----------------------------------------------------
    # Test 7: JPEG Quality Consistency (NEW)
    # ----------------------------------------------------
    print("\n[Test 7] JPEG Quality Consistency")
    c7_pass, c7_pts, c7_reason = checks.check_jpeg_quality_consistency(img1, bytes1)
    print(f"  ✓ Quality analysis on single-save: pts={c7_pts} ({c7_reason})")

    # ----------------------------------------------------
    # Test 8: Image Dimensions (NEW)
    # ----------------------------------------------------
    print("\n[Test 8] AI-Typical Dimension Detection")
    # Real camera resolution (3000x4000)
    c8_pass, c8_pts, c8_reason = checks.check_image_dimensions(img1)
    assert c8_pts == 10
    print(f"  ✓ Camera resolution (3000x4000) -> +10 pts")

    # AI-typical resolution (1024x1024)
    ai_img = Image.new("RGB", (1024, 1024), (100, 100, 100))
    c8_ai_pass, c8_ai_pts, c8_ai_reason = checks.check_image_dimensions(ai_img)
    assert c8_ai_pts == 0
    print(f"  ✓ AI resolution (1024x1024) -> 0 pts ({c8_ai_reason})")

    # AI-typical resolution (512x768)
    ai_img2 = Image.new("RGB", (512, 768), (100, 100, 100))
    c8_ai2_pass, c8_ai2_pts, _ = checks.check_image_dimensions(ai_img2)
    assert c8_ai2_pts == 0
    print(f"  ✓ AI resolution (512x768) -> 0 pts")

    # ----------------------------------------------------
    # Test 9: Scoring & Decision (Updated Thresholds)
    # ----------------------------------------------------
    print("\n[Test 9] Scoring & Decision Logic")

    # Scenario A: Web-downloaded image, no EXIF, all pixel checks pass
    # ELA(20) + Noise(20) + JPEG(15) + Duplicate(15) + Dims(10) = 80, no metadata = 0
    checks_web_good = [
        {"name": "ELA", "passed": True, "points": 20, "max_points": 20, "reason": "ok"},
        {"name": "Noise", "passed": True, "points": 20, "max_points": 20, "reason": "ok"},
        {"name": "JPEG", "passed": True, "points": 15, "max_points": 15, "reason": "ok"},
        {"name": "Dup", "passed": True, "points": 15, "max_points": 15, "reason": "ok"},
        {"name": "Dims", "passed": True, "points": 10, "max_points": 10, "reason": "ok"},
        {"name": "EXIF", "passed": None, "points": 0, "max_points": 10, "reason": "missing"},
        {"name": "GPS", "passed": None, "points": 0, "max_points": 10, "reason": "missing"},
        {"name": "Fresh", "passed": None, "points": 0, "max_points": 5, "reason": "missing"},
    ]
    res_web = scoring.compute_final_decision(checks_web_good, ai_tag_found=False)
    assert res_web["score"] == 80
    assert res_web["decision"] == "Accept"
    print(f"  ✓ Web image, all pixel checks pass: score={res_web['score']}, decision={res_web['decision']}")

    # Scenario B: Full camera photo with metadata
    checks_full = list(checks_web_good)
    checks_full[5] = {"name": "EXIF", "passed": True, "points": 10, "max_points": 10, "reason": "ok"}
    checks_full[6] = {"name": "GPS", "passed": True, "points": 10, "max_points": 10, "reason": "ok"}
    checks_full[7] = {"name": "Fresh", "passed": True, "points": 5, "max_points": 5, "reason": "ok"}
    res_full = scoring.compute_final_decision(checks_full, ai_tag_found=False)
    assert res_full["score"] == 100 and res_full["decision"] == "Accept"
    print(f"  ✓ Full camera photo: score={res_full['score']}, decision={res_full['decision']}")

    # Scenario C: Hard AI reject
    res_ai = scoring.compute_final_decision(checks_full, ai_tag_found=True)
    assert res_ai["decision"] == "Reject"
    print(f"  ✓ AI hard reject regardless of score")

    # Scenario D: Review zone (35-59)
    checks_mixed = list(checks_web_good)
    checks_mixed[0] = {"name": "ELA", "passed": False, "points": 0, "max_points": 20, "reason": "fail"}
    checks_mixed[1] = {"name": "Noise", "passed": False, "points": 0, "max_points": 20, "reason": "fail"}
    # 0 + 0 + 15 + 15 + 10 + 0 + 0 + 0 = 40
    res_review = scoring.compute_final_decision(checks_mixed, ai_tag_found=False)
    assert res_review["decision"] == "Review"
    print(f"  ✓ Mixed results: score={res_review['score']}, decision={res_review['decision']}")

    # ----------------------------------------------------
    # Test 10: Database & Admin Workflow
    # ----------------------------------------------------
    print("\n[Test 10] Database & Admin Review Workflow")
    rep_id = db.save_report(
        "uploads/pending.jpg", "abcdef1234567890", 12.97, 77.59, 45, "Review", checks_mixed, TEST_DB
    )
    pending = db.get_pending_reviews(TEST_DB)
    assert len(pending) == 1
    print("  ✓ Report logged under Review status")

    db.update_report_decision(rep_id, "Accept", TEST_DB)
    assert len(db.get_pending_reviews(TEST_DB)) == 0
    print("  ✓ Admin approved: cleared from review queue")

    clean_test_db()
    print("\n" + "=" * 60)
    print("All PotholeVerify Tests Passed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
