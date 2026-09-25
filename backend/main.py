from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os, tempfile, shutil
import cv2
import torch
from ultralytics import YOLO
import models, schemas, database, vms_adapters

# PyTorch 2.6+ compatibility fix for YOLOv8
_original_torch_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_load

import requests
from dotenv import load_dotenv

load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Sentinel-Lite API")

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    # Check if we need to seed the database
    if db.query(models.Camera).count() == 0:
        print("Seeding database with mock cameras...")
        cameras_data = [
            # Ahmedabad
            ("AHM-Junction-01", 23.0225, 72.5714, "Police", "Milestone", "online", "1080p"),
            ("AHM-Traffic-02", 23.0250, 72.5740, "RTO", "Hikvision", "online", "4K"),
            ("AHM-BusStop-03", 23.0200, 72.5700, "GSRTC", "Genetec", "online", "1080p"),
            ("AHM-Park-04", 23.0300, 72.5800, "Municipal", "Dahua", "offline", "720p"),
            # Rajkot
            ("RJK-MainRoad-01", 22.3039, 70.8022, "Police", "Genetec", "online", "1080p"),
            ("RJK-Crossroad-02", 22.3050, 70.8050, "RTO", "Milestone", "online", "4K"),
            ("RJK-Station-03", 22.3000, 70.8000, "GSRTC", "Hikvision", "offline", "1080p"),
            ("RJK-Square-04", 22.3100, 70.8100, "Municipal", "Milestone", "online", "720p"),
            # Surat
            ("SRT-Highway-01", 21.1702, 72.8311, "Police", "Hikvision", "online", "4K"),
            ("SRT-Toll-02", 21.1750, 72.8350, "RTO", "Dahua", "online", "1080p"),
            ("SRT-Depot-03", 21.1650, 72.8250, "GSRTC", "Genetec", "online", "1080p"),
            ("SRT-Market-04", 21.1800, 72.8400, "Municipal", "Milestone", "online", "1080p"),
            # Vadodara
            ("VAD-Entry-01", 22.3072, 73.1812, "Police", "Milestone", "online", "1080p"),
            ("VAD-Bridge-02", 22.3100, 73.1850, "RTO", "Genetec", "offline", "4K"),
            ("VAD-Terminal-03", 22.3000, 73.1750, "GSRTC", "Hikvision", "online", "1080p"),
            ("VAD-Plaza-04", 22.3150, 73.1900, "Municipal", "Dahua", "online", "720p"),
            # Gandhinagar
            ("GND-Secretariat-01", 23.2156, 72.6369, "Police", "Genetec", "online", "4K"),
            ("GND-Circle-02", 23.2200, 72.6400, "RTO", "Milestone", "online", "1080p"),
            ("GND-BusStand-03", 23.2100, 72.6300, "GSRTC", "Dahua", "online", "1080p"),
            ("GND-Sector-04", 23.2250, 72.6450, "Municipal", "Hikvision", "offline", "1080p"),
        ]
        for name, lat, lng, dept, vendor, status, res in cameras_data:
            cam = models.Camera(
                name=name, latitude=lat, longitude=lng, department=dept,
                vms_vendor=vendor, status=status, resolution=res
            )
            db.add(cam)
        db.commit()
    db.close()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/cameras", response_model=list[schemas.Camera])
def read_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    cameras = db.query(models.Camera).offset(skip).limit(limit).all()
    
    # Transform to schemas to allow appending non-DB cameras
    result_cameras = [schemas.Camera.from_orm(c) for c in cameras]
    
    # Fetch live grid cameras
    password = os.getenv("SENTINEL_ACCESS_PASSWORD")
    if password:
        try:
            # We assume it uses Basic Auth or a Bearer token, or just a query param. 
            # The prompt says: "Access requires a password ... Fetch (with the password)"
            # For this MVP, we will try Basic Auth with username 'admin' and the password, 
            # or pass it as a query param `?password=...` or Header `Authorization: Bearer ...`.
            # I will pass it as a Bearer token and as an X-Password header just to be safe, 
            # or maybe just HTTP Basic auth (which is common). Let's use headers.
            headers = {"Authorization": f"Bearer {password}", "X-Password": password}
            # Or query param
            resp = requests.get(f"https://cctv.corp8.cloud/cameras.json?password={password}", headers=headers, timeout=5)
            if resp.status_code == 200:
                live_cams = resp.json()
                for lc in live_cams:
                    result_cameras.append(
                        schemas.Camera(
                            id=str(lc.get("id")),
                            name=lc.get("name", "Live Camera"),
                            latitude=float(lc.get("latitude", 23.0)),
                            longitude=float(lc.get("longitude", 72.0)),
                            department=lc.get("department", "Test Grid"),
                            vms_vendor="LiveGrid",
                            status="online",
                            resolution="1080p",
                            added_date=datetime.now()
                        )
                    )
        except Exception as e:
            print("Failed to fetch live grid cameras:", e)

    return result_cameras

