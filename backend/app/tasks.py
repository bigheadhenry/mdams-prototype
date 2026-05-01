import os

from sqlalchemy.orm import Session

from . import config as app_config
from .celery_app import celery_app
from .database import SessionLocal
from .models import Asset, ImageRecord
from .services.face_recognition import (
    build_face_recognition_failed_state,
    normalize_face_recognition_response,
)
from .services.face_recognition_client import FaceRecognitionClientError, recognize_image_file
from .services.iiif_access import (
    apply_iiif_access_derivative,
    build_iiif_access_output_path,
    generate_pyramidal_tiff_access_copy,
    get_asset_original_file_path,
)
from .services.metadata_layers import build_metadata_layers


def _mark_asset_error(asset: Asset, error_message: str) -> None:
    asset.status = "error"
    asset.process_message = f"IIIF access derivative failed: {error_message}"
    layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_visibility_scope=asset.visibility_scope,
        asset_collection_object_id=asset.collection_object_id,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
    )
    layers["technical"]["error_message"] = error_message
    asset.metadata_info = layers
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(asset, "metadata_info")


def _record_layers(record: ImageRecord) -> dict:
    return record.metadata_info if isinstance(record.metadata_info, dict) else {}


def _management_section(record: ImageRecord) -> dict:
    management = _record_layers(record).get("management")
    return dict(management) if isinstance(management, dict) else {}


def _profile_fields(record: ImageRecord) -> dict:
    profile = _record_layers(record).get("profile")
    if not isinstance(profile, dict):
        return {}
    fields = profile.get("fields")
    return dict(fields) if isinstance(fields, dict) else {}


def _record_raw_metadata(record: ImageRecord) -> dict:
    raw_metadata = _record_layers(record).get("raw_metadata")
    return dict(raw_metadata) if isinstance(raw_metadata, dict) else {}


def _coerce_optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip()))
        except (TypeError, ValueError):
            return None


def _set_face_recognition_metadata(record: ImageRecord, asset: Asset, face_recognition: dict) -> None:
    raw_metadata = _record_raw_metadata(record)
    raw_metadata["face_recognition"] = face_recognition

    profile_fields = _profile_fields(record)
    recognized_names = [
        str(item).strip()
        for item in face_recognition.get("recognized_names", [])
        if str(item).strip()
    ]
    if recognized_names:
        profile_fields["main_person"] = "、".join(recognized_names)
    else:
        profile_fields.pop("main_person", None)

    record.metadata_info = build_metadata_layers(
        asset_status=record.status,
        asset_resource_type=record.resource_type,
        asset_visibility_scope=record.visibility_scope,
        asset_collection_object_id=record.collection_object_id,
        metadata={
            "core": {
                "record_no": record.record_no,
                "title": record.title,
                "status": record.status,
                "resource_type": record.resource_type,
                "visibility_scope": record.visibility_scope,
                "collection_object_id": record.collection_object_id,
                "profile_key": record.profile_key,
            },
            "management": _management_section(record),
            "profile": {
                "key": record.profile_key,
                "fields": profile_fields,
            },
            "raw_metadata": raw_metadata,
        },
        source_metadata=raw_metadata,
        profile_hint=record.profile_key,
    )

    asset_layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_visibility_scope=asset.visibility_scope,
        asset_collection_object_id=asset.collection_object_id,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
        source_metadata={
            **(
                asset.metadata_info.get("raw_metadata", {})
                if isinstance(asset.metadata_info, dict) and isinstance(asset.metadata_info.get("raw_metadata"), dict)
                else {}
            ),
            "face_recognition": face_recognition,
        },
        profile_hint=record.profile_key,
    )
    asset.metadata_info = asset_layers

    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(record, "metadata_info")
    flag_modified(asset, "metadata_info")


@celery_app.task(bind=True, name="app.tasks.generate_iiif_access_derivative")
def generate_iiif_access_derivative(self, asset_id: int, original_path: str | None = None):
    db: Session = SessionLocal()
    asset: Asset | None = None
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            print(f"Asset {asset_id} not found during IIIF derivative processing.")
            return

        source_path = original_path or get_asset_original_file_path(asset)
        if not source_path or not os.path.exists(source_path):
            raise FileNotFoundError(f"Original source path is not available for asset {asset_id}.")

        output_path = build_iiif_access_output_path(asset)
        width, height = generate_pyramidal_tiff_access_copy(source_path, output_path)
        apply_iiif_access_derivative(
            asset,
            output_path=output_path,
            width=width,
            height=height,
            conversion_method="celery_pyvips_generate_iiif_access_bigtiff",
        )
        db.commit()
    except Exception as exc:
        if asset is not None:
            _mark_asset_error(asset, str(exc))
            db.commit()
        print(f"Error generating IIIF access derivative for Asset {asset_id}: {exc}")
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.convert_psb_to_bigtiff")
def convert_psb_to_bigtiff(self, asset_id: int, original_path: str):
    return generate_iiif_access_derivative.run(asset_id=asset_id, original_path=original_path)


@celery_app.task(bind=True, name="app.tasks.recognize_business_activity_faces")
def recognize_business_activity_faces(self, record_id: int, asset_id: int):
    if not app_config.FACE_RECOGNITION_ENABLED:
        print(f"Face recognition skipped for record {record_id}: feature disabled.")
        return

    db: Session = SessionLocal()
    try:
        record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not record or not asset:
            print(f"Face recognition skipped: record {record_id} or asset {asset_id} not found.")
            return
        if record.profile_key != "business_activity":
            return
        if record.asset is None or record.asset.id != asset_id:
            print(f"Face recognition skipped: asset {asset_id} is no longer current for record {record_id}.")
            return

        source_path = get_asset_original_file_path(asset) or asset.file_path
        if not source_path or not os.path.exists(source_path):
            failed_state = build_face_recognition_failed_state(
                asset_id=asset_id,
                threshold=app_config.FACE_RECOGNITION_THRESHOLD,
                error_message="Recognition source file is not available",
            )
            _set_face_recognition_metadata(record, asset, failed_state)
            db.commit()
            return

        payload = recognize_image_file(
            source_path,
            threshold=app_config.FACE_RECOGNITION_THRESHOLD,
            request_id=f"record-{record_id}-asset-{asset_id}",
        )
        technical = asset.metadata_info.get("technical", {}) if isinstance(asset.metadata_info, dict) else {}
        image_width = _coerce_optional_int(technical.get("width"))
        image_height = _coerce_optional_int(technical.get("height"))
        normalized = normalize_face_recognition_response(
            payload,
            asset_id=asset_id,
            threshold=app_config.FACE_RECOGNITION_THRESHOLD,
            image_width=image_width,
            image_height=image_height,
        )
        _set_face_recognition_metadata(record, asset, normalized)
        db.commit()
    except FaceRecognitionClientError as exc:
        record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if record and asset:
            failed_state = build_face_recognition_failed_state(
                asset_id=asset_id,
                threshold=app_config.FACE_RECOGNITION_THRESHOLD,
                error_message=str(exc),
            )
            _set_face_recognition_metadata(record, asset, failed_state)
            db.commit()
        print(f"Face recognition client error for record {record_id}: {exc}")
    except Exception as exc:
        record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if record and asset:
            failed_state = build_face_recognition_failed_state(
                asset_id=asset_id,
                threshold=app_config.FACE_RECOGNITION_THRESHOLD,
                error_message=str(exc),
            )
            _set_face_recognition_metadata(record, asset, failed_state)
            db.commit()
        print(f"Unexpected face recognition error for record {record_id}: {exc}")
    finally:
        db.close()
