import os
import sys
import json
import argparse
from pathlib import Path
import cv2

from src.model import PotholeDetector

def run_prediction(
    source_path: str,
    weights_path: str = "yolov8s.pt",
    conf: float = 0.40,
    iou: float = 0.45,
    output_dir: str = "runs/predict",
    device: str = "cpu"
):
    """
    Runs detection on a single image, folder, or video stream.
    Saves annotated results and structured JSON records.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    detector = PotholeDetector(
        weights_path=weights_path,
        conf_threshold=conf,
        iou_threshold=iou,
        device=device
    )

    src = Path(source_path)
    if not src.exists():
        print(f"Error: Source path not found: {source_path}")
        return

    # Collect target files
    if src.is_dir():
        extensions = ["*.jpg", "*.png", "*.jpeg", "*.bmp"]
        image_files = []
        for ext in extensions:
            image_files.extend(list(src.glob(ext)))
    elif src.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]:
        # Handle video stream
        _process_video(detector, str(src), str(out_dir / f"annotated_{src.name}"))
        return
    else:
        image_files = [src]

    print(f"Processing {len(image_files)} image(s)...")
    all_reports = {}

    for img_path in image_files:
        result = detector.detect(str(img_path), return_annotated=True)

        # Save annotated image
        if result["annotated_image"] is not None:
            save_path = out_dir / f"pred_{img_path.name}"
            cv2.imwrite(str(save_path), result["annotated_image"])

        # Format detection summary
        clean_result = {
            "file": img_path.name,
            "total_detections": result["total_detections"],
            "highest_priority": result["highest_priority"],
            "detections": result["detections"]
        }
        all_reports[img_path.name] = clean_result

        print(f"[{img_path.name}] Found: {result['total_detections']} defect(s) | Priority: {result['highest_priority']}")
        for d in result["detections"]:
            print(f"  - Conf: {d['confidence']:.2f} | BBox: {d['bbox']} | {d['severity']['priority']} (Score: {d['severity']['severity_score']})")

    # Save consolidated JSON output
    json_path = out_dir / "detections_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_reports, f, indent=2)
    print(f"\nAnnotated outputs and report saved in: {out_dir.resolve()}")

def _process_video(detector: PotholeDetector, video_path: str, out_path: str):
    """Processes video frame-by-frame and writes annotated stream."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    print(f"Processing video: {video_path} ({width}x{height} @ {fps:.1f} fps)")
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        res = detector.detect(frame, return_annotated=True)
        if res["annotated_image"] is not None:
            out.write(res["annotated_image"])
        else:
            out.write(frame)

        frame_idx += 1
        if frame_idx % 30 == 0:
            print(f"Processed {frame_idx} frames...")

    cap.release()
    out.release()
    print(f"Video processing finished. Output saved to: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run pothole detection on images or video")
    parser.add_argument("--source", type=str, required=True, help="Path to image, directory, or video")
    parser.add_argument("--weights", type=str, default="yolov8s.pt", help="Path to model weights")
    parser.add_argument("--conf", type=float, default=0.40, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold")
    parser.add_argument("--output", type=str, default="runs/predict", help="Output directory")
    parser.add_argument("--device", type=str, default="cpu", help="Device ('cpu' or '0')")
    args = parser.parse_args()

    run_prediction(
        source_path=args.source,
        weights_path=args.weights,
        conf=args.conf,
        iou=args.iou,
        output_dir=args.output,
        device=args.device
    )