@app.get("/cameras/{camera_id}", response_model=schemas.Camera)
def read_camera(camera_id: str, db: Session = Depends(database.get_db)):
    # If it's a numeric ID, try DB
    if camera_id.isdigit():
        camera = db.query(models.Camera).filter(models.Camera.id == int(camera_id)).first()
        if camera:
            return camera
    
    # Otherwise it might be a LiveGrid external camera
    # For a real app, we'd fetch from cameras.json to get its details, but for MVP we just return a mock
    return schemas.Camera(
        id=camera_id,
        name=f"External Camera {camera_id}",
        latitude=23.0, longitude=72.0,
        department="Test Grid",
        vms_vendor="LiveGrid",
        status="online",
        resolution="1080p",
        added_date=datetime.now()
    )

@app.get("/cameras/{camera_id}/stream", response_model=schemas.VMSStreamResponse)
def get_camera_stream(camera_id: str, db: Session = Depends(database.get_db)):
    if camera_id.isdigit():
        camera = db.query(models.Camera).filter(models.Camera.id == int(camera_id)).first()
        if camera:
            provider = vms_adapters.get_vms_provider(camera.vms_vendor)
            return provider.get_stream(camera.id)
            
    # For external cameras, we know they are LiveGrid
    provider = vms_adapters.get_vms_provider("LiveGrid")
    return provider.get_stream(camera_id)

@app.get("/alerts", response_model=list[schemas.Alert])
def get_alerts():
    # Hardcoded mock cross-department alerts for the dashboard
    return [
        {
            "id": "ALT-1001",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "GJ01-AB-1234",
            "camera_names": ["AHM-Junction-01", "AHM-Traffic-02"],
            "departments": ["Police", "RTO"],
            "description": "Vehicle tracked across Police and RTO cameras."
        },
        {
            "id": "ALT-1002",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "GJ05-XX-9999",
            "camera_names": ["SRT-Highway-01", "SRT-Depot-03"],
            "departments": ["Police", "GSRTC"],
            "description": "Suspicious vehicle near GSRTC depot."
        },
        {
            "id": "ALT-1003",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "GJ03-MC-4567",
            "camera_names": ["RJK-Crossroad-02", "RJK-Square-04"],
            "departments": ["RTO", "Municipal"],
            "description": "Speeding violation in municipal zone."
        },
        {
            "id": "ALT-1004",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "plate_number": "GJ18-ZZ-0001",
            "camera_names": ["GND-Secretariat-01", "GND-Circle-02"],
            "departments": ["Police", "RTO"],
            "description": "VIP convoy route clearance check."
        }
    ]

@app.get("/health", response_model=schemas.HealthStats)
def get_health(db: Session = Depends(database.get_db)):
    try:
        total = db.query(models.Camera).count()
        online = db.query(models.Camera).filter(models.Camera.status == "online").count()
        deps = db.query(models.Camera.department).distinct().count()
        
        online_pct = (online / total * 100) if total > 0 else 0.0
        
        return {
            "total_cameras": total,
            "online_percentage": round(online_pct, 1),
            "departments_connected": deps
        }
    except Exception as e:
        # Fallback if DB is not ready yet
        return {
            "total_cameras": 0,
            "online_percentage": 0.0,
            "departments_connected": 0
        }

# Initialize YOLO model (will download yolov8n.pt if not present)
model = YOLO('yolov8n.pt')

from fastapi import Form

@app.post("/detect")
async def detect_objects(
    file: UploadFile = File(None),
    stream_url: str = Form(None)
):
    tmp_path = None
    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        cap = cv2.VideoCapture(tmp_path)
    elif stream_url:
        cap = cv2.VideoCapture(stream_url)
    else:
        return {"status": "error", "message": "Provide file or stream_url"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30 # fallback

    detections = []
    frame_count = 0
    frame_interval = int(fps) # Process 1 frame per second
    processed_count = 0
    max_frames = 10 if stream_url else float('inf')

    while cap.isOpened() and processed_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            # If it's a live stream, timestamp might just be processed_count
            timestamp = frame_count / fps if file else processed_count
            
            # Run YOLO (verbose=False to keep logs clean)
            results = model(frame, verbose=False)
            frame_detections = []
            
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = model.names[cls_id]
                    
                    if label in ['car', 'truck', 'bus', 'motorcycle', 'person', 'bicycle']:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        orig_h, orig_w = frame.shape[:2]
                        frame_detections.append({
                            "object_type": label,
                            "confidence": round(conf, 2),
                            "bounding_box": [
                                x1 / orig_w, y1 / orig_h, x2 / orig_w, y2 / orig_h
                            ]
                        })
            
            if frame_detections:
                detections.append({
                    "timestamp": round(timestamp, 2),
                    "detections": frame_detections
                })
            processed_count += 1
        
        frame_count += 1

    cap.release()
    if tmp_path:
        os.remove(tmp_path)

    return {"status": "success", "results": detections}
