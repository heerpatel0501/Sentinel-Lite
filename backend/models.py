from database import Base
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    department = Column(String(50), nullable=False)
    vms_vendor = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    resolution = Column(String(20), nullable=False)
    added_date = Column(DateTime(timezone=True), server_default=func.now())

    # ONVIF Connection Credentials
    onvif_host = Column(String(255), nullable=True)
    onvif_port = Column(Integer, nullable=True)
    onvif_username = Column(String(255), nullable=True)
    onvif_password = Column(String(255), nullable=True)


# ==============================================================================
# PIPELINE TABLES: CCTV -> Vehicle -> Plate -> OCR -> Watchlist -> Alert
# ==============================================================================


# 1. departments: id, name (Police/RTO/GSRTC/Municipal/Panchayat), contact_email
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    contact_email = Column(String(255), nullable=False)

# Stream Health & Telemetry Tracking
class StreamHealth(Base):
    __tablename__ = "stream_health"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active / reconnecting / offline
    codec = Column(String(20), default="H.264", nullable=False)  # H.264 / H.265
    resolution = Column(String(20), default="1080p", nullable=False)
    last_pts = Column(Float, default=0.0)  # Stream container PTS timestamp
    reconnect_attempts = Column(Integer, default=0)
    fps_actual = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# 2. vehicle_detections: id, camera_id (FK -> cameras), timestamp, vehicle_type, confidence_score, bounding_box, frame_snapshot_path
# [REAL PIPELINE DATA]: Populated by YOLOv8 vehicle detection engine
class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    vehicle_type = Column(String(50), nullable=False)  # car/truck/bus/motorcycle
    confidence_score = Column(Float, nullable=False)
    bounding_box = Column(
        JSON, nullable=False
    )  # [x1, y1, x2, y2] normalized coordinates
    frame_snapshot_path = Column(String(500), nullable=True)

# 3. plates: id, detection_id (FK -> vehicle_detections), plate_text, normalized_plate, ocr_confidence, plate_bounding_box
# [REAL OCR PIPELINE]: Produced by license plate detector + EasyOCR engine
class Plate(Base):
    __tablename__ = "plates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey("vehicle_detections.id"), nullable=True)
    plate_text = Column(String(50), index=True, nullable=False)
    normalized_plate = Column(String(50), index=True, nullable=True)  # Standardized e.g. GJ01-AB-1234
    ocr_confidence = Column(Float, nullable=False)
    plate_bounding_box = Column(JSON, nullable=True)


# 4. watchlist: id, plate_text, reason (stolen/wanted/flagged), added_by_department, added_date, active (boolean)
# [MOCKED SEED DATA]: Demonstrates state-level vehicle watchlist lookup logic.
class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_text = Column(String(50), index=True, nullable=False)
    reason = Column(String(50), nullable=False)  # stolen/wanted/flagged
    added_by_department = Column(String(100), nullable=False)
    added_date = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, default=True, nullable=False)

# 5. vehicle_movements: id, plate_text, camera_id (FK), department_id (FK), detection_id (FK), timestamp
# Powers cross-department correlation with full evidence traceability to vehicle_detections
class VehicleMovement(Base):
    __tablename__ = "vehicle_movements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_text = Column(String(50), index=True, nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    detection_id = Column(Integer, ForeignKey("vehicle_detections.id"), nullable=True)  # Full evidence traceability
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# 6. alerts: id, plate_text, alert_type, camera_ids_involved, departments_involved, timestamp, status
# Stores inter-agency alerts (cross_department, watchlist_match, speeding).
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_text = Column(String(50), index=True, nullable=False)
    alert_type = Column(
        String(50), nullable=False
    )  # watchlist_match/cross_department/speeding
    camera_ids_involved = Column(
        JSON, nullable=False
    )  # JSON list of camera identifiers/names
    departments_involved = Column(JSON, nullable=False)  # JSON list of department names
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status = Column(String(20), default="new", nullable=False)  # new/reviewed/resolved
    description = Column(
        String(255), nullable=True
    )  # Context summary for dashboard display


# Evidence Snapshots Table (Metadata and file reference pointers; zero raw video in DB)
class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey("vehicle_detections.id"), nullable=True)
    plate_text = Column(String(50), index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    uri_reference = Column(String(500), nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    pts_timestamp = Column(Float, default=0.0)
    file_size_bytes = Column(Integer, default=0)
    sha256_hash = Column(String(64), nullable=True)

# 7. users: id, email, department_id (FK), role (admin/viewer/analyst)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Populated with bcrypt hash for OAuth2 / JWT login
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    role = Column(String(50), nullable=False)  # admin/viewer/analyst

# 8. audit_logs: id, user_id (FK), action, target_type, target_id, details, timestamp
# Supports Access Accountability & Privacy Governance (tracking investigator queries & sensitive dossier access)
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # SEARCH_PLATE / VIEW_PROFILE / EXPORT_JOURNEY
    target_type = Column(String(50), nullable=False)  # plate / vehicle / alert
    target_id = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)  # Query parameters, client role, result count
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

