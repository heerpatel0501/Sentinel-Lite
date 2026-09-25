from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
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
