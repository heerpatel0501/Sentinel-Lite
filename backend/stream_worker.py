import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import time
import json
import logging
import threading
from datetime import datetime, timedelta
import requests
import cv2
import numpy as np
from sqlalchemy.orm import Session

import models
import database
from ai_pipeline import SentinelAIEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SentinelStreamWorker")

# Ensure TCP transport for RTSP streams across OpenCV FFmpeg backend
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

SENTINEL_INGEST_URL = os.getenv("SENTINEL_INGEST_URL", "http://localhost:8000/api/ingest")
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "")
USE_LOCAL_FALLBACK = os.getenv("USE_LOCAL_FALLBACK", "true").lower() == "true"
FALLBACK_VIDEO_PATH = os.getenv("FALLBACK_VIDEO_PATH", "traffic_sample.mp4")

class SentinelStreamWorker(threading.Thread):
    """
    Dedicated worker thread for an RTSP/CCTV stream:
    - Connects over TCP
    - Handles H.264 / H.265 and variable resolutions
    - Extracts PTS container timestamps
    - Exponential backoff reconnect
    - Updates stream_health table
    - Runs AI pipeline and commits detections, plates, movements, alerts, and evidence records
    """
    def __init__(self, camera_id: int, camera_name: str, stream_url: str, department_id: int = 1, ai_engine: SentinelAIEngine = None):
        super().__init__(daemon=True, name=f"Worker-Cam-{camera_id}")
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.stream_url = stream_url
        self.department_id = department_id
        self.ai_engine = ai_engine or SentinelAIEngine()
        self.running = True
        self.reconnect_attempts = 0
        self.is_official_sandbox = stream_url.startswith("rtsp://")

    def update_health(self, status: str, codec: str = None, resolution: str = None, fps: float = 0.0, pts: float = 0.0, error_message: str = None):
        db: Session = database.SessionLocal()
        try:
            health = db.query(models.StreamHealth).filter(models.StreamHealth.camera_id == self.camera_id).first()
            if not health:
                health = models.StreamHealth(camera_id=self.camera_id)
                db.add(health)
            
            health.status = status
            health.last_heartbeat = datetime.utcnow()
            if codec:
                health.codec = codec
            if resolution:
                health.resolution = resolution
            if fps > 0:
                health.fps_actual = round(fps, 1)
            health.last_pts = round(pts, 2)
            health.reconnect_attempts = self.reconnect_attempts
            db.commit()
        except Exception as e:
            logger.error(f"[Cam {self.camera_id}] Failed to update stream health: {e}")
            db.rollback()
        finally:
            db.close()

    def process_and_persist_detections(self, frame: np.ndarray, pts: float):
        detections = self.ai_engine.process_frame(frame, camera_id=self.camera_id, pts=pts)
        if not detections:
            return

        db: Session = database.SessionLocal()
        try:
            now = datetime.utcnow()
            for d in detections:
                # 1. vehicle_detections
                v_det = models.VehicleDetection(
                    camera_id=self.camera_id,
                    timestamp=now,
                    vehicle_type=d["vehicle_type"],
                    confidence_score=d["confidence_score"],
                    bounding_box=d["vehicle_box_norm"],
                    frame_snapshot_path=d["evidence_uri"]
                )
                db.add(v_det)
                db.flush() # get v_det.id

                # 2. plates
                plate_entry = models.Plate(
                    detection_id=v_det.id,
                    plate_text=d["plate_text"],
                    normalized_plate=d["normalized_plate"],
                    ocr_confidence=d["ocr_confidence"],
                    plate_bounding_box=d["plate_box_norm"]
                )
                db.add(plate_entry)

                # 3. evidence_records
                evidence = models.EvidenceRecord(
                    detection_id=v_det.id,
                    plate_text=plate_to_check,
                    file_path=d["evidence_file_path"],
                    uri_reference=d["evidence_uri"],
                    sha256_hash=d["sha256_hash"],
                    file_size_bytes=d["file_size_bytes"],
                    pts_timestamp=d["pts_timestamp"],
                    captured_at=now
                )
                db.add(evidence)

                # 4. vehicle_movements (with detection_id for full evidence traceability)
                movement = models.VehicleMovement(
                    detection_id=v_det.id,
                    plate_text=plate_to_check,
                    camera_id=self.camera_id,
                    department_id=self.department_id,
                    timestamp=now
                )
                db.add(movement)

                # 5. Check Watchlist Match
                clean_check = plate_to_check.replace("-", "").strip()
                
                watchlist_matches = db.query(models.Watchlist).filter(
                    models.Watchlist.active == True
                ).all()

                matched = None
                for w in watchlist_matches:
                    w_clean = w.plate_text.replace("-", "").strip().upper()
                    if w_clean == clean_check or w.plate_text.upper() == plate_to_check.upper():
                        matched = w
                        break

                dept_obj = db.query(models.Department).filter(models.Department.id == self.department_id).first()
                dept_name = dept_obj.name if dept_obj else "Police"

                if matched:
                    logger.warning(f"🚨 [WATCHLIST HIT] Plate {plate_to_check} at Camera {self.camera_name} (Reason: {matched.reason})")
                    alert = models.Alert(
                        plate_text=plate_to_check,
                        alert_type="watchlist_match",
                        camera_ids_involved=[self.camera_name],
                        departments_involved=list(set([dept_name, matched.added_by_department])),
                        timestamp=now,
                        status="new",
                        description=f"Watchlist Hit ({matched.reason.upper()}) detected at {self.camera_name}"
                    )
                    db.add(alert)
                else:
                    # Check Cross-Department Correlation (seen across 2+ distinct departments within 60 mins)
                    one_hour_ago = now - timedelta(minutes=60)
                    prior_depts = db.query(models.VehicleMovement.department_id).filter(
                        models.VehicleMovement.plate_text == plate_to_check,
                        models.VehicleMovement.timestamp >= one_hour_ago,
                        models.VehicleMovement.department_id != self.department_id
                    ).distinct().all()

                    if prior_depts:
                        logger.info(f"🔄 [CROSS-DEPT ALERT] Plate {plate_to_check} seen across multiple departments")
                        prior_dept_names = [
                            d_rec.name for d_rec in db.query(models.Department).filter(
                                models.Department.id.in_([pd[0] for pd in prior_depts])
                            ).all()
                        ]
                        all_depts = list(set([dept_name] + prior_dept_names))
                        alert = models.Alert(
                            plate_text=plate_to_check,
                            alert_type="cross_department",
                            camera_ids_involved=[self.camera_name],
                            departments_involved=all_depts,
                            timestamp=now,
                            status="new",
                            description=f"Cross-department movement tracked across {', '.join(all_depts)}"
                        )
                        db.add(alert)

            db.commit()
        except Exception as ex:
            logger.error(f"[Cam {self.camera_id}] Error persisting detections: {ex}")
            db.rollback()
        finally:
            db.close()

    def run(self):
        if self.is_official_sandbox:
            logger.info(f"[Cam {self.camera_id}] Connecting to Official Sentinel Sandbox RTSP stream: {self.stream_url} (TCP)")
        else:
            logger.info(f"[Cam {self.camera_id}] Running local fallback stream: {self.stream_url}")

        backoff_delay = 1.0
        frame_counter = 0

        while self.running:
            self.update_health(status="connecting" if self.reconnect_attempts > 0 else "starting")
            cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)

            if not cap.isOpened():
                self.reconnect_attempts += 1
                error_msg = f"Cannot open stream: {self.stream_url}"
                logger.warning(f"[Cam {self.camera_id}] {error_msg}. Reconnecting in {backoff_delay:.1f}s (Attempt #{self.reconnect_attempts})")
                self.update_health(status="reconnecting", error_message=error_msg)
                time.sleep(backoff_delay)
                backoff_delay = min(30.0, backoff_delay * 2.0)
                continue

            # Connected successfully
            self.reconnect_attempts = 0
            backoff_delay = 1.0

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            fourcc_str = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip()
            codec = "H.265" if "hvc" in fourcc_str.lower() or "hevc" in fourcc_str.lower() else "H.264"
            resolution = f"{width}x{height}" if width > 0 and height > 0 else "Unknown"

            fps_prop = cap.get(cv2.CAP_PROP_FPS)
            stream_fps = fps_prop if fps_prop > 0 and fps_prop < 120 else 25.0

            logger.info(f"[Cam {self.camera_id}] Stream connected. Resolution: {resolution}, Codec: {codec}, FPS: {stream_fps}")
            self.update_health(status="online", codec=codec, resolution=resolution, fps=stream_fps, pts=0.0)

            last_process_time = 0.0

            while self.running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    # If local video ends, loop it for continuous live demo simulation
                    if not self.is_official_sandbox and os.path.exists(self.stream_url):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        logger.warning(f"[Cam {self.camera_id}] Stream dropped or frame read failed.")
                        self.update_health(status="offline", error_message="Frame read failed or stream closed")
                        break

                frame_counter += 1
                
                # PTS timestamp tracking using container presentation timestamp
                pts_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                pts = (pts_msec / 1000.0) if pts_msec > 0 else (frame_counter / stream_fps)

                current_time = time.time()
                # Process AI pipeline at ~1.5 Hz interval to prevent queue backlog
                if (current_time - last_process_time) >= 0.7:
                    last_process_time = current_time
                    self.update_health(status="online", codec=codec, resolution=resolution, fps=stream_fps, pts=pts)
                    try:
                        self.process_and_persist_detections(frame, pts)
                    except Exception as pe:
                        logger.error(f"[Cam {self.camera_id}] Error in frame processing: {pe}")

                time.sleep(0.005)

            cap.release()
            self.reconnect_attempts += 1
            if self.running:
                logger.info(f"[Cam {self.camera_id}] Reconnecting after {backoff_delay:.1f}s backoff...")
                time.sleep(backoff_delay)
                backoff_delay = min(30.0, backoff_delay * 2.0)

        self.update_health(status="offline", error_message="Worker stopped")
        logger.info(f"[Cam {self.camera_id}] Worker terminated.")

    def stop(self):
        self.running = False


