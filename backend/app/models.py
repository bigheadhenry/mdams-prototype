from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    metadata_info = Column(JSON, nullable=True)  # Store Exif/IPTC as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status: processing, ready, error
    status = Column(String, default="processing")
