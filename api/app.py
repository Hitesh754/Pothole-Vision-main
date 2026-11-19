import os
import io
import time
import base64
from typing import Optional, List
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.model import PotholeDetector
from src.authenticity import AuthenticityVerifier
from src.severity import SeverityScoringEngine

app = FastAPI(
    title="RoadSense AI - ML Inference Service",
    description="REST API for real-time road damage detection, severity classification, and authenticity verification.",
    version="1.0.0"
)

# Enable CORS for React web client and Node.js gateway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core engines
DETECTOR = None
VERIFIER = None
SEVERITY_ENGINE = None

@app.on_event("startup")
def startup_event():
    """Initializes models and verifiers into memory on server start."""
    global DETECTOR, VERIFIER, SEVERITY_ENGINE
    weights = os.getenv("MODEL_WEIGHTS", "yolov8s.pt")
    device = os.getenv("DEVICE", "cpu")
    DETECTOR = PotholeDetector(weights_path=weights, device=device)
    VERIFIER = AuthenticityVerifier()
    SEVERITY_ENGINE = SeverityScoringEngine()
    print("RoadSense AI Inference Engines initialized successfully.")

# Schemas
class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    weights_path: str
    device: str
    timestamp: float

class VerificationResponse(BaseModel):
    verified: bool
    status: str
    mean_error: float
    is_duplicate: bool
    has_exif: bool
    phash: Optional[str]

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Returns runtime health and engine status."""
    return HealthResponse(
        status="OK",
        model_loaded=DETECTOR.model is not None if DETECTOR else False,
        weights_path=DETECTOR.weights_path if DETECTOR else "none",
        device=DETECTOR.device if DETECTOR else "none",
        timestamp=time.time()
    )

@app.post("/verify")
async def verify_image(file: UploadFile = File(...)):
    """
    Checks uploaded image for tampering, synthetic recompression artifacts,
    and duplicate perceptual hash matches.
    """
    contents = await file.read()
    temp_path = f"temp_{int(time.time()*1000)}_{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)

        verification = VERIFIER.verify_all(temp_path)
        return verification
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/detect")
async def detect_damage(
    file: UploadFile = File(...),
    return_base64_image: bool = Form(False)
):
    """
    Primary inference endpoint. Preprocesses image, runs YOLOv8 pothole detection,
    and scores damage severity.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image encoding.")

    result = DETECTOR.detect(image, return_annotated=return_base64_image)

    response_payload = {
        "status": "SUCCESS",
        "total_detections": result["total_detections"],
        "highest_priority": result["highest_priority"],
        "image_dimensions": result["image_dimensions"],
        "detections": result["detections"]
    }

    if return_base64_image and result["annotated_image"] is not None:
        _, buffer = cv2.imencode(".jpg", result["annotated_image"])
        encoded = base64.b64encode(buffer).decode("utf-8")
        response_payload["annotated_image_base64"] = f"data:image/jpeg;base64,{encoded}"

    return response_payload

@app.post("/report-payload")
async def generate_ticket_payload(
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    citizen_id: str = Form("anonymous"),
    address: Optional[str] = Form("Coordinates supplied")
):
    """
    Generates a structured complaint ticket ready for automated submission
    to government grievance portals (PWD / CPGRAMS).
    Integrates authenticity verification, damage detection, and metadata packaging.
    """
    contents = await file.read()
    temp_path = f"ticket_temp_{int(time.time()*1000)}.jpg"
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Authenticity validation
        auth_res = VERIFIER.verify_all(temp_path)
        if not auth_res["verified"]:
            return {
                "ticket_created": False,
                "reason": "Authenticity check failed. Image flagged for tampering or duplicate submission.",
                "verification_details": auth_res
            }

        # Detection and severity
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        det_res = DETECTOR.detect(image, return_annotated=False)

        if det_res["total_detections"] == 0:
            return {
                "ticket_created": False,
                "reason": "No structural damage or potholes detected with sufficient confidence.",
                "total_detections": 0
            }

        primary_defect = det_res["detections"][0]

        # Structured schema for Node.js / Selenium bridge
        ticket = {
            "ticket_created": True,
            "timestamp": int(time.time()),
            "citizen_id": citizen_id,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "address": address
            },
            "damage_summary": {
                "defect_type": primary_defect["class_name"],
                "total_defects_in_frame": det_res["total_detections"],
                "priority": primary_defect["severity"]["priority"],
                "severity_score": primary_defect["severity"]["severity_score"],
                "urgency": primary_defect["severity"]["urgency"],
                "recommended_action": primary_defect["severity"]["recommended_action"]
            },
            "authenticity": {
                "verified": True,
                "phash": auth_res["phash"],
                "ela_mean_error": auth_res["ela"]["mean_error"]
            },
            "target_department": "Public Works Department (PWD) / Municipal Road Maintenance Cell"
        }
        return ticket
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)

