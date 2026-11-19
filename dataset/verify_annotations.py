import os
import sys
from pathlib import Path
import cv2

def verify_dataset(base_dir: str):
    """
    Validates image readability and YOLO annotation formatting.
    Ensures normalized coordinates are strictly between 0 and 1.
    """
    base_path = Path(base_dir)
    splits = ["train", "val", "test"]
    stats = {}

    print(f"Starting dataset verification in: {base_path.resolve()}")

    for split in splits:
        img_dir = base_path / "images" / split
        lbl_dir = base_path / "labels" / split

        if not img_dir.exists():
            print(f"Split directory not found: {img_dir}. Skipping.")
            continue

        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpeg"))
        valid_pairs = 0
        corrupt_images = 0
        invalid_labels = 0
        missing_labels = 0

        for img_path in images:
            # Check image integrity
            img = cv2.imread(str(img_path))
            if img is None:
                corrupt_images += 1
                continue

            h, w = img.shape[:2]
            label_file = lbl_dir / f"{img_path.stem}.txt"

            if not label_file.exists():
                missing_labels += 1
                continue

            # Check bbox validity
            try:
                with open(label_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) < 5:
                        invalid_labels += 1
                        break
                    cls_id = int(parts[0])
                    xc, yc, bw, bh = map(float, parts[1:5])
                    if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < bw <= 1.0 and 0.0 < bh <= 1.0):
                        invalid_labels += 1
                        break
                else:
                    valid_pairs += 1
            except Exception:
                invalid_labels += 1

        stats[split] = {
            "total_images": len(images),
            "valid_annotated_pairs": valid_pairs,
            "corrupt_images": corrupt_images,
            "missing_labels": missing_labels,
            "invalid_labels": invalid_labels
        }

    print("\nDataset Verification Summary:")
    print("-" * 50)
    for split, info in stats.items():
        print(f"Split [{split}]:")
        for k, v in info.items():
            print(f"  {k}: {v}")
    print("-" * 50)
    return stats

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "./dataset"
    verify_dataset(target)

