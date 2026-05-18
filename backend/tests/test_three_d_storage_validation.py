import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile

from app.services.three_d_storage import (
    ThreeDUploadValidationError,
    validate_three_d_uploads,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def _upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(file=BytesIO(content), filename=filename)


def test_validate_three_d_uploads_accepts_expected_signatures():
    asyncio.run(
        validate_three_d_uploads(
            {
                "model": [_upload("model.glb", b"glTF\x02\x00\x00\x00")],
                "point_cloud": [_upload("cloud.ply", b"ply\nformat ascii 1.0\n")],
                "oblique_photo": [_upload("photo.jpg", b"\xff\xd8\xff\xe0JFIF")],
            }
        )
    )


def test_validate_three_d_uploads_rejects_invalid_role_extension():
    with pytest.raises(ThreeDUploadValidationError, match="not valid for role"):
        asyncio.run(validate_three_d_uploads({"model": [_upload("script.exe", b"MZ")]}))


def test_validate_three_d_uploads_rejects_signature_mismatch():
    with pytest.raises(ThreeDUploadValidationError, match="file signature"):
        asyncio.run(validate_three_d_uploads({"model": [_upload("fake.glb", b"not a glb")]}))


def test_validate_three_d_uploads_rejects_empty_file():
    with pytest.raises(ThreeDUploadValidationError, match="empty"):
        asyncio.run(validate_three_d_uploads({"model": [_upload("empty.glb", b"")]}))
