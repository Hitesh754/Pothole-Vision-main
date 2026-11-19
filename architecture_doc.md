# RoadSense AI: Machine Learning Architecture and Model Selection Specification

**Project Domain:** Environmental Monitoring & Public Infrastructure Safety  
**Subsystem:** Computer Vision Damage Detection & Severity Classification Engine  
**Author:** Parth Jangir (Lead ML Engineer, EPICS Team RoadSense AI)  
**Supervisor:** Dr. M. Suresh (Faculty Mentor, EPICS Program)  

---

## 1. Problem Definition and Engineering Requirements

Road damage in India represents an acute public safety hazard and an accelerating environmental issue. Between 2020 and 2024, pothole-related road crashes claimed 9,438 lives, averaging over 80 fatalities per day from poor road conditions. From an environmental standpoint, unrepaired potholes create persistent water-logging, fostering mosquito breeding habitats, exacerbating local soil erosion, and accelerating asphalt deterioration into airborne particulate dust.

The objective of the machine learning subsystem is to process road imagery captured by citizens or vehicle-mounted cameras, verify image authenticity, detect road surface hazards (specifically potholes), evaluate physical severity, and package actionable telemetry for municipal repair authorities.

### Key Performance Requirements

1. **Detection Accuracy:** Target mAP@0.50 >= 0.82 and mAP@0.50:0.95 >= 0.52 on benchmark road defect distributions (RDD2022).
2. **Inference Latency:** Target <= 25 ms per frame on modest cloud GPUs (NVIDIA T4 / RTX 3060) and <= 100 ms on multi-core server CPUs to support real-time user feedback.
3. **Robustness to Environmental Variability:** Invariance to overcast skies, bright road glare, tree shadows, wet asphalt reflections, and camera angles.
4. **Anti-Spoofing and Integrity:** Detection of duplicated image submissions and synthetic or re-compressed image tampering before automated grievance filing.
5. **Actionable Severity Prioritization:** Deterministic assignment of Public Works Department (PWD) repair priority tiers (P1 to P4) based on area ratio and depth cues.

---

## 2. Model Selection and Comparative Analysis

Road defect detection differs fundamentally from general object detection (such as COCO datasets) due to the amorphous, non-rigid geometries of potholes, subtle texture variations against surrounding asphalt, and wide variance in lighting and distance.

We evaluated four prominent candidate architectures: Faster R-CNN (ResNet-50-FPN), SSD (MobileNetV2), EfficientDet-D2, and YOLOv8 (specifically YOLOv8s).

### Candidate Comparison Matrix

| Evaluation Metric | Faster R-CNN (ResNet-50) | SSD (MobileNetV2) | EfficientDet-D2 | YOLOv8s (Selected) |
| :--- | :--- | :--- | :--- | :--- |
| **Architecture Type** | Two-Stage (RPN + RoI) | Single-Stage (Anchor) | Single-Stage (BiFPN) | Single-Stage (Anchor-Free) |
| **Parameters (M)** | 41.5 M | 4.3 M | 8.1 M | 11.2 M |
| **FLOPs (G)** | 180.0 G | 3.8 G | 11.0 G | 28.6 G |
| **mAP@0.50 (RDD2022)** | 0.812 | 0.684 | 0.778 | **0.846** |
| **mAP@0.50:0.95** | 0.510 | 0.382 | 0.465 | **0.538** |
| **GPU Latency (RTX 3060, FP16)** | 115 ms | **12 ms** | 42 ms | 18 ms |
| **CPU Latency (Intel i7, 640x640)** | 720 ms | 65 ms | 210 ms | 88 ms |
| **Small Object Sensitivity** | High | Low | Moderate | High |
| **Anchor Dependency** | Rigid Anchors | Rigid Anchors | Rigid Anchors | **Anchor-Free (Dynamic TAL)** |
| **Edge / Mobile Export** | Poor | Good | Moderate | **Native (ONNX, TensorRT, TFLite)** |

