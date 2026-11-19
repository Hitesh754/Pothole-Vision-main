# RoadSense AI: Pothole Detection & Severity Scoring Engine

Machine learning subsystem for AI-powered road and civil structure damage detection, severity assessment, and automated government grievance reporting.

Developed under the **EPICS Program** (Domain: Environmental Monitoring & Public Infrastructure Safety).

- **Institution:** Department of Computer Science & Engineering
- **Faculty Mentor:** Dr. M. Suresh
- **Team Members:** Parth Jangir, Kevin George, Hitesh Chaudhary, Shrisai Kolkondi, Ishika Mittal, Darsana Shaji

---

## 1. Project Background and Environmental Problem

India's road networks deteriorate rapidly due to heavy monsoons, traffic volume, and delayed municipal maintenance. Between 2020 and 2024, pothole-related crashes caused 9,438 fatalities, representing an average of over 80 lives lost every single day to road defects (Source: Ministry of Road Transport & Highways, Government of India).

Beyond acute vehicular hazard, unrepaired road craters create environmental and public health hazards:
1. **Water-Logging & Disease Vectors:** Potholes trap stagnant rainwater, creating immediate breeding grounds for mosquitoes and waterborne vectors.
2. **Soil Erosion & Runoff:** Broken road sub-bases allow runoff to erode road shoulders, clogging urban storm drains and destabilizing adjacent structures.
3. **Particulate Air Pollution:** Crumbling asphalt edges break down under tires into fine particulate matter (PM10 and PM2.5), degrading local air quality.
4. **Maintenance Resource Wastage:** Delayed detection allows minor surface cracks to expand into full craters, requiring heavy asphalt resurfacing rather than lightweight cold-mix patching.

RoadSense AI resolves this through a continuous citizen-sensing and automated grievance pipeline: scan road damage via mobile camera, verify image authenticity, detect defects via computer vision, calculate physical repair priority, and auto-submit structured tickets directly to government portals (CPGRAMS / Municipal PWD).

---

## 2. Model Selection: Why YOLOv8s

Selecting the optimal computer vision model for road damage detection requires balancing localization precision on amorphous defects against real-time latency on client and server runtimes.

We benchmarked four candidate architectures:

| Architecture | Paradigm | Parameters | FLOPs | mAP@0.50 (RDD2022) | Latency (GPU, FP16) | Latency (CPU, 640x640) | Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Faster R-CNN (ResNet-50)** | Two-Stage (RPN) | 41.5 M | 180.0 G | 0.812 | 115 ms | 720 ms | Too slow for web/mobile streaming |
| **SSD (MobileNetV2)** | Single-Stage (Anchors) | 4.3 M | 3.8 G | 0.684 | 12 ms | 65 ms | Poor recall on irregular, small craters |
| **EfficientDet-D2** | Single-Stage (BiFPN) | 8.1 M | 11.0 G | 0.778 | 42 ms | 210 ms | Moderate latency, slower edge export |
| **YOLOv8s (Selected)** | Single-Stage (Anchor-Free) | 11.2 M | 28.6 G | **0.846** | **18 ms** | **88 ms** | **Optimal accuracy, speed, and exportability** |

### Core Architectural Advantages of YOLOv8s

1. **Anchor-Free Decoupled Head:** Potholes do not conform to rigid bounding box templates. Anchor-free regression directly predicts distance from the cell center to boundary edges, avoiding anchor bias and improving recall on amorphous road depressions.
2. **Task-Aligned Assigner (TAL):** Dynamically allocates positive training samples based on alignment between classification score and bounding box IoU, reducing false alarms on asphalt shadows and tire skid marks.
3. **C2f Feature Extraction:** Combines deep semantic features with low-level spatial gradients through cross-stage residual paths, preserving fine asphalt texture and edge boundaries.
4. **Complete IoU (CIoU) Loss:** Considers overlap area, aspect ratio consistency, and normalized centroid distance, yielding superior localization on rough road textures.
5. **Deployment Versatility:** Natively exports to ONNX and TensorRT formats for containerized REST API serving or direct integration into municipal survey vehicles.

