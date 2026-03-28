import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..services.metadata_layers import build_iiif_metadata_entries, build_metadata_layers, get_dimensions

router = APIRouter(tags=["iiif"])


@router.get("/iiif/{asset_id}/manifest")
def get_iiif_manifest(asset_id: int, request: Request, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if config.API_PUBLIC_URL:
        api_base_url = config.API_PUBLIC_URL.rstrip("/")
    else:
        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        forwarded_prefix = request.headers.get("x-forwarded-prefix", "")

        if forwarded_host:
            host = forwarded_host
            scheme = forwarded_proto
            if forwarded_prefix:
                prefix = forwarded_prefix.rstrip("/")
                api_base_url = f"{scheme}://{host}{prefix}"
            else:
                api_base_url = f"{scheme}://{host}/api"
        else:
            host = request.headers.get("host")
            if not host:
                host = "localhost:8000"
            scheme = request.url.scheme
            if ":3000" in host:
                api_base_url = f"{scheme}://{host}/api"
            else:
                api_base_url = f"{scheme}://{host}"

    if config.CANTALOUPE_PUBLIC_URL:
        cantaloupe_base_url = config.CANTALOUPE_PUBLIC_URL.rstrip("/")
    else:
        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")

        if forwarded_host:
            host = forwarded_host
            scheme = forwarded_proto
            cantaloupe_base_url = f"{scheme}://{host}/iiif/2"
        else:
            host = request.headers.get("host")
            if host and ":3000" in host:
                cantaloupe_base_url = f"{request.url.scheme}://{host}/iiif/2"
            else:
                cantaloupe_base_url = "http://localhost:8182/iiif/2"

    manifest_id = f"{api_base_url}/iiif/{asset_id}/manifest"
    canvas_id = f"{api_base_url}/iiif/{asset_id}/canvas/1"
    annotation_page_id = f"{api_base_url}/iiif/{asset_id}/page/1"
    annotation_id = f"{api_base_url}/iiif/{asset_id}/annotation/1"

    actual_filename = os.path.basename(asset.file_path) if asset.file_path else asset.filename
    image_service_id = f"{cantaloupe_base_url}/{quote(actual_filename)}"

    metadata_layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
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
