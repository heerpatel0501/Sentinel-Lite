from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    department = Column(String(50), nullable=False)
    vms_vendor = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    resolution = Column(String(20), nullable=False)
    added_date = Column(DateTime(timezone=True), server_default=func.now())

# ==============================================================================
# PIPELINE TABLES: CCTV -> Vehicle -> Plate -> OCR -> Watchlist -> Alert
# ==============================================================================

# 1. departments: id, name (Police/RTO/GSRTC/Municipal/Panchayat), contact_email
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    contact_email = Column(String(255), nullable=False)

# 2. vehicle_detections: id, camera_id (FK -> cameras), timestamp, vehicle_type, confidence_score, bounding_box, frame_snapshot_path
# [REAL PIPELINE DATA]: Dynamically populated by the live YOLOv8 /detect inference endpoint
class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # car/truck/bus/motorcycle
    confidence_score = Column(Float, nullable=False)
    bounding_box = Column(JSON, nullable=False)  # [x1, y1, x2, y2] normalized coordinates
    frame_snapshot_path = Column(String(500), nullable=True)

# 3. plates: id, detection_id (FK -> vehicle_detections), plate_text, ocr_confidence, plate_bounding_box
# [MOCKED DATA]: Plate/OCR pipeline uses Indian ANPR OCR Corpus dataset in production;
# mocked here with realistic sample data due to hackathon time constraints.
class Plate(Base):
    __tablename__ = "plates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey("vehicle_detections.id"), nullable=True)
    plate_text = Column(String(50), index=True, nullable=False)
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

# 5. vehicle_movements: id, plate_text, camera_id (FK), department_id (FK), timestamp
# [MOCKED SEED DATA]: Powers cross-department correlation — same plate observed across 2+ different department cameras.
class VehicleMovement(Base):
    __tablename__ = "vehicle_movements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_text = Column(String(50), index=True, nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

# 6. alerts: id, plate_text, alert_type, camera_ids_involved, departments_involved, timestamp, status
# [MOCKED SEED DATA]: Stores migrated inter-agency alerts (cross_department, watchlist_match, speeding).
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_text = Column(String(50), index=True, nullable=False)
    alert_type = Column(String(50), nullable=False)  # watchlist_match/cross_department/speeding
    camera_ids_involved = Column(JSON, nullable=False)  # JSON list of camera identifiers/names
    departments_involved = Column(JSON, nullable=False)  # JSON list of department names
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), default="new", nullable=False)  # new/reviewed/resolved
    description = Column(String(255), nullable=True)  # Context summary for dashboard display

# 7. users: id, email, department_id (FK), role (admin/viewer/analyst)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    role = Column(String(50), nullable=False)  # admin/viewer/analyst

# 8. audit_logs: id, user_id (FK), action, target_type, target_id, timestamp
# (for DPDP Act compliance — who viewed/accessed what, when)
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