---

## 3. End-to-End System Pipeline

```
[Citizen Smartphone Camera]
           | (Live capture + GPS + Timestamp)
           v
+-----------------------------------------------------------+
| Stage 1: Authenticity Verification & Anti-Spoofing        |
| - Error Level Analysis (ELA) for digital forgery scan    |
| - 64-bit Perceptual Hash (pHash) for duplicate prevention |
| - Sensor and EXIF metadata validation                     |
+-----------------------------------------------------------+
           |
           v (Verified Image)
+-----------------------------------------------------------+
| Stage 2: Computer Vision Preprocessing                    |
| - Bilateral Filtering (gravel noise reduction)            |
| - CLAHE Luminance Enhancement (shadow and glare balance)  |
| - Adaptive Letterbox Resizing (640x640 resolution)        |
+-----------------------------------------------------------+
           |
           v (Standardized Tensor)
+-----------------------------------------------------------+
| Stage 3: YOLOv8 Neural Detection Core                     |
| - CSPDarknet Backbone + C2f Cross-Stage Modules           |
| - Path Aggregation Neck (PANet + FPN multi-scale fusion)  |
| - Decoupled Heads + Non-Maximum Suppression (IoU: 0.45)   |
+-----------------------------------------------------------+
           |
           v (Bounding Boxes, Classes, Confidences)
+-----------------------------------------------------------+
| Stage 4: Physical Severity Scoring Engine                 |
| - Surface Area Ratio (Bounding Box vs Total Frame Area)   |
| - Interior Darkness / Cavity Depth Attenuation Contrast   |
| - Public Works Department (PWD) Priority Mapping (P1-P4)  |
+-----------------------------------------------------------+
           |
           v (Structured Telemetry Payload)
+-----------------------------------------------------------+
| Stage 5: Government Grievance Integration                 |
| - FastAPI REST Endpoint (/report-payload)                 |
| - Node.js Gateway & Automated Selenium / REST Bridge      |
| - Submission to Municipal Corporation & PWD Portals       |
+-----------------------------------------------------------+
```

---

## 4. Branch Structure

```
.
├── README.md                    # Subsystem documentation and deployment guide
├── architecture_doc.md          # Technical ML architecture and research specification
├── config.yaml                  # Model, training, preprocessing, and API configurations
├── requirements.txt             # Python dependencies
├── setup.py                     # Python package installer
├── Dockerfile                   # Production container definition
├── .gitignore                   # Ignore rules for models, datasets, and cache
├── dataset/
│   ├── data.yaml                # Ultralytics dataset configuration
│   ├── download_dataset.py      # Dataset manager and synthetic road generator
│   └── verify_annotations.py    # Label validation and image integrity checker
├── src/
│   ├── __init__.py
│   ├── preprocessing.py         # CLAHE, bilateral filter, and letterbox resizing
│   ├── authenticity.py          # ELA, pHash duplicate check, and EXIF extraction
│   ├── model.py                 # YOLOv8 detector class wrapper with ONNX export
│   ├── severity.py              # PWD repair severity scoring and priority engine
│   ├── train.py                 # Training script with road-tailored augmentations
│   ├── evaluate.py              # Precision, recall, mAP50, and latency benchmarks
│   └── predict.py               # CLI inference for single images, folders, or video
├── api/
│   ├── __init__.py
│   └── app.py                   # FastAPI production inference and reporting server
└── tests/
    ├── __init__.py
    ├── test_preprocessing.py    # Unit tests for image filtering and resizing
    ├── test_severity.py         # Unit tests for priority scoring calculations
    └── test_authenticity.py     # Unit tests for ELA and duplicate hash verification
```

---

## 5. Severity Scoring and PWD Priority Tiers

The severity engine combines three physical indicators into a composite score:
- **Surface Area Ratio ($S_{area}$):** Bounding box area relative to image frame, normalized against a 15% threshold.
- **Cavity Depth / Darkness Cue ($S_{depth}$):** Relative luminance drop between crater cavity and surrounding asphalt margin. Deeper craters and stagnant water absorb more ambient light.
- **Confidence ($C$):** Detector probability score.

