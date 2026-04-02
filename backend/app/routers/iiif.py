import os
import json
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..permissions import CurrentUser, can_access_visibility_scope, ensure_current_user, require_permission
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


def _asset_iiif_access_file_path(asset: Asset) -> str | None:
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    technical = metadata.get("technical") if isinstance(metadata, dict) else {}
    if isinstance(technical, dict):
        iiif_access_file_path = technical.get("iiif_access_file_path")
        if isinstance(iiif_access_file_path, str) and iiif_access_file_path and os.path.exists(iiif_access_file_path):
            return iiif_access_file_path
        preview_file_path = technical.get("preview_file_path")
        if isinstance(preview_file_path, str) and preview_file_path and os.path.exists(preview_file_path):
            return preview_file_path
    return asset.file_path


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
    if config.CANTALOUPE_PUBLIC_URL:
        return config.CANTALOUPE_PUBLIC_URL.rstrip("/")

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
    api_base_url = _api_base_url(request)

    manifest_id = f"{api_base_url}/iiif/{asset_id}/manifest"
    canvas_id = f"{api_base_url}/iiif/{asset_id}/canvas/1"
    annotation_page_id = f"{api_base_url}/iiif/{asset_id}/page/1"
    annotation_id = f"{api_base_url}/iiif/{asset_id}/annotation/1"

    iiif_file_path = _asset_iiif_access_file_path(asset)
    actual_filename = os.path.basename(iiif_file_path) if iiif_file_path else asset.filename
    image_service_id = f"{api_base_url}/iiif/{asset_id}/service/{quote(actual_filename, safe='')}"

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
            "zh-cn": [f"MDAMS 资源 {asset.id}"],
        },
        "homepage": [
            {
                "id": f"{api_base_url}/assets/{asset_id}",
                "type": "Text",
                "label": {
                    "en": ["MDAMS Asset Detail"],
                    "zh-cn": ["MDAMS 资源详情"],
                },
                "format": "text/html",
            }
        ],
        "metadata": [
            {"label": {"en": ["Asset ID"]}, "value": {"en": [str(asset.id)]}},
            {
                "label": {"en": ["Resource ID"]},
                "value": {"en": [str(metadata_layers["core"].get("resource_id") or f"image_2d:{asset.id}")]},
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

    iiif_file_path = _asset_iiif_access_file_path(asset)
    actual_filename = os.path.basename(iiif_file_path) if iiif_file_path else asset.filename
    requested_filename, _, suffix = image_path.partition("/")
    if requested_filename not in {actual_filename, asset.filename}:
        raise HTTPException(status_code=404, detail="Image service not found")

    target_url = f"{_cantaloupe_base_url(request)}/{quote(actual_filename, safe='')}"
    if suffix:
        target_url = f"{target_url}/{suffix}"

    upstream = httpx.get(target_url, timeout=IIIF_UPSTREAM_TIMEOUT)
    content_type = upstream.headers.get("content-type", "application/octet-stream")
    content = upstream.content

    if suffix.endswith("info.json") and "json" in content_type.lower():
        try:
          info_json = upstream.json()
          proxy_base_url = f"{_api_base_url(request)}/iiif/{asset_id}/service/{quote(actual_filename, safe='')}"
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
    )
