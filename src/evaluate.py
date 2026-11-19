import argparse
from pathlib import Path
import yaml

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

def run_evaluation(
    weights_path: str = "runs/train/pothole_yolov8/weights/best.pt",
    data_yaml: str = "dataset/data.yaml",
    img_size: int = 640,
    device: str = "cpu"
):
    """
    Evaluates detector performance on the held-out test or validation split.
    Calculates precision, recall, mAP50, and mAP50-95.
    """
    if not HAS_ULTRALYTICS:
        raise ImportError("ultralytics package is required for model evaluation.")

    if not Path(weights_path).exists():
        print(f"Target weights not found at: {weights_path}")
        print("Falling back to yolov8s.pt baseline evaluation.")
        weights_path = "yolov8s.pt"

    print(f"Loading weights from {weights_path} for validation on {data_yaml}...")
    model = YOLO(weights_path)

    metrics = model.val(
        data=data_yaml,
        imgsz=img_size,
        device=device,
        split="val",
        verbose=True
    )

    print("\n" + "=" * 50)
    print("RoadSense AI - Model Evaluation Results")
    print("=" * 50)
    print(f"Precision:        {metrics.box.mp:.4f}")
    print(f"Recall:           {metrics.box.mr:.4f}")
    print(f"mAP @ 0.50:       {metrics.box.map50:.4f}")
    print(f"mAP @ 0.50:0.95:  {metrics.box.map:.4f}")
    print(f"Inference Speed:  {metrics.speed['inference']:.2f} ms per image")
    print(f"Pre-process Speed:{metrics.speed['preprocess']:.2f} ms per image")
    print(f"Post-process Speed:{metrics.speed['postprocess']:.2f} ms per image")
    print("=" * 50)

    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate pothole detection model")
    parser.add_argument("--weights", type=str, default="runs/train/pothole_yolov8/weights/best.pt")
    parser.add_argument("--data", type=str, default="dataset/data.yaml")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    run_evaluation(
        weights_path=args.weights,
        data_yaml=args.data,
        img_size=args.imgsz,
        device=args.device
    )

