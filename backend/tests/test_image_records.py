from __future__ import annotations

import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException
from fastapi import UploadFile
from PIL import Image
from sqlalchemy.exc import IntegrityError

from app.models import Asset, User
from app import config as app_config
from app.permissions import get_current_user
from app.routers import image_records as image_records_router
from app.schemas import ImageRecordActionRequest, ImageRecordConfirmRequest, ImageRecordSaveRequest
from app.services.auth import seed_auth_data


pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _metadata_entry_user():
    return get_current_user(x_mdams_user="image-metadata-entry")


def _photographer_user():
    return get_current_user(x_mdams_user="image-photographer")


def _photographer_user_id(db_session) -> int:
    photographer = db_session.query(User).filter(User.username == "image_photographer").one()
    return photographer.id


def _user_id(db_session, username: str) -> int:
    return db_session.query(User).filter(User.username == username).one().id


def _make_png_upload(filename: str = "match.png") -> UploadFile:
    image = Image.new("RGB", (12, 10), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return UploadFile(file=buffer, filename=filename)


def _make_binary_upload(filename: str, content: bytes = b"binary-upload") -> UploadFile:
    return UploadFile(file=BytesIO(content), filename=filename)


def test_image_record_draft_submit_and_return_flow(db_session):
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="North Gate Inspection",
            visibility_scope="open",
            profile_key="business_activity",
            management={
                "project_name": "Spring Survey",
                "image_category": "documentation",
            },
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )

    assert created.record_no.startswith("IR-")
    assert created.status == "draft"
    assert created.validation.ready_for_submit is False
    assert "main_location" in created.validation.missing_fields

    updated = image_records_router.update_image_record(
        record_id=created.id,
        payload=ImageRecordSaveRequest(
            profile_fields={"main_location": "Hall A"},
        ),
        db=db_session,
        user=metadata_user,
    )
    assert updated.validation.ready_for_submit is True

    submitted = image_records_router.submit_image_record(
        record_id=created.id,
        db=db_session,
        user=metadata_user,
    )
    assert submitted.status == "ready_for_upload"
    assert submitted.submitted_at is not None

    photographer_ready_records = image_records_router.list_ready_for_upload_records(
        db=db_session,
        user=photographer_user,
    )
    assert [record.id for record in photographer_ready_records] == [created.id]

    returned = image_records_router.return_image_record(
        record_id=created.id,
        payload=ImageRecordActionRequest(note="Need updated location wording"),
        db=db_session,
        user=metadata_user,
    )
    assert returned.status == "returned"
    assert returned.metadata_info["management"]["return_note"] == "Need updated location wording"


def test_submit_rejects_incomplete_image_record(db_session):
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(title="Incomplete Record"),
        db=db_session,
        user=metadata_user,
    )

    with pytest.raises(HTTPException) as exc:
        image_records_router.submit_image_record(
            record_id=created.id,
            db=db_session,
            user=metadata_user,
        )

    assert exc.value.status_code == 400
    assert "project_name" in exc.value.detail["missing_fields"]
    assert "image_category" in exc.value.detail["missing_fields"]


def test_photographer_general_list_includes_assigned_upload_queue_records(db_session):
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    ready_record = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Ready Record",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=ready_record.id, db=db_session, user=metadata_user)

    upload_queue_record = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Awaiting Validation",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=upload_queue_record.id, db=db_session, user=metadata_user)
    db_record = db_session.query(image_records_router.ImageRecord).filter(image_records_router.ImageRecord.id == upload_queue_record.id).one()
    db_record.status = "uploaded_pending_validation"
    db_session.commit()

    image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Draft Only",
            profile_key="other",
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )

    not_mine = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Not Mine",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror"},
            assigned_photographer_user_id=_user_id(db_session, "system_admin"),
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=not_mine.id, db=db_session, user=metadata_user)

    visible_to_photographer = image_records_router.list_image_records(
        db=db_session,
        user=photographer_user,
    )
    assert [record.title for record in visible_to_photographer] == ["Awaiting Validation", "Ready Record"]