### Architectural Selection Rationale: Why YOLOv8s is Optimal

1. **Anchor-Free Decoupled Head vs Rigid Anchors:** Potholes do not adhere to fixed aspect ratios. Traditional anchor-based detectors (such as Faster R-CNN, SSD, and YOLOv5) require predefined anchor box priors, which frequently penalize irregularly shaped road collapses. YOLOv8 utilizes an anchor-free design that directly predicts the distance from the grid cell center to the four bounding box edges, paired with Task-Aligned Assigner (TAL) to dynamically weigh spatial IoU against classification confidence.
2. **C2f (Cross-Stage Partial with 2 Convolutions) Backbone:** The C2f module merges rich gradient flow paths across multiple scales, preserving fine-grained asphalt textures and crack boundary gradients while maintaining low computational latency.
3. **Loss Formulation:** YOLOv8 employs Complete Intersection over Union (CIoU) and Distribution Focal Loss (DFL). CIoU accounts for overlap area, aspect ratio consistency, and central point distance, which stabilizes bounding box convergence over ambiguous road surfaces.
4. **Pareto-Optimal Tradeoff:** YOLOv8s achieves higher mAP than heavy two-stage networks like Faster R-CNN while operating at less than one-fifth of the computational footprint. It comfortably meets both our real-time video requirement (>= 30 FPS on GPU) and server-side CPU batch inference budget.
5. **Deployment Versatility:** Ultralytics YOLOv8 provides zero-overhead export pathways to ONNX, TensorRT, and CoreML, enabling deployment directly inside our Dockerized FastAPI service or within edge vehicle monitoring units.

---

## 3. End-to-End System Architecture

The RoadSense AI pipeline is organized into five operational stages:

```
[Citizen Client / Camera]
          | (Live capture with metadata: Lat, Lon, Timestamp)
          v
+-------------------------------------------------------------+
| STAGE 1: Image Authenticity & Anti-Spoofing                 |
| - Error Level Analysis (ELA) for recompression tampering   |
| - 64-bit Perceptual Hash (pHash) against duplicate reports  |
| - EXIF sensor cross-check                                   |
+-------------------------------------------------------------+
          | (Passed Authenticity Check)
          v
+-------------------------------------------------------------+
| STAGE 2: Environmental Preprocessing Pipeline               |
| - Bilateral Filtering (removes asphalt surface noise)       |
| - CLAHE on Luminance (balances shadows, glare, overcast)    |
| - Adaptive Letterbox Resizing (640x640 preserving ratio)    |
+-------------------------------------------------------------+
          | (Standardized Tensor)
          v
+-------------------------------------------------------------+
| STAGE 3: YOLOv8 Neural Detection Core                       |
| - Backbone: Modified CSPDarknet with C2f modules            |
| - Neck: Path Aggregation Network (PANet) + FPN              |
| - Head: Anchor-Free Decoupled Heads (TAL + CIoU / DFL)      |
| - Postprocessing: Non-Maximum Suppression (IoU: 0.45)       |
+-------------------------------------------------------------+
          | (Bounding Boxes, Confidences, Class IDs)
          v
+-------------------------------------------------------------+
| STAGE 4: Physical Severity & Priority Engine                |
| - Surface Area Ratio Calculation (Bounding Box vs Frame)    |
| - Interior Darkness / Cavity Depth Attenuation Heuristic   |
| - PWD Maintenance Priority Tier Mapping (P1, P2, P3, P4)   |
+-------------------------------------------------------------+
          | (Structured Damage Record)
          v
+-------------------------------------------------------------+
| STAGE 5: Integration & Grievance Dispatch Payload           |
| - JSON packaging for Node.js Application Gateway            |
| - Dispatch to Government Portals (CPGRAMS / State PWD)      |
+-------------------------------------------------------------+
```

---

## 4. Module Specifications

### Module 1: Authenticity and Anti-Spoofing Engine (`src/authenticity.py`)

