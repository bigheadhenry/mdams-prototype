import json
import os
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..permissions import CurrentUser, can_access_visibility_scope, ensure_current_user, require_permission
from ..services.iiif_access import (
    get_asset_iiif_access_file_path,
    is_iiif_ready,
    requires_iiif_access_derivative,
)
from ..services.metadata_layers import build_iiif_metadata_entries, build_metadata_layers, get_dimensions

router = APIRouter(tags=["iiif"])
IIIF_UPSTREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)


def _asset_visibility_scope(asset: Asset) -> str:
    visibility_scope = getattr(asset, "visibility_scope", None)
    if visibility_scope:
        return str(visibility_scope)
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    core = metadata.get("core") if isinstance(metadata, dict) else {}
    if isinstance(core, dict):
        core_scope = core.get("visibility_scope")
        if core_scope not in (None, ""):
            return str(core_scope)
    return "open"


def _asset_collection_object_id(asset: Asset) -> int | None:
    collection_object_id = getattr(asset, "collection_object_id", None)
    if isinstance(collection_object_id, bool):
        return int(collection_object_id)
    if isinstance(collection_object_id, int):
        return collection_object_id
    if isinstance(collection_object_id, str) and collection_object_id.isdigit():
        return int(collection_object_id)
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    core = metadata.get("core") if isinstance(metadata, dict) else {}
    if isinstance(core, dict):
        core_collection_object_id = core.get("collection_object_id")
        if isinstance(core_collection_object_id, int):
            return core_collection_object_id
        if isinstance(core_collection_object_id, str) and core_collection_object_id.isdigit():
            return int(core_collection_object_id)
    return None


def _assert_asset_visible(asset: Asset, user: CurrentUser) -> None:
    if not can_access_visibility_scope(
        user,
        visibility_scope=_asset_visibility_scope(asset),
        collection_object_id=_asset_collection_object_id(asset),
    ):
        raise HTTPException(status_code=403, detail="Asset is not visible to current user")


def _api_base_url(request: Request) -> str:
    if config.API_PUBLIC_URL:
        return config.API_PUBLIC_URL.rstrip("/")

    forwarded_host = request.headers.get("x-forwarded-host")
    forwarded_proto = request.headers.get("x-forwarded-proto", "http")

    if forwarded_host:
        host = forwarded_host
        scheme = forwarded_proto
        forwarded_prefix = request.headers.get("x-forwarded-prefix", "")
        if forwarded_prefix:
            prefix = forwarded_prefix.rstrip("/")
            return f"{scheme}://{host}{prefix}"
        return f"{scheme}://{host}/api"

    host = request.headers.get("host") or "localhost:8000"
    scheme = request.url.scheme
    if ":3000" in host:
        return f"{scheme}://{host}/api"
    return f"{scheme}://{host}"


def _cantaloupe_base_url(request: Request) -> str:
    if config.CANTALOUPE_INTERNAL_URL:
        return config.CANTALOUPE_INTERNAL_URL.rstrip("/")

    forwarded_host = request.headers.get("x-forwarded-host")
    forwarded_proto = request.headers.get("x-forwarded-proto", "http")

    if forwarded_host:
        host = forwarded_host
        scheme = forwarded_proto
        return f"{scheme}://{host}/iiif/2"

    host = request.headers.get("host")
    if host and ":3000" in host:
        return f"{request.url.scheme}://{host}/iiif/2"
    return "http://localhost:8182/iiif/2"


def _quote_iiif_identifier(identifier: str) -> str:
    return quote(identifier.replace("\\", "/"), safe="/")


def _iiif_identifier_for_source_path(source_path: str) -> str:
    source_abs = os.path.abspath(source_path)
    upload_abs = os.path.abspath(config.UPLOAD_DIR)
    try:
        relative_path = os.path.relpath(source_abs, upload_abs)
    except ValueError:
        return os.path.basename(source_abs)

    if relative_path == "." or relative_path == ".." or relative_path.startswith(f"..{os.sep}"):
        return os.path.basename(source_abs)
    return relative_path.replace(os.sep, "/")


def _backend_image_service_url(request: Request, asset_id: int, iiif_identifier: str) -> str:
    return f"{_api_base_url(request)}/iiif/{asset_id}/service/{_quote_iiif_identifier(iiif_identifier)}"


def _cantaloupe_image_service_url(request: Request, iiif_identifier: str) -> str:
    return f"{_cantaloupe_base_url(request)}/{_quote_iiif_identifier(iiif_identifier)}"


def _resolve_requested_iiif_identifier(
    image_path: str,
    *,
    expected_identifier: str,
    aliases: set[str],
) -> tuple[str, str]:
    normalized_path = image_path.lstrip("/")
    expected_identifier = expected_identifier.strip("/")

    for candidate in (expected_identifier, *sorted(alias.strip("/") for alias in aliases if alias)):
        if normalized_path == candidate:
            return expected_identifier, ""
        prefix = f"{candidate}/"
        if normalized_path.startswith(prefix):
            return expected_identifier, normalized_path[len(prefix):]

    raise HTTPException(status_code=404, detail="Image service not found")


