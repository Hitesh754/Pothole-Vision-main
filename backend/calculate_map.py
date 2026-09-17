#!/usr/bin/env python3
"""
Pothole Vision / Civic Guard object detection evaluation script.
This script calculates standard computer vision performance metrics:
- Mean Average Precision at IoU 0.50 (mAP@50)
- Mean Average Precision over IoU 0.50 to 0.95 (mAP@50:95)
- Precision, Recall, and F1-score per damage class.

Supports:
1. Pure Python calculations on custom JSON labels / predictions.
2. Native YOLO validation (if path to best.pt and data.yaml are supplied).
3. Synthetic playground file generator to test metrics out-of-the-box.
"""

import os
import json
import argparse
import logging
from typing import Dict, List, Tuple, Set
import numpy as np

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("mAP-Calculator")


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculates the Intersection over Union (IoU) of two bounding boxes.
    Format: [xmin, ymin, xmax, ymax]
    """
    x_min_inter = max(box1[0], box2[0])
    y_min_inter = max(box1[1], box2[1])
    x_max_inter = min(box1[2], box2[2])
    y_max_inter = min(box1[3], box2[3])

    inter_width = max(0.0, x_max_inter - x_min_inter)
    inter_height = max(0.0, y_max_inter - y_min_inter)
    intersection_area = inter_width * inter_height

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - intersection_area

    if union_area <= 0:
        return 0.0
    return intersection_area / union_area


def calculate_ap_all_points(recalls: np.ndarray, precisions: np.ndarray) -> float:
    """
    Calculates the Average Precision (AP) using the all-point interpolation method (COCO standard).
    """
    if len(recalls) == 0 or len(precisions) == 0:
        return 0.0

    # Ensure arrays are sorted by recall
    sort_indices = np.argsort(recalls)
    rec_sorted = recalls[sort_indices]
    prec_sorted = precisions[sort_indices]

    # Append boundaries
    mrec = np.concatenate(([0.0], rec_sorted, [1.0]))
    mpre = np.concatenate(([0.0], prec_sorted, [0.0]))

    # Compute the precision envelope (monotonically decreasing)
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])

    # Integrate the area under the PR curve
    indices = np.where(mrec[1:] != mrec[:-1])[0]
    ap = float(np.sum((mrec[indices + 1] - mrec[indices]) * mpre[indices + 1]))
    return ap


def calculate_class_ap(
    gt_boxes: List[Dict], 
    pred_boxes: List[Dict], 
    iou_threshold: float = 0.5
) -> Tuple[float, float, float, float]:
    """
    Calculates Average Precision, final Precision, final Recall, and F1-score for a single class.
    
    gt_boxes: list of {"image_id": str, "box": [xmin, ymin, xmax, ymax]}
    pred_boxes: list of {"image_id": str, "box": [xmin, ymin, xmax, ymax], "confidence": float}
    """
    total_gts = len(gt_boxes)
    if total_gts == 0:
        # If there are no ground truths but we made predictions, we have 0 recall & 0 precision
        return 0.0, 0.0, 0.0, 0.0

    if len(pred_boxes) == 0:
        return 0.0, 0.0, 0.0, 0.0

    # Sort predictions by confidence in descending order
    preds_sorted = sorted(pred_boxes, key=lambda x: x["confidence"], reverse=True)

    # Initialize lists to track True Positives (TP) and False Positives (FP)
    tp = np.zeros(len(preds_sorted))
    fp = np.zeros(len(preds_sorted))

    # Keep track of which ground truth boxes have been matched
    # Key: (image_id, index_in_gt_list)
    matched_gts: Set[Tuple[str, int]] = set()

    # Group ground truths by image_id for faster index lookup
    gt_by_img: Dict[str, List[Tuple[int, List[float]]]] = {}
    for idx, gt in enumerate(gt_boxes):
        img_id = gt["image_id"]
        if img_id not in gt_by_img:
            gt_by_img[img_id] = []
        gt_by_img[img_id].append((idx, gt["box"]))

    # Match predictions to ground truths
    for pred_idx, pred in enumerate(preds_sorted):
        img_id = pred["image_id"]
        pred_box = pred["box"]

        # If there are no ground truths in this image for this class, it's a False Positive
        if img_id not in gt_by_img:
            fp[pred_idx] = 1
            continue

        best_iou = -1.0
        best_gt_idx = -1

        # Calculate IoU with all ground truths in the same image
        for gt_idx, gt_box in gt_by_img[img_id]:
            # Skip if this specific ground truth was already matched
            if (img_id, gt_idx) in matched_gts:
                continue
            
            iou = calculate_iou(pred_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx

        # If the best match meets the IoU criteria, count as TP
        if best_iou >= iou_threshold and best_gt_idx != -1:
            tp[pred_idx] = 1
            matched_gts.add((img_id, best_gt_idx))
        else:
            fp[pred_idx] = 1

    # Cumulative TP and FP arrays
    tp_cum = np.cumsum(tp)
    fp_cum = np.cumsum(fp)

    # Calculate precision and recall curves
    precisions = tp_cum / (tp_cum + fp_cum)
    recalls = tp_cum / total_gts

    # Final overall precision and recall at the end of the lists
    eps = 1e-16
    final_p = float(tp_cum[-1] / (tp_cum[-1] + fp_cum[-1] + eps))
    final_r = float(tp_cum[-1] / total_gts)
    final_f1 = float(2 * (final_p * final_r) / (final_p + final_r + eps))

    ap = calculate_ap_all_points(recalls, precisions)
    return ap, final_p, final_r, final_f1


def calculate_map(
    ground_truths: Dict[str, List[Dict]], 
    predictions: List[Dict], 
    classes: List[str]
) -> Dict:
    """
    Computes overall mAP metrics.
    
    ground_truths: Dict class_name -> list of {"image_id": str, "box": [xmin, ymin, xmax, ymax]}
    predictions: List of {"image_id": str, "class_name": str, "box": [xmin, ymin, xmax, ymax], "confidence": float}
    classes: List of class names
    """
    metrics = {
        "classes": {},
        "mAP@50": 0.0,
        "mAP@50:95": 0.0,
        "mean_precision": 0.0,
        "mean_recall": 0.0,
        "mean_f1": 0.0
    }

    ap50_sum = 0.0
    ap50_95_sum = 0.0
    precision_sum = 0.0
    recall_sum = 0.0
    f1_sum = 0.0

    # COCO standard IoU thresholds: 0.50 to 0.95 with steps of 0.05
    iou_thresholds = np.arange(0.50, 1.00, 0.05)

    for class_name in classes:
        gts = ground_truths.get(class_name, [])
        preds = [p for p in predictions if p["class_name"] == class_name]

        # Calculate AP at 0.50
        ap50, p, r, f1 = calculate_class_ap(gts, preds, iou_threshold=0.50)

        # Calculate AP across all thresholds (0.50:0.95)
        ap_steps = []
        for thresh in iou_thresholds:
            ap_t, _, _, _ = calculate_class_ap(gts, preds, iou_threshold=thresh)
            ap_steps.append(ap_t)
        ap50_95 = float(np.mean(ap_steps))

        metrics["classes"][class_name] = {
            "AP@50": round(ap50, 4),
            "AP@50:95": round(ap50_95, 4),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f1, 4),
            "gt_count": len(gts),
            "pred_count": len(preds)
        }

        ap50_sum += ap50
        ap50_95_sum += ap50_95
        precision_sum += p
        recall_sum += r
        f1_sum += f1

    num_classes = len(classes)
    if num_classes > 0:
        metrics["mAP@50"] = round(ap50_sum / num_classes, 4)
        metrics["mAP@50:95"] = round(ap50_95_sum / num_classes, 4)
        metrics["mean_precision"] = round(precision_sum / num_classes, 4)
        metrics["mean_recall"] = round(recall_sum / num_classes, 4)
        metrics["mean_f1"] = round(f1_sum / num_classes, 4)

    return metrics


def generate_synthetic_data() -> Tuple[Dict[str, List[Dict]], List[Dict], List[str]]:
    """
    Generates synthetic ground truths and predictions mimicking real-world
    pothole and road damage detections (the "Civic Guard" system context).
    """
    classes = ["pothole", "longitudinal_crack", "alligator_cracking", "rutting"]
    ground_truths = {c: [] for c in classes}
    predictions = []

    np.random.seed(42)  # For reproducible evaluation outcomes
    num_images = 15

    for img_idx in range(num_images):
        img_id = f"road_img_{img_idx:03d}.jpg"
        
        # Add 1 to 4 random ground truth anomalies per image
        num_anomalies = np.random.randint(1, 5)
        for _ in range(num_anomalies):
            cls = np.random.choice(classes)
            
            # Generate box coordinates in 640x640 frame
            w = np.random.randint(40, 180)
            h = np.random.randint(30, 120)
            xmin = np.random.randint(10, 640 - w)
            ymin = np.random.randint(10, 640 - h)
            gt_box = [float(xmin), float(ymin), float(xmin + w), float(ymin + h)]
            
            ground_truths[cls].append({
                "image_id": img_id,
                "box": gt_box
            })

            # Simulate Predictor Outcomes:
            # - 75% chance of finding the true anomaly (True Positive)
            # - Some shift/coordinate noise to simulate real ML boundaries
            if np.random.random() < 0.75:
                noise = np.random.randint(-15, 15, size=4)
                pred_box = [
                    max(0.0, gt_box[0] + noise[0]),
                    max(0.0, gt_box[1] + noise[1]),
                    min(640.0, gt_box[2] + noise[2]),
                    min(640.0, gt_box[3] + noise[3])
                ]
                confidence = float(np.random.uniform(0.55, 0.98))
                
                predictions.append({
                    "image_id": img_id,
                    "class_name": cls,
                    "box": pred_box,
                    "confidence": confidence
                })

            # - 15% chance of a spurious prediction mismatch (False Positive)
            if np.random.random() < 0.15:
                fp_w = np.random.randint(30, 150)
                fp_h = np.random.randint(20, 110)
                fp_xmin = np.random.randint(10, 640 - fp_w)
                fp_ymin = np.random.randint(10, 640 - fp_h)
                
                predictions.append({
                    "image_id": img_id,
                    "class_name": np.random.choice(classes),
                    "box": [float(fp_xmin), float(fp_ymin), float(fp_xmin + fp_w), float(fp_ymin + fp_h)],
                    "confidence": float(np.random.uniform(0.35, 0.75))
                })

    return ground_truths, predictions, classes


def main():
    parser = argparse.ArgumentParser(
        description="Calculate mAP (mean Average Precision) for Civic Guard / Pothole Vision predictions."
    )
    
    parser.add_argument(
        "--gt", 
        type=str, 
        help="Path to Ground Truth JSON file (structure: {class_name: [{'image_id': 'id', 'box': [xmin, ymin, xmax, ymax]}]})"
    )
    parser.add_argument(
        "--pred", 
        type=str, 
        help="Path to Predictions JSON file (structure: [{'image_id': 'id', 'class_name': 'name', 'box': [xmin, ymin, xmax, ymax], 'confidence': score}])"
    )
    parser.add_argument(
        "--classes", 
        type=str, 
        help="Comma-separated class names list (e.g. 'pothole,crack,rut')"
    )
    parser.add_argument(
        "--yolo-model", 
        type=str, 
        help="Optional: Path to YOLO model weights to trigger native Ultralytics Validation (e.g. backend/weights/best.pt)"
    )
    parser.add_argument(
        "--yolo-data", 
        type=str, 
        help="Optional: Path to YOLO dataset config file (e.g. dataset/data.yaml) for Ultralytics validation"
    )
    parser.add_argument(
        "--generate-synthetic", 
        action="store_true", 
        help="Generate synthetic ground-truths/predictions to evaluate metric math proof and generate output file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="map_evaluation_report.json", 
        help="File path to save the computed mAP JSON results. Default: map_evaluation_report.json"
    )

    args = parser.parse_args()

    # Case A: YOLO model native validation requested
    if args.yolo_model:
        logger.info(f"YOLO Validation request detected. Loading: {args.yolo_model}")
        try:
            from ultralytics import YOLO
            model = YOLO(args.yolo_model)
            
            data_cfg = args.yolo_data if args.yolo_data else "data.yaml"
            logger.info(f"Running validation evaluation on data configuration: {data_cfg}")
            
            results = model.val(data=data_cfg)
            
            # Ultralytics results.results_dict contains metrics
            # e.g.: metrics/mAP50(B), metrics/mAP50-95(B), etc.
            report = {
                "yolo_model": args.yolo_model,
                "dataset_config": data_cfg,
                "mAP50": results.results_dict.get("metrics/mAP50(B)", 0.0),
                "mAP50-95": results.results_dict.get("metrics/mAP50-95(B)", 0.0),
                "fitness": results.fitness,
                "raw_result_keys": list(results.results_dict.keys())
            }
            
            # Write to output file
            with open(args.output, "w") as f:
                json.dump(report, f, indent=4)
                
            logger.info("YOLO Model native validation finished successfully.")
            print("\n" + "="*50)
            print("         YOLO NATIVE VAL REPORT SUMMARY")
            print("="*50)
            print(f"Model path:     {args.yolo_model}")
            print(f"Dataset config: {data_cfg}")
            print(f"mAP@50 (B):     {report['mAP50']:.4f}")
            print(f"mAP@50:95 (B):  {report['mAP50-95']:.4f}")
            print(f"Fitness Score:  {report['fitness']:.4f}")
            print("="*50)
            print(f"Detailed output stored safely in: {args.output}\n")
            return

        except ImportError:
            logger.error(
                "Ultralytics is not available. Please install it using 'pip install ultralytics' or ensure you're utilizing the virtual environment."
            )
            return
        except Exception as e:
            logger.error(f"Error executing YOLO verification process: {e}")
            return

    # Case B: Standard evaluation on custom JSON or Synthetic setup
    gt_data = None
    pred_data = None
    classes_list = []

    if args.generate_synthetic or (not args.gt and not args.pred):
        logger.info("Initializing evaluation with synthetic Civic Guard damage dataset parameters...")
        gt_data, pred_data, classes_list = generate_synthetic_data()
        
        # Save synthetic files so the user has fully-functional samples!
        with open("synthetic_ground_truths.json", "w") as f:
            json.dump(gt_data, f, indent=4)
        with open("synthetic_predictions.json", "w") as f:
            json.dump(pred_data, f, indent=4)
            
        logger.info("Created input sample files 'synthetic_ground_truths.json' and 'synthetic_predictions.json'")
    else:
        # Load custom inputs
        if not args.gt or not args.pred:
            logger.error("Please specify both --gt and --pred paths, or run with --generate-synthetic")
            return

        try:
            with open(args.gt, "r") as f:
                gt_data = json.load(f)
            with open(args.pred, "r") as f:
                pred_data = json.load(f)
            
            if args.classes:
                classes_list = [c.strip() for c in args.classes.split(",") if c.strip()]
            else:
                # Deduce classes from inputs
                classes_list = list(gt_data.keys())

            logger.info(f"Loaded {sum(len(v) for v in gt_data.values())} Ground Truth labels and {len(pred_data)} Predictions.")
            logger.info(f"Classes for evaluation: {classes_list}")

        except Exception as e:
            logger.error(f"Failed to read dataset file inputs: {e}")
            return

    # Compute custom calculations
    results = calculate_map(gt_data, pred_data, classes_list)

    # Save outputs to generated files
    with open(args.output, "w") as f:
        json.dump(results, f, indent=4)

    # Save a detailed readable text summary report alongside the JSON
    txt_report_path = args.output.replace(".json", "") + "_summary.txt"
    with open(txt_report_path, "w") as f:
        f.write("="*60 + "\n")
        f.write("        CIVIC GUARD METRIC EVALUATION SUMMARY\n")
        f.write("="*60 + "\n")
        f.write(f"mAP@50 (Precision threshold 0.50):       {results['mAP@50']:.4f}\n")
        f.write(f"mAP@50:95 (COCO Standard metric average): {results['mAP@50:95']:.4f}\n")
        f.write(f"Precision Average:                       {results['mean_precision']:.4f}\n")
        f.write(f"Recall Average:                          {results['mean_recall']:.4f}\n")
        f.write(f"F1-Score Average:                        {results['mean_f1']:.4f}\n\n")
        f.write("CLASS LEVEL BREAKDOWNS:\n")
        f.write("-"*60 + "\n")
        f.write(f"{'Class Name':<22}{'AP@50':<9}{'AP@50:95':<11}{'Precision':<11}{'Recall':<9}{'F1':<6}\n")
        f.write("-"*60 + "\n")
        for cls, detail in results["classes"].items():
            f.write(f"{cls:<22}{detail['AP@50']:<9.4f}{detail['AP@50:95']:<11.4f}{detail['precision']:<11.4f}{detail['recall']:<9.4f}{detail['f1_score']:<6.4f}\n")
        f.write("="*60 + "\n")

    logger.info(f"Metrics written cleanly to JSON file: '{args.output}'")
    logger.info(f"Metrics written cleanly to friendly TXT file: '{txt_report_path}'")

    # Output printout
    print("\n" + "="*60)
    print("        CIVIC GUARD METRIC EVALUATION STATUS")
    print("="*60)
    print(f"Overall mAP@50:       {results['mAP@50']:.4f}")
    print(f"Overall mAP@50:95:    {results['mAP@50:95']:.4f}")
    print(f"Overall Precision:    {results['mean_precision']:.4f}")
    print(f"Overall Recall:       {results['mean_recall']:.4f}")
    print(f"Overall F1-Score:     {results['mean_f1']:.4f}")
    print("-"*60)
    print(f"{'Class Name':<22}{'AP@50':<9}{'AP@50:95':<11}{'Precision':<11}{'Recall':<9}{'F1':<6}")
    print("-"*60)
    for cls, detail in results["classes"].items():
        print(f"{cls:<22}{detail['AP@50']:<9.4f}{detail['AP@50:95']:<11.4f}{detail['precision']:<11.4f}{detail['recall']:<9.4f}{detail['f1_score']:<6.4f}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
