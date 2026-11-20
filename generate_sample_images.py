"""
generate_sample_images.py - Generate Sample Test Images for PotholeVerify Demo
Creates 4 sample images in sample_images/ to demonstrate all verification paths:
1. genuine_pothole.jpg -> Genuine camera EXIF, GPS, fresh timestamp (Accept)
2. ai_generated_pothole.jpg -> Embedded AI generator metadata (Reject via Hard Rule)
3. spliced_pothole.jpg -> Edited patch with compression mismatch (ELA fail)
4. web_download_pothole.jpg -> No metadata (simulating web download) but clean pixels (Accept)
"""

import os
import io
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import numpy as np

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_images")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def create_realistic_pothole(width=4032, height=3024):
    """Create a realistic-looking synthetic pothole on asphalt background."""
    # Start with a uniform grey base
    arr = np.random.normal(loc=90, scale=8, size=(height, width, 3)).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    draw = ImageDraw.Draw(img)

    # Road surface texture - subtle horizontal lines
    for y in range(0, height, 3):
        shade = int(np.random.normal(85, 5))
        draw.line([(0, y), (width, y)], fill=(shade, shade, shade), width=1)

    # Pothole cavity (dark, irregular shape)
    cx, cy = width // 2, height // 2
    rx, ry = width // 5, height // 6
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(30, 30, 35), outline=(20, 20, 25), width=4)
    draw.ellipse([cx - rx + 30, cy - ry + 20, cx + rx - 30, cy + ry - 20], fill=(18, 18, 22))

    # Road marking line
    draw.rectangle([20, 20, width - 20, 50], fill=(210, 190, 45))

    return img


def generate_all_samples():
    print("Generating sample demo images in 'sample_images/'...")

    # 1. Genuine Pothole Photo (high-res, full EXIF)
    img1 = create_realistic_pothole(4032, 3024)
    exif1 = img1.getexif()
    exif1[0x010F] = "Sony"
    exif1[0x0110] = "ILCE-7M4"

    t_fresh = (datetime.now() - timedelta(hours=3)).strftime("%Y:%m:%d %H:%M:%S")
    exif1.get_ifd(0x8769)[0x9003] = t_fresh
    exif1[0x0132] = t_fresh

    gps_ifd = exif1.get_ifd(0x8825)
    gps_ifd[1] = "N"
    gps_ifd[2] = (12, 58, 17.76)
    gps_ifd[3] = "E"
    gps_ifd[4] = (77, 35, 40.56)

    path1 = os.path.join(SAMPLES_DIR, "1_genuine_pothole.jpg")
    img1.save(path1, format="JPEG", exif=exif1, quality=95)
    print(f"  ✓ Created: {path1} (4032×3024, full EXIF)")

    # 2. AI Generated Pothole (Midjourney metadata, 1024x1024)
    img2 = create_realistic_pothole(1024, 1024)
    exif2 = img2.getexif()
    exif2[0x0131] = "Midjourney v6.0 Diffusion Model"
    path2 = os.path.join(SAMPLES_DIR, "2_ai_generated_pothole.jpg")
    img2.save(path2, format="JPEG", exif=exif2, quality=95)
    print(f"  ✓ Created: {path2} (1024×1024, AI metadata)")

    # 3. Spliced / Tampered Photo (compression mismatch for ELA)
    base = create_realistic_pothole(2000, 1500)
    buf_low = io.BytesIO()
    base.save(buf_low, format="JPEG", quality=35)
    buf_low.seek(0)
    spliced = Image.open(buf_low).copy()
    # Paste uncompressed high-contrast foreign block
    draw_sp = ImageDraw.Draw(spliced)
    for i in range(400, 1600, 20):
        draw_sp.line([(i, 400), (i, 1100)], fill=(255, 0, 255), width=8)
    draw_sp.rectangle([500, 500, 1500, 1000], fill=(0, 255, 255))

    path3 = os.path.join(SAMPLES_DIR, "3_spliced_tampered_pothole.jpg")
    spliced.save(path3, format="JPEG", quality=98)
    print(f"  ✓ Created: {path3} (2000×1500, spliced patch)")

    # 4. Web Download — no EXIF but genuine-looking pixels (high-res)
    img4 = create_realistic_pothole(3264, 2448)
    path4 = os.path.join(SAMPLES_DIR, "4_web_download_pothole.jpg")
    img4.save(path4, format="JPEG", quality=92)  # No EXIF injected
    print(f"  ✓ Created: {path4} (3264×2448, no metadata)")

    print("\nSample generation complete!")


if __name__ == "__main__":
    generate_all_samples()
