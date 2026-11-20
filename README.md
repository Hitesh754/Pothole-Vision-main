# PotholeVerify

PotholeVerify is a lightweight, rule-based verification tool designed for municipal road issue reporting systems. It evaluates whether an uploaded pothole photo is an authentic photograph rather than an AI-generated image, duplicate submission, or digitally spliced composite.

The verification pipeline supports both camera captures and images downloaded from web sources or messaging apps where metadata has been stripped. It runs entirely on deterministic heuristics and digital image forensics without machine learning models.

## Technology Stack

- Python 3.10+
- Streamlit: Web application interface
- Pillow: Image parsing, conversion, and metadata extraction
- exifread: Detailed EXIF tag parsing
- imagehash: Perceptual hashing (pHash) for duplicate detection
- numpy: Array computations for error and noise analysis
- sqlite3: Storage for reports and perceptual hashes

## Project Structure

```text
.
├── app.py                      # Streamlit application interface
├── checks.py                   # Modular verification checks
├── scoring.py                  # Scoring weights, thresholds, and decision logic
├── db.py                       # SQLite database operations and storage helpers
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── test_pothole_verify.py      # Automated test suite
├── generate_sample_images.py   # Test image generator for demonstration
├── uploads/                    # Storage directory for submitted report images
└── sample_images/              # Demonstration images covering different test scenarios
```

## Verification Pipeline

The system evaluates incoming images across two tiers: core pixel-level analysis and metadata bonus checks.

### 1. Pixel-Level Analysis (Core)

These checks inspect image data directly and function even if all EXIF metadata is absent:

- Error Level Analysis (ELA) [20 points]:
  Re-saves the image as JPEG at 90 percent quality and measures absolute pixel differences. Non-uniform error distribution or localized spikes indicate possible digital manipulation or composite editing.

- Noise Uniformity Analysis [20 points]:
  Divides the image into an 8x8 block grid and measures high-pass variance (Laplacian) across blocks. Real camera sensors exhibit consistent noise distribution. Mismatched block noise levels suggest spliced content from differing sources.

- JPEG Quality Consistency [15 points]:
  Evaluates compression behavior across multiple quality levels (50 to 95). Double-compressed images (edited and re-saved) show irregular roughness in error curves compared to single-save originals.

- Duplicate Detection [15 points]:
  Computes a 64-bit perceptual hash (pHash) and compares Hamming distance against accepted or reviewed submissions in the database. A distance of 5 or lower flags a duplicate report.

- Dimensional Heuristics [10 points]:
  Flags typical square and standard aspect ratios commonly output by generative models (such as 512x512, 1024x1024, 768x1344). Resolutions above 2 megapixels consistent with camera sensors pass this check.

### 2. Metadata Analysis (Bonus)

Metadata checks provide bonus points when present. Stripped metadata yields 0 bonus points without penalizing the core score:

- Camera Hardware EXIF [10 points]:
  Awards bonus points if camera Make and Model tags exist. Scans raw bytes, XMP blocks, and PNG chunks for known AI generator signatures (such as Stable Diffusion, Midjourney, DALL-E, Firefly, ComfyUI, Automatic1111). Detection triggers an immediate reject decision.

- GPS Proximity [10 points]:
  Extracts GPS tags from EXIF and computes the Haversine distance to the reported location. Distance within 500 meters awards bonus points.

- Timestamp Freshness [5 points]:
  Verifies that the capture timestamp (DateTimeOriginal) occurred within 48 hours of submission.

## Scoring and Decision Rules

- Maximum Score: 100 points (75 pixel-level points + 25 metadata bonus points)
- Hard Rule: Any confirmed generative AI signature triggers an immediate Reject decision, regardless of points.

### Decision Boundaries

- Accept: Score >= 60
  The image passes consistency checks and qualifies as authentic.
- Review: Score 35 to 59
  The image shows ambiguous indicators or partial anomalies and is sent to the admin queue for manual confirmation.
- Reject: Score < 35 (or AI signature detected)
  The image fails key forensic checks or contains generative model signatures.

## Installation and Setup

### 1. Prerequisites

Ensure Python 3.10 or higher is installed.

### 2. Virtual Environment Setup

On Windows:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

On Linux or macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 5. Generate Test Images

To generate test images covering authentic, AI-tagged, spliced, and web-sourced cases:

```bash
python generate_sample_images.py
```

### 6. Run the Test Suite

```bash
python test_pothole_verify.py
```

## System Limitations

1. EXIF spoofing: Metadata is not cryptographically signed. Dedicated command-line tools can forge GPS coordinates, timestamps, or camera tags.
2. Web compression: Social networks and messaging platforms strip EXIF metadata and recompress images, which limits metadata extraction.
3. ELA sensitivity: Natural high-contrast edges and textures can produce localized ELA variance without malicious intent.
4. AI footprint evasion: Screenshots or metadata stripping can remove AI software tags; pixel-level checks serve as secondary heuristics rather than absolute proof.