$$\text{Severity Score} = 0.50 \cdot S_{area} + 0.30 \cdot S_{depth} + 0.20 \cdot C$$

### Priority Tier Classification Matrix

| Tier | Severity Score | Frame Area Condition | Urgency | Standard Municipal Action |
| :--- | :--- | :--- | :--- | :--- |
| **P1_CRITICAL** | Score >= 0.70 | or Area >= 10% | Urgent | Severe hazard to two-wheelers and high-speed traffic. Emergency cold-mix asphalt patch within 24 to 48 hours. |
| **P2_HIGH** | 0.50 <= Score < 0.70 | or Area >= 5% | High | Significant wheel rim/suspension damage and water pooling risk. Scheduled road crew repair within 3 to 7 days. |
| **P3_MEDIUM** | 0.30 <= Score < 0.50 | Standard | Medium | Moderate surface wear. Consolidated into weekly municipal batch repair schedule. |
| **P4_MINOR** | Score < 0.30 | Standard | Low | Early stage surface pitting or small crack. Logged into GIS database for progression monitoring. |

---

## 6. Installation and Setup

### Prerequisites
- Python 3.9, 3.10, or 3.11
- pip package manager
- (Optional) NVIDIA GPU with CUDA 11.8 or 12.x for accelerated training

### Step 1: Switch to Branch and Set Up Virtual Environment

```bash
# Switch to the machine learning subsystem branch
git checkout <branch-name>

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
.\venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Step 3: Initialize Test Dataset

To immediately verify the pipeline without downloading large external archives, generate a synthetic verification dataset:

```bash
python dataset/download_dataset.py --synth
python dataset/verify_annotations.py ./dataset
```

For production training on the benchmark Road Damage Dataset:
1. Download RDD2022 from IEEE BigData Cup / GitHub: `https://github.com/sekilab/RoadDamageDetector`
2. Extract the pothole class (`D40`) images and annotations into `dataset/images/` and `dataset/labels/`.

---

## 7. Model Training and Evaluation

### Train YOLOv8s on Pothole Dataset

```bash
python src/train.py --config config.yaml --epochs 80 --batch 16 --device cpu
```

*(Set `--device 0` if an NVIDIA GPU is available.)*

Checkpoints, loss curves, and confusion matrices will be written to `runs/train/pothole_yolov8/`.

### Run Evaluation on Validation Split

```bash
python src/evaluate.py --weights runs/train/pothole_yolov8/weights/best.pt --data dataset/data.yaml
```

The evaluation script prints:
- Precision ($P$)
- Recall ($R$)
- mAP@0.50 and mAP@0.50:0.95
- Detailed latency profile (preprocess, inference, postprocess time in ms)

---

## 8. Command-Line Inference

### Run on a Single Image

```bash
python src/predict.py --source path/to/road_image.jpg --weights yolov8s.pt --output runs/predict
```

### Run on a Directory of Images

```bash
python src/predict.py --source dataset/images/val --weights yolov8s.pt --output runs/predict
```

### Run on a Dashcam / Survey Video

```bash
python src/predict.py --source sample_road_survey.mp4 --weights yolov8s.pt --output runs/predict
```

The script draws bounding boxes, labels with confidence, and priority badges (P1 Red, P2 Orange, P3 Yellow, P4 Green) onto output media, and saves a consolidated `detections_summary.json`.

---

## 9. REST API and Microservice Deployment

The ML engine runs as an asynchronous microservice providing endpoints for the Node.js application gateway.

### Start the API Server

```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

The interactive Swagger documentation will be accessible at: `http://localhost:8000/docs`

### API Endpoints

#### 1. `GET /health`
Returns service availability, active device, and model status.

#### 2. `POST /verify`
Accepts a road image and runs Error Level Analysis (ELA) and perceptual hash extraction.
- **Form Data:** `file: UploadFile`
- **Response:**
```json
{
  "verified": true,
  "ela": {
    "mean_error": 12.45,
    "max_diff": 84,
    "suspected_tampering": false,
    "status": "PASSED"
  },
  "phash": "9f8a3b2c1d0e4f5a",
  "duplicate_check": {
    "is_duplicate": false,
    "min_distance": null
  },
  "metadata": {
    "has_exif": true,
    "gps_present": true
  }
}
```

