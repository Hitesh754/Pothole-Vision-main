import os
import argparse
from pathlib import Path
import yaml

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

def load_config(config_path: str = "config.yaml") -> dict:
    """Loads configuration yaml file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_training(
    data_yaml: str = "dataset/data.yaml",
    weights: str = "yolov8s.pt",
    epochs: int = 80,
    batch_size: int = 16,
    img_size: int = 640,
    device: str = "cpu",
    patience: int = 15,
    project: str = "runs/train",
    name: str = "pothole_yolov8"
):
    """
    Executes transfer learning on the pothole dataset using YOLOv8.
    """
    if not HAS_ULTRALYTICS:
        raise ImportError("ultralytics package is required to execute training.")

    print(f"Initializing YOLOv8 training with base weights: {weights}")
    print(f"Dataset config: {data_yaml} | Target image size: {img_size} | Epochs: {epochs}")

    # Initialize model
    model = YOLO(weights)

    # Train model with hyperparameters tuned for road defects
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        patience=patience,
        save=True,
        project=project,
        name=name,
        exist_ok=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        # Augmentation settings for asphalt road textures
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0
    )

    print(f"Training complete. Weights and metrics saved in {project}/{name}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 pothole detector")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs")
    parser.add_argument("--batch", type=int, default=None, help="Override batch size")
    parser.add_argument("--weights", type=str, default=None, help="Override base weights")
    parser.add_argument("--device", type=str, default=None, help="Device to use ('cpu' or '0')")
    args = parser.parse_args()

    cfg = load_config(args.config)
    t_cfg = cfg.get("training", {})
    m_cfg = cfg.get("model", {})

    data_file = t_cfg.get("data_yaml", "dataset/data.yaml")
    epochs_val = args.epochs or t_cfg.get("epochs", 80)
    batch_val = args.batch or t_cfg.get("batch_size", 16)
    weights_val = args.weights or m_cfg.get("weights", "yolov8s.pt")
    device_val = args.device or m_cfg.get("device", "cpu")
    img_size_val = t_cfg.get("image_size", 640)
    patience_val = t_cfg.get("patience", 15)

    run_training(
        data_yaml=data_file,
        weights=weights_val,
        epochs=epochs_val,
        batch_size=batch_val,
        img_size=img_size_val,
        device=device_val,
        patience=patience_val
    )

