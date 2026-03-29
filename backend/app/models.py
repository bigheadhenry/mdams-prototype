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
    visibility_scope = Column(String, default="open", index=True)
    collection_object_id = Column(Integer, index=True, nullable=True)
    metadata_info = Column(JSON, nullable=True)  # Store Exif/IPTC as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resource_type = Column(String, default="image_2d_cultural_object")
    process_message = Column(String, nullable=True)
    
    # Status: processing, ready, error
    status = Column(String, default="processing")
    application_items = relationship("ApplicationItem", back_populates="asset")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    collection_scope = Column(JSON, nullable=True)
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UserRole.id",
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UserSession.id",
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=False)
    description = Column(String, nullable=True)
    metadata_info = Column(JSON, nullable=True)

    users = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
        order_by="UserRole.id",
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    application_no = Column(String, unique=True, index=True, nullable=False)
    requester_name = Column(String, nullable=False)
    requester_org = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    purpose = Column(String, nullable=False)
    usage_scope = Column(String, nullable=True)
    status = Column(String, default="submitted", index=True)
    review_note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    items = relationship(
        "ApplicationItem",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationItem.id",
    )


class ApplicationItem(Base):
    __tablename__ = "application_items"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), index=True, nullable=False)
    requested_variant = Column(String, nullable=True)
    delivery_format = Column(String, nullable=True)
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="items")
    asset = relationship("Asset", back_populates="application_items")


class ThreeDAsset(Base):
    __tablename__ = "three_d_assets"

    id = Column(Integer, primary_key=True, index=True)
    collection_object_id = Column(Integer, ForeignKey("three_d_collection_objects.id", ondelete="SET NULL"), index=True, nullable=True)
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
    storage_tier = Column(String, default="archive")
    preservation_status = Column(String, default="pending")
    preservation_note = Column(String, nullable=True)

    # Status: processing, ready, error
    status = Column(String, default="processing")

    collection_object = relationship("ThreeDCollectionObject", back_populates="assets")
    files = relationship(
        "ThreeDAssetFile",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="ThreeDAssetFile.sort_order",
    )
    production_records = relationship(
        "ThreeDProductionRecord",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="ThreeDProductionRecord.occurred_at",
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


class ThreeDCollectionObject(Base):
    __tablename__ = "three_d_collection_objects"

    id = Column(Integer, primary_key=True, index=True)
    object_number = Column(String, index=True, nullable=True)
    object_name = Column(String, index=True, nullable=True)
    object_type = Column(String, index=True, nullable=True)
    collection_unit = Column(String, index=True, nullable=True)
    summary = Column(String, nullable=True)
    keywords = Column(String, nullable=True)
    metadata_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assets = relationship("ThreeDAsset", back_populates="collection_object")


class ThreeDProductionRecord(Base):
    __tablename__ = "three_d_production_records"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("three_d_assets.id", ondelete="CASCADE"), index=True, nullable=False)
    stage = Column(String, index=True)
    event_type = Column(String, index=True)
    status = Column(String, index=True)
    actor = Column(String, nullable=True)
    description = Column(String, nullable=True)
    evidence = Column(String, nullable=True)
    metadata_info = Column(JSON, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("ThreeDAsset", back_populates="production_records")