def test_asset_image_record_binding_is_unique(db_session):
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(title="Bound Record"),
        db=db_session,
        user=metadata_user,
    )

    db_session.add(
        Asset(
            filename="bound-1.jpg",
            file_path="/tmp/bound-1.jpg",
            file_size=10,
            mime_type="image/jpeg",
            status="ready",
            image_record_id=created.id,
        )
    )
    db_session.commit()

    db_session.add(
        Asset(
            filename="bound-2.jpg",
            file_path="/tmp/bound-2.jpg",
            file_size=20,
            mime_type="image/jpeg",
            status="ready",
            image_record_id=created.id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_photographer_temp_upload_and_confirm_bind_flow(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Bind Me",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror", "object_number": "OBJ-77"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=created.id, db=db_session, user=metadata_user)

    detailed = asyncio.run(
        image_records_router.upload_temp_image_for_record(
            record_id=created.id,
            file=_make_png_upload("IR-20260406-000001-OBJ-77.png"),
            db=db_session,
            user=photographer_user,
        )
    )
    assert detailed.pending_upload is not None
    assert detailed.pending_upload.sha256
    assert detailed.pending_upload.filename_matches

    confirmed = image_records_router.confirm_bind_image_record(
        record_id=created.id,
        payload=ImageRecordConfirmRequest(temp_upload_token=detailed.pending_upload.token),
        db=db_session,
        user=photographer_user,
    )
    assert confirmed.status == "uploaded_pending_validation"
    assert confirmed.pending_upload is None
    assert confirmed.asset is not None

    asset = db_session.query(Asset).filter(Asset.image_record_id == created.id).one()
    assert asset.filename == "IR-20260406-000001-OBJ-77.png"
    assert asset.status == "ready"


def test_photographer_confirm_replace_rebinds_asset(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Replace Me",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=created.id, db=db_session, user=metadata_user)

    original_asset = Asset(
        filename="original.png",
        file_path=str(test_upload_dir / "original.png"),
        file_size=100,
        mime_type="image/png",
        status="ready",
        image_record_id=created.id,
    )
    db_session.add(original_asset)
    db_session.commit()

    db_record = db_session.query(image_records_router.ImageRecord).filter(image_records_router.ImageRecord.id == created.id).one()
    layers = dict(db_record.metadata_info or {})
    raw_metadata = dict(layers.get("raw_metadata") or {})
    raw_metadata["binding_validation"] = {
        "validation_status": "passed",
        "validation_summary": "Validation passed",
        "validation_report": [],
        "has_blocking_errors": False,
        "has_warnings": False,
        "requires_confirmation": False,
    }
    layers["raw_metadata"] = raw_metadata
    db_record.metadata_info = layers
    db_record.status = "uploaded_pending_validation"
    db_session.commit()

    detailed = asyncio.run(
        image_records_router.upload_temp_image_for_record(
            record_id=created.id,
            file=_make_png_upload("replacement.png"),
            db=db_session,
            user=photographer_user,
        )
    )
    assert detailed.pending_upload is not None
    assert detailed.pending_upload.can_confirm_replace is True

    confirmed = image_records_router.confirm_replace_image_record_asset(
        record_id=created.id,
        payload=ImageRecordConfirmRequest(temp_upload_token=detailed.pending_upload.token, note="new master"),
        db=db_session,
        user=photographer_user,
    )
    assert confirmed.status == "uploaded_pending_validation"
    assert confirmed.asset is not None
    assert confirmed.asset.filename == "replacement.png"
    assert confirmed.binding_validation is not None
    assert confirmed.binding_validation.validation_status == "warning"

    db_session.refresh(original_asset)
    assert original_asset.image_record_id is None
    assert original_asset.status == "superseded"


def test_duplicate_hash_blocks_confirm_bind(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Needs Hash Check",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror", "object_number": "OBJ-88"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=created.id, db=db_session, user=metadata_user)

    detailed = asyncio.run(
        image_records_router.upload_temp_image_for_record(
            record_id=created.id,
            file=_make_png_upload(f"{created.record_no}-OBJ-88.png"),
            db=db_session,
            user=photographer_user,
        )
    )

    duplicate_record = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Existing Asset",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror"},
            assigned_photographer_user_id=_user_id(db_session, "system_admin"),
        ),
        db=db_session,
        user=metadata_user,
    )
    db_session.add(
        Asset(
            filename="existing.png",
            file_path=str(test_upload_dir / "existing.png"),
            file_size=100,
            mime_type="image/png",
            status="ready",
            image_record_id=duplicate_record.id,
            metadata_info={"technical": {"fixity_sha256": detailed.pending_upload.sha256}},
        )
    )
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        image_records_router.confirm_bind_image_record(
            record_id=created.id,
            payload=ImageRecordConfirmRequest(temp_upload_token=detailed.pending_upload.token),
            db=db_session,
            user=photographer_user,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail["validation"]["validation_status"] == "failed"
    assert any(
        rule["code"] == "bind.hash.duplicate"
        for rule in exc.value.detail["validation"]["validation_report"]
    )


def test_filename_mismatch_is_warning_but_bind_can_continue(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Filename Warning",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror", "object_number": "OBJ-99"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=created.id, db=db_session, user=metadata_user)

    detailed = asyncio.run(
        image_records_router.upload_temp_image_for_record(
            record_id=created.id,
            file=_make_png_upload("plain-upload-name.png"),
            db=db_session,
            user=photographer_user,
        )
    )

    assert detailed.pending_upload is not None
    assert detailed.pending_upload.validation is not None
    assert detailed.pending_upload.validation.validation_status == "warning"
    assert detailed.pending_upload.can_confirm_bind is True
    assert any("record number" in warning for warning in detailed.pending_upload.warnings)

    confirmed = image_records_router.confirm_bind_image_record(
        record_id=created.id,
        payload=ImageRecordConfirmRequest(temp_upload_token=detailed.pending_upload.token),
        db=db_session,
        user=photographer_user,
    )

    assert confirmed.status == "uploaded_pending_validation"
    assert confirmed.binding_validation is not None
    assert confirmed.binding_validation.validation_status == "warning"


def test_probe_image_file_falls_back_to_exiftool_metadata(monkeypatch, tmp_path):
    file_path = tmp_path / "layered.psb"
    file_path.write_bytes(b"psb")

    def _raise_unreadable(*args, **kwargs):
        raise OSError("unsupported by pillow")

    monkeypatch.setattr(image_records_router.Image, "open", _raise_unreadable)
    monkeypatch.setattr(
        image_records_router,
        "extract_metadata",
        lambda _path: {
            "File": {
                "ImageWidth": 2048,
                "ImageHeight": 1024,
                "MIMEType": "image/vnd.adobe.photoshop",
            }
        },
    )

    width, height, format_name, frame_count = image_records_router._probe_image_file(str(file_path), None)

    assert (width, height) == (2048, 1024)
    assert format_name == "image/vnd.adobe.photoshop"
    assert frame_count is None


def test_confirm_bind_psb_upload_enqueues_iiif_derivative(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    seed_auth_data(db_session)
    metadata_user = _metadata_entry_user()
    photographer_user = _photographer_user()
    photographer_user_id = _photographer_user_id(db_session)

    created = image_records_router.create_image_record(
        payload=ImageRecordSaveRequest(
            title="Layered Source",
            profile_key="movable_artifact",
            management={"project_name": "Photo Plan", "image_category": "catalogue"},
            profile_fields={"object_name": "Bronze Mirror"},
            assigned_photographer_user_id=photographer_user_id,
        ),
        db=db_session,
        user=metadata_user,
    )
    image_records_router.submit_image_record(record_id=created.id, db=db_session, user=metadata_user)

    monkeypatch.setattr(
        image_records_router,
        "_probe_image_file",
        lambda _path, _mime_type: (1200, 900, "image/vnd.adobe.photoshop", 1),
    )

    enqueued: list[tuple[int, str]] = []
    monkeypatch.setattr(
        image_records_router.generate_iiif_access_derivative,
        "delay",
        lambda asset_id, source_path: enqueued.append((asset_id, source_path)),
    )

    detailed = asyncio.run(
        image_records_router.upload_temp_image_for_record(
            record_id=created.id,
            file=_make_binary_upload(f"{created.record_no}.psb", b"psb-binary"),
            db=db_session,
            user=photographer_user,
        )
    )
    assert detailed.pending_upload is not None

    confirmed = image_records_router.confirm_bind_image_record(
        record_id=created.id,
        payload=ImageRecordConfirmRequest(temp_upload_token=detailed.pending_upload.token),
        db=db_session,
        user=photographer_user,
    )

    assert confirmed.asset is not None
    assert confirmed.asset.status == "processing"
    assert len(enqueued) == 1
    assert enqueued[0][0] == confirmed.asset.asset_id
