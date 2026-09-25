from pydantic import BaseModel
from datetime import datetime

class CameraBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    department: str
    vms_vendor: str
    status: str
    resolution: str

from typing import Union

class Camera(CameraBase):
    id: Union[int, str]
    added_date: datetime

    class Config:
        from_attributes = True

class Alert(BaseModel):
    id: str
    timestamp: str
    plate_number: str
    camera_names: list[str]
    departments: list[str]
    description: str

class HealthStats(BaseModel):
    total_cameras: int
    online_percentage: float
    departments_connected: int

class VMSStreamResponse(BaseModel):
    stream_url: str
    status: str
    resolution: str
