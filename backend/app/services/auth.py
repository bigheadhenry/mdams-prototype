from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..models import Role, User, UserRole, UserSession

DEFAULT_PASSWORD = "mdams123"
PASSWORD_SALT = "mdams-prototype-auth"
SESSION_DURATION_HOURS = 12

DEFAULT_ROLES: dict[str, dict[str, str]] = {
    "image_structured_editor": {"label": "2D Structured Editor", "description": "Maintain structured metadata for 2D assets."},
    "image_ingest_operator": {"label": "2D Ingest Operator", "description": "Upload and prepare 2D files for ingest."},
    "image_ingest_reviewer": {"label": "2D Ingest Reviewer", "description": "Review 2D ingest readiness."},
    "image_resource_manager": {"label": "2D Resource Manager", "description": "Maintain 2D assets and metadata quality."},
    "image_metadata_entry": {"label": "Image Metadata Entry", "description": "Create and maintain image records before file upload."},
    "image_photographer_upload": {"label": "Image Photographer Upload", "description": "Upload files and match them to ready image records."},
    "three_d_operator": {"label": "3D Operator", "description": "Upload and manage 3D objects and versions."},
    "application_reviewer": {"label": "Application Reviewer", "description": "Review application requests and export deliveries."},
    "collection_owner": {"label": "Collection Owner", "description": "Manage resources within owned collection scope."},
    "resource_user": {"label": "Resource User", "description": "Browse open resources and submit applications."},
    "system_admin": {"label": "System Admin", "description": "Manage system-wide settings and permissions."},
}

DEFAULT_USERS: list[dict[str, object]] = [
    {"username": "image_editor", "display_name": "2D Structured Editor", "roles": ["image_structured_editor"], "collection_scope": []},
    {"username": "image_ingest", "display_name": "2D Ingest Operator", "roles": ["image_ingest_operator"], "collection_scope": []},
    {"username": "image_review", "display_name": "2D Ingest Reviewer", "roles": ["image_ingest_reviewer"], "collection_scope": []},
    {"username": "image_manager", "display_name": "2D Resource Manager", "roles": ["image_resource_manager"], "collection_scope": []},
    {"username": "image_metadata_entry", "display_name": "Image Metadata Entry", "roles": ["image_metadata_entry"], "collection_scope": []},
    {"username": "image_photographer", "display_name": "Image Photographer Upload", "roles": ["image_photographer_upload"], "collection_scope": []},
    {"username": "three_d_operator", "display_name": "3D Operator", "roles": ["three_d_operator"], "collection_scope": [1]},
    {"username": "application_review", "display_name": "Application Reviewer", "roles": ["application_reviewer"], "collection_scope": []},
    {"username": "collection_owner", "display_name": "Collection Owner", "roles": ["collection_owner"], "collection_scope": [1]},
    {"username": "resource_user", "display_name": "Resource User", "roles": ["resource_user"], "collection_scope": []},
    {"username": "system_admin", "display_name": "System Admin", "roles": ["system_admin"], "collection_scope": []},
]


def hash_password(password: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        PASSWORD_SALT.encode("utf-8"),
        100_000,
    )
    return digest.hex()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def seed_auth_data(db: Session) -> None:
    role_map: dict[str, Role] = {}
    for key, definition in DEFAULT_ROLES.items():
        role = db.query(Role).filter(Role.key == key).first()
        if role is None:
            role = Role(key=key, label=definition["label"], description=definition["description"])
            db.add(role)
            db.flush()
        else:
            role.label = definition["label"]
            role.description = definition["description"]
        role_map[key] = role

    for user_definition in DEFAULT_USERS:
        username = str(user_definition["username"])
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(
                username=username,
                display_name=str(user_definition["display_name"]),
                password_hash=hash_password(DEFAULT_PASSWORD),
                is_active=True,
                collection_scope=list(user_definition.get("collection_scope", [])),
                metadata_info={"seeded": True},
            )
            db.add(user)
            db.flush()
        else:
            user.display_name = str(user_definition["display_name"])
            user.collection_scope = list(user_definition.get("collection_scope", []))
            if not user.password_hash:
                user.password_hash = hash_password(DEFAULT_PASSWORD)

        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for role_key in list(user_definition.get("roles", [])):
            db.add(UserRole(user_id=user.id, role_id=role_map[str(role_key)].id))

    db.commit()


def create_user_session(db: Session, user: User) -> UserSession:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS)
    session = UserSession(
        user_id=user.id,
        session_token=create_session_token(),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_by_session_token(db: Session, token: str) -> User | None:
    session = db.query(UserSession).filter(UserSession.session_token == token).first()
    if session is None:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    return session.user


def delete_session_token(db: Session, token: str) -> None:
    session = db.query(UserSession).filter(UserSession.session_token == token).first()
    if session is not None:
        db.delete(session)
        db.commit()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