def _resolve_iiif_source_path(asset: Asset) -> str:
    iiif_source_path = get_asset_iiif_access_file_path(
        asset,
        allow_original_fallback=True,
        require_exists=True,
    )
    if iiif_source_path:
        return iiif_source_path

    metadata_layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_visibility_scope=_asset_visibility_scope(asset),
        asset_collection_object_id=_asset_collection_object_id(asset),
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
    )
    if requires_iiif_access_derivative(metadata_layers):
        raise HTTPException(status_code=409, detail="IIIF access derivative is not ready")
    raise HTTPException(status_code=404, detail="IIIF source file not found")


@router.get("/iiif/{asset_id}/manifest")
def get_iiif_manifest(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    user = ensure_current_user(user)
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    _assert_asset_visible(asset, user)
    iiif_source_path = _resolve_iiif_source_path(asset)
    api_base_url = _api_base_url(request)

    manifest_id = f"{api_base_url}/iiif/{asset_id}/manifest"
    canvas_id = f"{api_base_url}/iiif/{asset_id}/canvas/1"
    annotation_page_id = f"{api_base_url}/iiif/{asset_id}/page/1"
    annotation_id = f"{api_base_url}/iiif/{asset_id}/annotation/1"

    iiif_identifier = _iiif_identifier_for_source_path(iiif_source_path)
    image_service_id = _backend_image_service_url(request, asset_id, iiif_identifier)

    metadata_layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_visibility_scope=_asset_visibility_scope(asset),
        asset_collection_object_id=_asset_collection_object_id(asset),
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
    )
    width, height = get_dimensions(metadata_layers)
    if not width:
        width = 1000
    if not height:
        height = 1000
    manifest_title = str(metadata_layers["core"].get("title") or asset.filename)

    manifest = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": manifest_id,
        "type": "Manifest",
        "label": {
            "en": [manifest_title],
            "zh-cn": [manifest_title],
        },
        "summary": {
            "en": [f"MDAMS asset {asset.id}"],
            "zh-cn": [f"MDAMS asset {asset.id}"],
        },
        "homepage": [
            {
                "id": f"{api_base_url}/assets/{asset_id}",
                "type": "Text",
                "label": {
                    "en": ["MDAMS Asset Detail"],
                    "zh-cn": ["MDAMS Asset Detail"],
                },
                "format": "text/html",
            }
        ],
        "metadata": [
            {"label": {"en": ["Asset ID"]}, "value": {"en": [str(asset.id)]}},
            {
                "label": {"en": ["Source System"]},
                "value": {"en": [str(metadata_layers["core"].get("source_system") or "image_2d")]},
            },
            {
                "label": {"en": ["Source ID"]},
                "value": {"en": [str(metadata_layers["core"].get("source_id") or asset.id)]},
            },
            {"label": {"en": ["Title"]}, "value": {"en": [manifest_title]}},
            {"label": {"en": ["File Size"]}, "value": {"en": [f"{asset.file_size} bytes"]}},
            {"label": {"en": ["MIME Type"]}, "value": {"en": [asset.mime_type]}},
            {"label": {"en": ["Uploaded At"]}, "value": {"en": [str(asset.created_at)]}},
        ],
        "items": [
            {
                "id": canvas_id,
                "type": "Canvas",
                "label": {"en": ["Page 1"]},
                "height": height,
                "width": width,
                "items": [
                    {
                        "id": annotation_page_id,
                        "type": "AnnotationPage",
                        "items": [
                            {
                                "id": annotation_id,
                                "type": "Annotation",
                                "motivation": "painting",
                                "target": canvas_id,
                                "body": {
                                    "id": f"{image_service_id}/full/max/0/default.jpg",
                                    "type": "Image",
                                    "format": "image/jpeg",
                                    "service": [
                                        {
                                            "id": image_service_id,
                                            "type": "ImageService2",
                                            "profile": "level2",
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }

    manifest["metadata"].extend(build_iiif_metadata_entries(metadata_layers))

    return manifest


@router.get("/iiif/{asset_id}/service/{image_path:path}")
def proxy_iiif_image(
    asset_id: int,
    image_path: str,
    request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    user = ensure_current_user(user)
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    _assert_asset_visible(asset, user)

    iiif_source_path = _resolve_iiif_source_path(asset)
    iiif_identifier = _iiif_identifier_for_source_path(iiif_source_path)
    actual_filename = os.path.basename(iiif_source_path)
    resolved_identifier, suffix = _resolve_requested_iiif_identifier(
        image_path,
        expected_identifier=iiif_identifier,
        aliases={actual_filename, asset.filename or ""},
    )

    target_url = _cantaloupe_image_service_url(request, resolved_identifier)
    if suffix:
        target_url = f"{target_url}/{suffix}"

    upstream = httpx.get(target_url, timeout=IIIF_UPSTREAM_TIMEOUT)
    content_type = upstream.headers.get("content-type", "application/octet-stream")
    content = upstream.content

    if suffix.endswith("info.json") and "json" in content_type.lower():
        try:
            info_json = upstream.json()
            proxy_base_url = _backend_image_service_url(request, asset_id, resolved_identifier)
            info_json["@id"] = proxy_base_url
            info_json["atId"] = proxy_base_url
            info_json["id"] = proxy_base_url
            content = json.dumps(info_json, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        except Exception:
            pass

    return Response(
        content=content,
        status_code=upstream.status_code,
        media_type=content_type,
        headers={"Cache-Control": "no-store"} if is_iiif_ready(asset) else None,
    )
