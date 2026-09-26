from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, computed_field, field_serializer

# ==============================================================================
# Camera Schemas
# ==============================================================================


class CameraBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    department: str
    vms_vendor: str
    status: str
    resolution: str

    # ONVIF Credentials
    onvif_host: Optional[str] = None
    onvif_port: Optional[int] = None
    onvif_username: Optional[str] = None
    onvif_password: Optional[str] = None


class Camera(CameraBase):
    id: Union[int, str]
    added_date: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Pipeline Schemas: CCTV -> Vehicle -> Plate -> OCR -> Watchlist -> Alert
# ==============================================================================


# 1. departments
class DepartmentBase(BaseModel):
    name: str
    contact_email: str


class Department(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


# 2. vehicle_detections (REAL: populated by YOLOv8 /detect)
class VehicleDetectionBase(BaseModel):
    camera_id: Optional[int] = None
    vehicle_type: str
    confidence_score: float
    bounding_box: List[float]
    frame_snapshot_path: Optional[str] = None


class VehicleDetection(VehicleDetectionBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# 3. plates (REAL OCR PIPELINE)
class PlateBase(BaseModel):
    detection_id: Optional[int] = None
    plate_text: str
    normalized_plate: Optional[str] = None
    ocr_confidence: float
    plate_bounding_box: Optional[List[float]] = None


class Plate(PlateBase):
    id: int

    class Config:
        from_attributes = True


# 4. watchlist (MOCKED seed data)
class WatchlistBase(BaseModel):
    plate_text: str
    reason: str
    added_by_department: str
    active: bool = True


class Watchlist(WatchlistBase):
    id: int
    added_date: datetime

    class Config:
        from_attributes = True

# 5. vehicle_movements (with full evidence traceability via detection_id)
class VehicleMovementBase(BaseModel):
    plate_text: str
    camera_id: int
    department_id: int
    detection_id: Optional[int] = None


class VehicleMovement(VehicleMovementBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Stream Health & Telemetry
class StreamHealthBase(BaseModel):
    camera_id: int
    status: str
    codec: str
    resolution: str
    last_pts: float
    reconnect_attempts: int
    fps_actual: float

class StreamHealth(StreamHealthBase):
    id: int
    last_heartbeat: datetime

    class Config:
        from_attributes = True

# Evidence Records
class EvidenceRecordBase(BaseModel):
    detection_id: Optional[int] = None
    plate_text: str
    file_path: str
    uri_reference: str
    pts_timestamp: float
    file_size_bytes: int
    sha256_hash: Optional[str] = None

class EvidenceRecord(EvidenceRecordBase):
    id: int
    captured_at: datetime

    class Config:
        from_attributes = True

# Authorized Synthetic Vehicle Profile
class VehicleProfile(BaseModel):
    plate_number: str
    owner_name: str
    registration_date: str
    vehicle_class: str
    maker_model: str
    fuel_type: str
    engine_no_hash: str
    chassis_no_hash: str
    insurance_valid_until: str
    rto_office: str
    contact_phone_masked: str
    is_synthetic_authorized_data: bool = True

# 6. alerts (MOCKED seed data)
class AlertBase(BaseModel):
    plate_text: str
    alert_type: str
    camera_ids_involved: List[str]
    departments_involved: List[str]
    status: str = "new"
    description: Optional[str] = None


class Alert(AlertBase):
    id: Union[int, str]
    timestamp: Union[str, datetime]

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: Union[str, datetime], _info):
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(dt)

    # Backwards-compatibility computed fields for the existing React frontend
    @computed_field
    @property
    def plate_number(self) -> str:
        return self.plate_text

    @computed_field
    @property
    def camera_names(self) -> List[str]:
        return self.camera_ids_involved

    @computed_field
    @property
    def departments(self) -> List[str]:
        return self.departments_involved

    class Config:
        from_attributes = True


# 7. users
class UserBase(BaseModel):
    email: str
    department_id: int
    role: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# 8. audit_logs (DPDP Act compliance)
class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    target_type: str
    target_id: str


class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# System Telemetry & VMS Schemas
# ==============================================================================


class HealthStats(BaseModel):
    total_cameras: int
    online_percentage: float
    departments_connected: int


class VMSStreamResponse(BaseModel):
    stream_url: str
    status: str
    resolution: str

# ==============================================================================
# Investigation & Stream Ingestion Schemas
# ==============================================================================

class JourneyPoint(BaseModel):
    timestamp: Union[str, datetime]
    camera_id: Union[int, str]
    camera_name: str
    department: str
    latitude: float
    longitude: float
    evidence_reference: Optional[str] = None
    confidence: Optional[float] = None

class InvestigationResult(BaseModel):
    plate_text: str
    watchlist_status: Optional[str] = None
    total_sightings: int
    departments_involved: List[str]
    journey_history: List[JourneyPoint]
    active_alerts: List[str]