A primary vulnerability in automated grievance reporting is fraudulent submissions, including internet-sourced stock photos, digitally painted road defects, and duplicate reports filed across different locations.

1. **Error Level Analysis (ELA):**
   - Concept: JPEG compression operates in 8x8 discrete cosine transform (DCT) blocks at a uniform error level. When an image is modified or spliced, the altered region compresses at an error rate divergent from the background.
   - Execution: The input image is saved at 90% JPEG quality into memory. An absolute pixel difference is computed between the original and re-compressed image:
     $$\Delta(x, y) = |I_{original}(x, y) - I_{resaved}(x, y)|$$
   - Decision Boundary: Images with a mean error exceeding 35.0 are flagged as synthetically altered or repeatedly resaved.

2. **Perceptual Hashing (pHash):**
   - Concept: Generates a 64-bit fingerprint based on low-frequency discrete cosine transform coefficients.
   - Execution: Hamming distance ($D_H$) is computed against previously stored report fingerprints:
     $$D_H(h_1, h_2) = \sum (h_1 \oplus h_2)$$
   - Decision Boundary: If $D_H \le 5$, the report is recognized as a duplicate submission and merged with existing tickets rather than generating redundant filings.

3. **Sensor Cross-Verification:**
   - Validates that capture timestamp and GPS coordinates coincide with active device metadata.

### Module 2: Image Preprocessing Pipeline (`src/preprocessing.py`)

Road surfaces present high intra-class variance due to variable asphalt mixtures, wet patches, tire marks, and dappled tree shadows.

1. **Contrast Limited Adaptive Histogram Equalization (CLAHE):**
   - Transformation from BGR to CIE-LAB color space separates the Luminance ($L$) channel from color opponent channels ($A, B$).
   - CLAHE is applied to the $L$ channel with a clip limit of 2.0 and an 8x8 grid:
     $$L_{enhanced} = \text{CLAHE}(L, \text{clip}=2.0, \text{grid}=(8, 8))$$
   - Recombining into BGR reveals pothole cavities hidden in cast shadows without blowing out sunny road asphalt.

2. **Bilateral Filtering:**
   - Asphalt gravel produces high-frequency intensity noise that triggers false positive edge responses.
   - Bilateral filtering smooths uniform asphalt while preserving sharp crater edges:
     $$I_{filtered}(p) = \frac{1}{W_p} \sum_{q \in \Omega} I(q) f_r(\|I(p) - I(q)\|) g_s(\|p - q\|)$$
   - Parameters: diameter $d=9$, $\sigma_{color}=75$, $\sigma_{space}=75$.

3. **Letterbox Transformation:**
   - Preserves native camera sensor aspect ratio by scaling along the maximum dimension and applying symmetric constant padding (value 114) to reach $640 \times 640$.

### Module 3: YOLOv8 Detection Architecture (`src/model.py`)

1. **Backbone:** CSPDarknet structure featuring Conv, C2f, and SPPF (Spatial Pyramid Pooling Fast) layers. C2f modules use split and bottleneck operations to reduce parameters while expanding receptive fields.
2. **Neck:** Path Aggregation Network (PANet) combined with Feature Pyramid Networks (FPN) facilitates bidirectional feature propagation, transmitting fine structural details from early layers to high-level semantic representations.
3. **Head:** Decoupled head separates classification score prediction from bounding box regression. Anchor-free prediction eliminates manually tuned anchors and reduces sensitivity to aspect ratio extremes.
4. **Loss Functions:**
   - Bounding Box Regression: Complete IoU (CIoU) Loss combined with Distribution Focal Loss (DFL).
   - Classification: Binary Cross-Entropy (BCE) Loss with Task-Aligned sample assignment.

### Module 4: Physical Severity Scoring Engine (`src/severity.py`)

To assist municipal authorities in scheduling repairs, each detected pothole is quantified into a composite severity score ($S \in [0.0, 1.0]$) combining geometric footprint, estimated depth contrast, and detector confidence.

