from .celery_app import celery_app
from .database import SessionLocal
from .models import Asset
import os
import pyvips
from sqlalchemy.orm import Session

@celery_app.task(bind=True, name="app.tasks.convert_psb_to_bigtiff")
def convert_psb_to_bigtiff(self, asset_id: int, original_path: str):
    """
    Background task to convert PSB to BigTIFF.
    """
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            print(f"Asset {asset_id} not found during background processing.")
            return

        print(f"Starting conversion for Asset {asset_id}: {original_path}")
        
        # Load PSB using pyvips
        # access="sequential" is efficient for large files
        image = pyvips.Image.new_from_file(original_path, access="sequential")
        
        # Define output path (change extension to .tiff)
        base_name = os.path.splitext(original_path)[0]
        output_path = f"{base_name}.tiff"
        
        # Save as BigTIFF with JPEG compression, Tiled, Pyramid
        # This is standard for IIIF compatibility
        image.write_to_file(
            output_path, 
            compression="jpeg", 
            tile=True, 
            pyramid=True, 
            bigtiff=True
        )
        
        print(f"Conversion successful: {output_path}")
        
        # Update Asset
        asset.file_path = output_path
        
        # Update metadata
        if asset.metadata_info is None:
            asset.metadata_info = {}
            
        asset.metadata_info["original_file_path"] = original_path
        asset.metadata_info["conversion_method"] = "celery_pyvips_psb_to_bigtiff"
        asset.metadata_info["width"] = image.width
        asset.metadata_info["height"] = image.height
        
        asset.status = "ready"
        
        # Ensure JSON field update is tracked
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(asset, "metadata_info")
        
        db.commit()
        
    except Exception as e:
        print(f"Error converting PSB for Asset {asset_id}: {e}")
        asset.status = "error"
        if asset.metadata_info is None:
            asset.metadata_info = {}
        asset.metadata_info["error_message"] = str(e)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(asset, "metadata_info")
        db.commit()
    finally:
        db.close()
