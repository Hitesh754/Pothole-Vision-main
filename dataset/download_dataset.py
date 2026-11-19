import os
import argparse
from pathlib import Path
import numpy as np
import cv2

def create_sample_dataset(output_dir: str):
    """
    Generates synthetic road surface images with simulated potholes and cracks.
    Useful for local pipeline validation without downloading gigabytes of raw data.
    """
    base = Path(output_dir)
    splits = {
        "train": 16,
        "val": 4,
        "test": 2
    }

    print(f"Generating synthetic verification dataset at: {base.resolve()}")

    for split, count in splits.items():
        img_dir = base / "images" / split
        lbl_dir = base / "labels" / split
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i in range(count):
            # Generate asphalt-like noisy background
            h, w = 640, 640
            asphalt = np.random.normal(loc=110, scale=25, size=(h, w, 3)).clip(0, 255).astype(np.uint8)

            # Draw 1 to 3 simulated potholes (dark irregular ellipses with rough edges)
            num_potholes = np.random.randint(1, 4)
            labels = []

            for _ in range(num_potholes):
                cx = np.random.randint(100, 540)
                cy = np.random.randint(100, 540)
                rx = np.random.randint(25, 80)
                ry = np.random.randint(20, 60)
                angle = np.random.randint(0, 180)

                # Depressed road core (dark gray/black)
                cv2.ellipse(asphalt, (cx, cy), (rx, ry), angle, 0, 360, (35, 35, 35), -1)
                # Outer deteriorated rim
                cv2.ellipse(asphalt, (cx, cy), (rx + 6, ry + 6), angle, 0, 360, (70, 70, 70), 3)

                # Normalized coordinates for YOLO format
                bw = (rx * 2 + 16) / w
                bh = (ry * 2 + 16) / h
                nxc = cx / w
                nyc = cy / h
                labels.append(f"0 {nxc:.6f} {nyc:.6f} {bw:.6f} {bh:.6f}")

            # Save synthetic image and corresponding label file
            img_path = img_dir / f"synth_pothole_{split}_{i:03d}.jpg"
            lbl_path = lbl_dir / f"synth_pothole_{split}_{i:03d}.txt"

            cv2.imwrite(str(img_path), asphalt)
            with open(lbl_path, "w", encoding="utf-8") as f:
                f.write("\n".join(labels) + "\n")

    print("Sample dataset successfully created.")

def print_rdd2022_instructions():
    """Prints instructions for loading the full RDD2022 benchmark dataset."""
    print("=" * 60)
    print("Road Damage Dataset (RDD2022) Setup Instructions")
    print("=" * 60)
    print("1. Download RDD2022 from the official IEEE BigData Cup / GitHub:")
    print("   https://github.com/sekilab/RoadDamageDetector")
    print("2. Pothole target class corresponds to 'D40' in RDD2022 labels.")
    print("3. Convert Pascal VOC XML annotations to YOLO format:")
    print("   Class mapping: D40 -> 0 (pothole)")
    print("4. Place converted images and labels in dataset/images/ and dataset/labels/.")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset manager for RoadSense AI")
    parser.add_argument("--synth", action="store_true", help="Generate synthetic samples for testing")
    parser.add_argument("--dir", type=str, default="./dataset", help="Target dataset directory")
    args = parser.parse_args()

    if args.synth:
        create_sample_dataset(args.dir)
    else:
        print_rdd2022_instructions()
        create_sample_dataset(args.dir)