class SentinelStreamManager:
    """
    Manages discovery from Sentinel /api/ingest and lifecycle of all stream workers.
    """
    def __init__(self, ingest_url: str = SENTINEL_INGEST_URL):
        self.ingest_url = ingest_url
        self.workers = {}
        self.ai_engine = None

    def discover_and_start(self, use_fallback_if_unreachable: bool = USE_LOCAL_FALLBACK):
        if self.ai_engine is None:
            self.ai_engine = SentinelAIEngine()

        headers = {}
        if SENTINEL_API_KEY:
            headers["Authorization"] = f"Bearer {SENTINEL_API_KEY}"

        cameras_to_ingest = []
        is_official = False

        try:
            logger.info(f"[Stream Manager] Attempting dynamic camera discovery from {self.ingest_url}...")
            resp = requests.get(self.ingest_url, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                cameras_to_ingest = data.get("cameras", data if isinstance(data, list) else [])
                is_official = True
                logger.info(f"✅ [Official Sentinel Sandbox] Discovered {len(cameras_to_ingest)} cameras from official catalogue.")
            else:
                logger.warning(f"[Stream Manager] Discovery endpoint returned HTTP {resp.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ [Sentinel Ingestion Notice] Could not reach official ingest endpoint ({self.ingest_url}): {e}")

        if not cameras_to_ingest and use_fallback_if_unreachable:
            logger.info(f"ℹ️ [Development Mode] Official Sentinel sandbox endpoint not reachable or credentials pending.")
            logger.info(f"ℹ️ [Development Mode] Testing is currently LOCAL using fallback CCTV stream: {FALLBACK_VIDEO_PATH}")
            
            db: Session = database.SessionLocal()
            try:
                db_cams = db.query(models.Camera).limit(4).all()
                for c in db_cams:
                    cameras_to_ingest.append({
                        "id": c.id,
                        "name": c.name,
                        "stream_url": FALLBACK_VIDEO_PATH,
                        "department": c.department,
                        "latitude": c.latitude,
                        "longitude": c.longitude
                    })
            finally:
                db.close()

        # Start stream worker threads
        for cam in cameras_to_ingest:
            cid = cam.get("id") or cam.get("camera_id")
            cname = cam.get("name", f"CAM-{cid}")
            surl = cam.get("stream_url") or cam.get("rtsp_url") or FALLBACK_VIDEO_PATH

            dept_name = cam.get("department", "Police")
            dept_id = 1
            if dept_name == "RTO":
                dept_id = 2
            elif dept_name == "GSRTC":
                dept_id = 3
            elif dept_name == "Municipal":
                dept_id = 4
            elif dept_name == "Panchayat":
                dept_id = 5

            if cid not in self.workers:
                worker = SentinelStreamWorker(
                    camera_id=cid,
                    camera_name=cname,
                    stream_url=surl,
                    department_id=dept_id,
                    ai_engine=self.ai_engine
                )
                self.workers[cid] = worker
                worker.start()
                logger.info(f"🚀 Started stream worker for Camera {cname} (ID: {cid})")

        return len(self.workers)

    def stop_all(self):
        logger.info(f"[Stream Manager] Stopping {len(self.workers)} stream workers...")
        for cid, worker in self.workers.items():
            worker.stop()
        self.workers.clear()

global_stream_manager = SentinelStreamManager()
