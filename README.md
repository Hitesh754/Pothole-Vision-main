# RoadSense AI

> **AI-Powered Road & Civil Structure Damage Detection with Automated Municipal Grievance Ticketing**  
> *EPICS • Environmental Monitoring Program*

![Status](https://img.shields.io/badge/Status-Prototype-emerald) ![YOLOv8](https://img.shields.io/badge/Vision-YOLOv8_--_Segmentation-10b981) ![Stack](https://img.shields.io/badge/Stack-React_FastAPI_Tailwind-orange)

---

## 👥 Project Team & Mentorship

- **Supervisor**: Dr. M. Suresh *(Faculty Mentor, EPICS Program)*
- **Team Members**:
  - Kevin George
  - Hitesh Chaudhary
  - Parth Jangir
  - Shrisai Kolkondi
  - Ishika Mittal
  - Darsana Shaji

---

## 🌍 The Problem & Environmental Monitoring

According to the Ministry of Road Transport & Highways (MoRTH), Government of India:
- **9,438 lives** were lost to pothole-related road crashes between 2020–2024 (a 53% rise in 5 years).
- **80+ citizens** die on average every day in India due to deteriorating road conditions.

### Environmental Hazards Addressed:
1. **Water-Logging & Mosquito Breeding Grounds**: Stagnant water collected in deep craters accelerates vector-borne disease transmission.
2. **Soil Erosion & Runoff**: Broken asphalt surfaces lead to structural sub-base erosion and sediment overflow into municipal storm drains.
3. **Air & Dust Pollution**: Pulverized road aggregate increases breathable particulate matter (PM2.5 / PM10), degrading urban air quality.
4. **Resource-Efficient Maintenance**: Data-driven defect classification prevents premature full-width road failures and saves material waste.

---

## 🏗️ Architecture & Modules

1. **AI Vision & Inspection Engine (`backend/main.py`)**:
   - Built with **FastAPI**, **YOLOv8**, and **OpenCV**.
   - Identifies road potholes, fissures, and alligator cracking from photos, videos, or live camera feeds.
   - Computes defect counts, severity metrics (0–100), and renders real-time HUD annotations with translucent polygon masks.

2. **Municipal Grievance Registry (`components/GrievanceTickets.tsx`)**:
   - Automatically generates formal tracking IDs (e.g., `RS-2026-9438`).
   - Geotags defects with live GPS coordinates and administrative zones.
   - Provides live status lifecycle tracking: **Reported ➔ In Review ➔ Scheduled ➔ Repaired**.

3. **Admin Dashboard & Heatmap (`components/HeatmapGrid.tsx`)**:
   - Real-time zone health matrix, critical hazard priority queues, and severity analytics.

4. **EPICS Information Hub (`components/TeamModal.tsx`)**:
   - Comprehensive documentation of team roles, supervisor details, and environmental metrics.

---

## 🚀 Quickstart Guide

### 1. Launch Python Backend
Ensure Python virtual environment is activated:
```powershell
.\.venv\Scripts\Activate.ps1
python backend/main.py
```
*The local inference server runs on `http://localhost:8000`.*

### 2. Launch Web App
In a second terminal:
```bash
npm run dev
```
*Open `http://localhost:3000` (or `http://localhost:5173`) in your browser.*

---

## 🧪 Testing the Model
1. Navigate to **"AI Scan & Detect"** in the sidebar.
2. Click any of the **Instant Evaluation Samples** (`Pothole Crater`, `Fissure Crack`, or `Multi-Pothole Zone`) or upload your own road image.
3. Observe bounding boxes, segmentation masks, severity score, and click **"File Official Grievance Ticket"** to log it into the system.
