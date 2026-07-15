from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ApplicationItem, Asset, ThreeDAsset
from .fixity import calculate_sha256
from .iiif_access import get_asset_iiif_access_file_path, get_asset_original_file_path


@dataclass(frozen=True)
class DeliveryFile:
    path: Path
    archive_path: str
    sha256: str
    role: str


@dataclass(frozen=True)
class DeliveryPayload:
    files: tuple[DeliveryFile, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class DeliveryProvider(Protocol):
    def resolve(self, item: ApplicationItem, db: Session) -> DeliveryPayload: ...


def _existing_file(path: str | None, *, label: str) -> Path:
    candidate = Path(path or "")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"Physical file missing for {label}")
    return candidate


class ImageDeliveryProvider:
    def resolve(self, item: ApplicationItem, db: Session) -> DeliveryPayload:
        asset = item.asset
        if asset is None and item.source_id and item.source_id.isdigit():
            asset = db.query(Asset).filter(Asset.id == int(item.source_id)).first()
        if asset is None:
            raise HTTPException(status_code=404, detail=f"2D asset not found for application item {item.id}")

        original_path = _existing_file(get_asset_original_file_path(asset), label=f"asset {asset.id}")
        access_path_value = get_asset_iiif_access_file_path(asset, allow_original_fallback=False, require_exists=True)
        requested = (item.requested_variant or "current").strip().lower()
        selected_path = original_path
        role = "original_file"
        if requested in {"iiif_access", "access", "web"}:
            if not access_path_value:
                raise HTTPException(status_code=404, detail=f"IIIF access file missing for asset {asset.id}")
            selected_path = _existing_file(access_path_value, label=f"asset {asset.id} IIIF access")
            role = "iiif_access_copy"
        return DeliveryPayload(
            files=(
                DeliveryFile(
                    path=selected_path,
                    archive_path=f"data/image_2d/{asset.id}/{selected_path.name}",
                    sha256=calculate_sha256(selected_path),
                    role=role,
                ),
            ),
            metadata={
                "asset_id": asset.id,
                "delivered_variant": role,
                "iiif_access_available": bool(access_path_value),
                "iiif_access_note": "A distinct IIIF access copy is available." if access_path_value else "The preserved original is the current access source.",
            },
        )


def _three_d_representations(item: ApplicationItem, db: Session) -> list[ThreeDAsset]:
    source_id = str(item.source_id or "")
    raw_id = source_id.removeprefix("object-")
    if not raw_id.isdigit():
        raise HTTPException(status_code=404, detail=f"Invalid 3D source id for application item {item.id}")
    anchor = db.query(ThreeDAsset).filter(ThreeDAsset.id == int(raw_id)).first()
    if anchor is None:
        raise HTTPException(status_code=404, detail=f"3D resource not found for application item {item.id}")
    if source_id.startswith("object-") and anchor.three_d_object_id is not None:
        return (
            db.query(ThreeDAsset)
            .filter(ThreeDAsset.three_d_object_id == anchor.three_d_object_id)
            .order_by(ThreeDAsset.version_order.asc(), ThreeDAsset.id.asc())
            .all()
        )
    return [anchor]


class ThreeDDeliveryProvider:
    def resolve(self, item: ApplicationItem, db: Session) -> DeliveryPayload:
        representations = _three_d_representations(item, db)
        current = [representation for representation in representations if representation.is_current]
        selected = current or representations
        files: list[DeliveryFile] = []
        representation_manifest: list[dict[str, Any]] = []
        for representation in selected:
            rep_files = []
            for record in representation.files:
                path = _existing_file(record.file_path, label=f"3D resource {representation.id} file {record.id}")
                checksum = record.sha256 or calculate_sha256(path)
                role = record.role or "other"
                archive_path = f"data/three_d/{item.source_id}/representation-{representation.id}/{role}/{record.actual_filename or path.name}"
                files.append(DeliveryFile(path=path, archive_path=archive_path, sha256=checksum, role=role))
                rep_files.append({"file_id": record.id, "role": role, "filename": record.actual_filename or path.name, "sha256": checksum})
            representation_manifest.append(
                {
                    "id": representation.id,
                    "representation_type": representation.representation_type,
                    "version_label": representation.version_label,
                    "publication_status": representation.publication_status,
                    "files": rep_files,
                }
            )
        if not files:
            raise HTTPException(status_code=404, detail=f"No physical files found for 3D application item {item.id}")
        return DeliveryPayload(tuple(files), {"representations": representation_manifest, "delivered_variant": "current"})


PROVIDERS: dict[str, DeliveryProvider] = {
    "image_2d": ImageDeliveryProvider(),
    "three_d": ThreeDDeliveryProvider(),
}


def resolve_delivery(item: ApplicationItem, db: Session) -> DeliveryPayload:
    source_system = item.source_system or ("image_2d" if item.asset_id is not None else "")
    provider = PROVIDERS.get(source_system)
    if provider is None:
        return DeliveryPayload((), {"delivery_note": f"No physical delivery provider is registered for {source_system}."})
    return provider.resolve(item, db)
