from pydantic import BaseModel, computed_field, field_serializer
from typing import Union, List, Optional
from datetime import datetime

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

# 3. plates (MOCKED for submission)
class PlateBase(BaseModel):
    detection_id: Optional[int] = None
    plate_text: str
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

# 5. vehicle_movements (MOCKED seed data - powers cross-dept correlation)
class VehicleMovementBase(BaseModel):
    plate_text: str
    camera_id: int
    department_id: int

class VehicleMovement(VehicleMovementBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

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