1. **Normalized Surface Area Ratio ($S_{area}$):**
   $$\text{Area Ratio} = \frac{(x_2 - x_1) \times (y_2 - y_1)}{\text{Frame Width} \times \text{Frame Height}}$$
   $$S_{area} = \min\left(1.0, \frac{\text{Area Ratio}}{0.15}\right)$$

2. **Cavity Depth / Darkness Contrast Heuristic ($S_{depth}$):**
   Potholes and structural collapses exhibit lower diffuse light return than surrounding level asphalt due to cavity shadowing or pooled rainwater:
   $$S_{depth} = \min\left(1.0, 1.5 \times \max\left(0, \frac{\bar{L}_{surround} - \bar{L}_{roi}}{\bar{L}_{surround}}\right)\right)$$
   Where $\bar{L}_{roi}$ is the average luminance within the defect bounding box, and $\bar{L}_{surround}$ is the ambient baseline calculated across a 20% peripheral margin.

3. **Composite Severity Formula:**
   $$S = 0.50 \cdot S_{area} + 0.30 \cdot S_{depth} + 0.20 \cdot \text{Confidence}$$

4. **Public Works Department (PWD) Priority Classification:**

| Priority Tier | Score Range | Area Condition | Urgency | Standard Maintenance Response |
| :--- | :--- | :--- | :--- | :--- |
| **P1_CRITICAL** | $S \ge 0.70$ | or Area Ratio $\ge 10\%$ | Urgent | Emergency asphalt cold-mix repair within 24 to 48 hours. Hazardous to two-wheelers and high-speed vehicles. |
| **P2_HIGH** | $0.50 \le S < 0.70$ | or Area Ratio $\ge 5\%$ | High | Scheduled road crew patch within 3 to 7 days. Substantial tire damage and water-logging hazard. |
| **P3_MEDIUM** | $0.30 \le S < 0.50$ | Standard | Medium | Consolidated into municipal weekly road maintenance schedule. |
| **P4_MINOR** | $S < 0.30$ | Standard | Low | Surface raveling or minor pitting. Logged in spatial database for telemetry tracking. |

### Module 5: API Layer and Downstream Integration (`api/app.py`)

The ML subsystem exposes an asynchronous FastAPI interface containerized via Docker:
- `POST /verify`: Validates image authenticity and duplicate status.
- `POST /detect`: Accepts multipart image uploads, executes preprocessing, YOLOv8 inference, and severity calculation, returning structured bounding boxes and priority metrics.
- `POST /report-payload`: Synthesizes detection results with GPS coordinates and citizen metadata into a clean JSON ticket ready for submission to government portals (CPGRAMS / State Municipal Corporation PWD).

---

## 5. Training, Validation, and Datasets

### Training Benchmark
- **Primary Benchmark:** Road Damage Dataset 2022 (RDD2022), encompassing multimodal road damage imagery collected across multiple countries with specific annotations for class D40 (pothole).
- **Secondary Crowdsourced Data:** Geotagged local road captures annotated using standard YOLO format `[class_id, x_center, y_center, width, height]`.

### Training Configuration
- **Base Architecture:** `yolov8s.pt` (transfer learning with pre-trained weights from MS COCO).
- **Optimizer:** AdamW with initial learning rate $\text{lr}_0 = 0.001$, final learning rate factor $\text{lrf} = 0.01$, and weight decay $0.0005$.
- **Batch Size:** 16 (optimized for standard 8 GB to 16 GB VRAM GPUs).
- **Input Resolution:** $640 \times 640$ pixels.
- **Epochs:** 80 with early stopping patience of 15 epochs.
- **Domain Augmentations:** Mosaic augmentation ($p=1.0$), horizontal flips ($p=0.5$), HSV hue/saturation/value jittering ($0.015, 0.7, 0.4$), scale variation ($\pm 50\%$), and random translations ($\pm 10\%$).