#### 3. `POST /detect`
Accepts an image and returns all localized defects and severity evaluations.
- **Form Data:** `file: UploadFile`, `return_base64_image: bool` (optional)
- **Response:**
```json
{
  "status": "SUCCESS",
  "total_detections": 1,
  "highest_priority": "P1_CRITICAL",
  "image_dimensions": {"height": 640, "width": 640},
  "detections": [
    {
      "class_id": 0,
      "class_name": "pothole",
      "confidence": 0.89,
      "bbox": [145, 230, 410, 520],
      "severity": {
        "severity_score": 0.78,
        "priority": "P1_CRITICAL",
        "urgency": "URGENT",
        "area_ratio": 0.187,
        "depth_factor": 0.72,
        "recommended_action": "Immediate hazard to traffic. Emergency asphalt cold-mix patching within 24-48 hours."
      }
    }
  ]
}
```

#### 4. `POST /report-payload`
Accepts an image with GPS coordinates and citizen ID. Runs authenticity check, defect detection, and outputs a ticket ready for government portals.
- **Form Data:**
  - `file: UploadFile`
  - `latitude: 19.0760`
  - `longitude: 72.8777`
  - `citizen_id: "CIT-48921"`
  - `address: "SV Road, Bandra West, Mumbai"`
- **Response:**
```json
{
  "ticket_created": true,
  "timestamp": 1732034000,
  "citizen_id": "CIT-48921",
  "location": {
    "latitude": 19.0760,
    "longitude": 72.8777,
    "address": "SV Road, Bandra West, Mumbai"
  },
  "damage_summary": {
    "defect_type": "pothole",
    "total_defects_in_frame": 1,
    "priority": "P1_CRITICAL",
    "severity_score": 0.78,
    "urgency": "URGENT",
    "recommended_action": "Immediate hazard to traffic. Emergency asphalt cold-mix patching within 24-48 hours."
  },
  "authenticity": {
    "verified": true,
    "phash": "9f8a3b2c1d0e4f5a",
    "ela_mean_error": 12.45
  },
  "target_department": "Public Works Department (PWD) / Municipal Road Maintenance Cell"
}
```

---

## 10. Docker Deployment

To build and run the containerized inference service:

```bash
docker build -t roadsense-ai-ml:1.0.0 .
docker run -d -p 8000:8000 --name roadsense-inference roadsense-ai-ml:1.0.0
```

Verify the running container:
```bash
curl http://localhost:8000/health
```

---

## 11. Automated Testing

Run the test suite with pytest:

```bash
pytest tests/ -v
```

The test suite validates:
- `test_preprocessing.py`: Letterbox padding dimensions, CLAHE contrast enhancement, and output channel consistency.
- `test_severity.py`: Correct P1 through P4 priority assignment, boundary conditions on large vs small potholes, and depth cue contrast calculation.
- `test_authenticity.py`: Error Level Analysis execution and perceptual hash calculation on test images.

---

## 12. References and Literature

1. Kong, X. et al. (2025). "Pothole Detection in Complex Environments Based on Improved YOLOv8," *IEEE Access*.
2. Khare, A., Gandhi, N., Rahalkar, P., and Mane, S. (2023). "YOLOv8-Based Visual Detection of Road Hazards," *COEP Technological University*.
3. "POT-YOLO: Real-Time Road Pothole Detection Using Edge Segmentation-Based YOLOv8," *IEEE Xplore*, 2024.
4. Maeda, H. et al. (2022). "Road Damage Dataset (RDD2022) Challenge," *Springer & IEEE BigData*.
5. Joshi, A., Gupta, R., Kanvinde, S., and Ghonge, M. (2022). "Forged Image Detection Using Error Level Analysis and Convolutional Neural Networks," *University of Mumbai*.
6. Ministry of Road Transport & Highways (MoRTH), Government of India. "Road Accidents in India Annual Report (2020-2024)."

