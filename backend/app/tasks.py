import os

from sqlalchemy.orm import Session

from .celery_app import celery_app
from .database import SessionLocal
from .models import Asset
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
