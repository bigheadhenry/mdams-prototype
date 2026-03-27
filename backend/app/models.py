from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    resource_type = Column(String, default="image_2d_cultural_object")
    process_message = Column(String, nullable=True)
    
    # Status: processing, ready, error
    status = Column(String, default="processing")


class ThreeDAsset(Base):
    __tablename__ = "three_d_assets"

    id = Column(Integer, primary_key=True, index=True)
    resource_group = Column(String, index=True, nullable=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resource_type = Column(String, default="three_d_model")
    process_message = Column(String, nullable=True)
    version_label = Column(String, default="original")
    version_order = Column(Integer, default=0)
    is_current = Column(Boolean, default=True)
    is_web_preview = Column(Boolean, default=False)
    web_preview_status = Column(String, default="disabled")
    web_preview_reason = Column(String, nullable=True)

    # Status: processing, ready, error
    status = Column(String, default="processing")

    files = relationship(
        "ThreeDAssetFile",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="ThreeDAssetFile.sort_order",
    )


class ThreeDAssetFile(Base):
    __tablename__ = "three_d_asset_files"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("three_d_assets.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String, index=True)
    role_label = Column(String)
    filename = Column(String, index=True)
    actual_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("ThreeDAsset", back_populates="files")
