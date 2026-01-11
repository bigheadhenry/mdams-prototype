from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import Asset
from .routers.ingest import router as ingest_router
import shutil
import os
from datetime import datetime
from typing import List
from pydantic import BaseModel
from urllib.parse import quote
from PIL import Image

# Initialize DB tables
# 初始化数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MEAM Prototype API")

# CORS config
# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prototype, allow all. Tighten for prod. # 原型开发阶段允许所有来源。生产环境需收紧策略。
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"], # Required for IIIF readers sometimes # IIIF 阅读器有时需要此配置
)

# Storage setup
# 存储设置
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic models
# Pydantic 模型
class AssetOut(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    status: str

    class Config:
        orm_mode = True

app.include_router(ingest_router)

@app.get("/debug/files")
def list_uploaded_files():
    """
    Debug endpoint to list files in the upload directory and their permissions.
    """
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            filepath = os.path.join(UPLOAD_DIR, filename)
            stat = os.stat(filepath)
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "permissions": oct(stat.st_mode)[-3:],
                "uid": stat.st_uid,
                "gid": stat.st_gid
            })
        return {
            "upload_dir": UPLOAD_DIR,
            "abs_path": os.path.abspath(UPLOAD_DIR),
            "files": files,
            "dir_permissions": oct(os.stat(UPLOAD_DIR).st_mode)[-3:]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Welcome to MEAM Prototype API"}

@app.post("/upload", response_model=AssetOut)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Save file to disk (Streamed write to avoid memory spike)
    # 1. 保存文件到磁盘（流式写入以避免内存峰值）
    # Use NAS path mapped in Docker
    # 使用 Docker 中映射的 NAS 路径
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    
    # 64KB chunk size for network IO optimization
    # 64KB 块大小优化网络 IO
    CHUNK_SIZE = 64 * 1024 
    
    with open(file_location, "wb") as buffer:
        while content := await file.read(CHUNK_SIZE):
            buffer.write(content)
    
    # 2. Get file size
    # 2. 获取文件大小
    file_size = os.path.getsize(file_location)
    
    # 3. Create DB record
    # 3. 创建数据库记录
    # Extract dimensions
    width, height = 0, 0
    try:
        with Image.open(file_location) as img:
            width, height = img.size
    except Exception:
        pass

    db_asset = Asset(
        filename=file.filename,
        file_path=file_location,
        file_size=file_size,
        mime_type=file.content_type,
        status="ready",
        metadata_info={"width": width, "height": height} # No original_metadata here
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    return db_asset

@app.get("/iiif/{asset_id}/manifest")
def get_iiif_manifest(asset_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Generate IIIF Presentation API 3.0 Manifest dynamically from Asset metadata.
    根据资产元数据动态生成 IIIF Presentation API 3.0 Manifest。
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Determine Base URLs dynamically from request headers if possible, otherwise fallback to env
    # 尽可能从请求头动态确定基础 URL，否则回退到环境变量
    
    # PRIORITY 1: Environment Variables (The most reliable source if configured)
    # 优先级 1: 环境变量 (如果配置了，这是最可靠的来源)
    env_api_url = os.getenv("API_PUBLIC_URL")
    env_cantaloupe_url = os.getenv("CANTALOUPE_PUBLIC_URL")

    # 1. API Base URL
    if env_api_url:
        api_base_url = env_api_url.rstrip('/')
    else:
        # Fallback to auto-detection
        # 1. API Base URL (for Manifest ID, Canvas ID, etc.)
        # 1. API 基础 URL (用于 Manifest ID, Canvas ID 等)
        # Check for X-Forwarded-Host (from Nginx) or Host header
        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        forwarded_prefix = request.headers.get("x-forwarded-prefix", "")
        
        if forwarded_host:
             # Behind Nginx Proxy
             host = forwarded_host
             scheme = forwarded_proto
             
             # Use X-Forwarded-Prefix if available (e.g. /api)
             if forwarded_prefix:
                 # Remove trailing slash from prefix if present
                 prefix = forwarded_prefix.rstrip('/')
                 api_base_url = f"{scheme}://{host}{prefix}"
             else:
                 # Assume /api prefix if proxied, but best to rely on env or consistent routing
                 # Nginx config usually proxies /api -> backend root.
                 api_base_url = f"{scheme}://{host}/api"
        else:
            # Direct access (e.g. localhost:8000) or Host header from Nginx
            host = request.headers.get("host")
            if not host:
                 host = "localhost:8000"
            scheme = request.url.scheme
            
            # If Host indicates port 3000, we should assume we are behind Nginx but X-Forwarded-Host was missing
            if ":3000" in host:
                api_base_url = f"{scheme}://{host}/api"
            else:
                api_base_url = f"{scheme}://{host}"

    # 2. Cantaloupe Base URL (for Image Service ID)
    if env_cantaloupe_url:
        cantaloupe_base_url = env_cantaloupe_url.rstrip('/')
    else:
        # Fallback to auto-detection
        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        
        # 2. Cantaloupe 基础 URL (用于图像服务 ID)
        # If we are behind Nginx (port 3000), we want to point to /iiif/2
        # If direct access, we might need env var or default to 8182
        
        if forwarded_host:
             host = forwarded_host
             scheme = forwarded_proto
             # Assume Nginx routing: /iiif/2 -> Cantaloupe
             cantaloupe_base_url = f"{scheme}://{host}/iiif/2"
        else:
            # If no X-Forwarded-Host, check if we have a direct Host header (e.g. from local dev)
            # 如果没有 X-Forwarded-Host，检查是否有直接的 Host 头（例如来自本地开发）
            host = request.headers.get("host")
            if host and ":3000" in host:
                 # Heuristic: If Host port is 3000 (Nginx), assume we want /iiif/2
                 cantaloupe_base_url = f"{scheme}://{host}/iiif/2"
            else:
                 # Fallback to env or assume localhost:8182 for dev
                 # 回退到环境变量或假设开发环境为 localhost:8182
                 cantaloupe_base_url = "http://localhost:8182/iiif/2"

    print(f"DEBUG: Manifest ID Base: {api_base_url}")
    print(f"DEBUG: Cantaloupe Base: {cantaloupe_base_url}")
    print(f"DEBUG: Request Headers: {request.headers}")
    
    # Construct Canvas ID and Image ID
    # 构建 Canvas ID 和 Image ID
    manifest_id = f"{api_base_url}/iiif/{asset_id}/manifest"
    canvas_id = f"{api_base_url}/iiif/{asset_id}/canvas/1"
    annotation_page_id = f"{api_base_url}/iiif/{asset_id}/page/1"
    annotation_id = f"{api_base_url}/iiif/{asset_id}/annotation/1"
    
    # Image Service ID (Cantaloupe)
    # 图像服务 ID (Cantaloupe)
    # Cantaloupe serves images by filename.
    # Cantaloupe 通过文件名提供图像服务。
    # Ensure filename is URL encoded for the manifest
    # Use the actual file path on disk (basename) to support converted files (e.g., PSB -> TIFF)
    actual_filename = os.path.basename(asset.file_path) if asset.file_path else asset.filename
    image_service_id = f"{cantaloupe_base_url}/{quote(actual_filename)}"

    # Basic Manifest Structure (IIIF Presentation 3.0)
    # 基础 Manifest 结构 (IIIF Presentation 3.0)
    manifest = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": manifest_id,
        "type": "Manifest",
        "label": {
            "en": [asset.filename],
            "zh-cn": [asset.filename]
        },
        "metadata": [
            {"label": {"en": ["File Size"]}, "value": {"en": [f"{asset.file_size} bytes"]}},
            {"label": {"en": ["MIME Type"]}, "value": {"en": [asset.mime_type]}},
            {"label": {"en": ["Uploaded At"]}, "value": {"en": [str(asset.created_at)]}}
        ],
        "items": [
            {
                "id": canvas_id,
                "type": "Canvas",
                "label": { "en": ["Page 1"] },
                # Width/Height should ideally come from image metadata (libvips)
                # 宽高信息理想情况下应来自图像元数据 (libvips)
                # For now, we default to a placeholder or 0 if unknown (Mirador handles 0 gracefully usually, or we query Cantaloupe info.json)
                # 目前如果未知则默认为占位符或 0（Mirador 通常能优雅处理 0，或者我们会查询 Cantaloupe info.json）
                # TODO: Extract real dimensions using libvips during upload
                # 待办: 上传时使用 libvips 提取真实尺寸
                "height": asset.metadata_info.get("height", 1000) if asset.metadata_info else 1000, 
                "width": asset.metadata_info.get("width", 1000) if asset.metadata_info else 1000,
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
                                            "profile": "level2"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Inject extra metadata if available
    if asset.metadata_info:
        for key, value in asset.metadata_info.items():
             # Skip original_metadata blob to keep Manifest clean and avoid parsing issues
             if key == "original_metadata":
                 continue
                 
             manifest["metadata"].append({
                 "label": {"en": [key]},
                 "value": {"en": [str(value)]}
             })


    return manifest

@app.get("/assets", response_model=List[AssetOut])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = db.query(Asset).offset(skip).limit(limit).all()
    return assets

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    """
    Delete an asset and its corresponding file.
    删除资产及其对应的物理文件。
    """
    # 1. Find asset in DB
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # 2. Delete physical file
    try:
        if os.path.exists(asset.file_path):
            os.remove(asset.file_path)
            print(f"Deleted file: {asset.file_path}")
        else:
            print(f"File not found on disk: {asset.file_path}")
    except Exception as e:
        # Log error but continue to delete DB record so state is consistent
        print(f"Error deleting file {asset.file_path}: {e}")
        # raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    # 3. Delete DB record
    db.delete(asset)
    db.commit()

    return {"status": "success", "message": f"Asset {asset_id} deleted"}

from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
import tempfile
import zipfile

@app.get("/assets/{asset_id}/download-bag")
def download_asset_bag(asset_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Generate and download a BagIt-compliant ZIP package for the asset.
    生成并下载资产的 BagIt 兼容 ZIP 包。
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if not os.path.exists(asset.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")

    # Create a temporary directory for the bag
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    bag_name = f"bag_{asset_id}"
    bag_root = os.path.join(temp_dir, bag_name)
    data_dir = os.path.join(bag_root, "data")
    
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # 1. Copy file to data directory
        # 复制文件到 data 目录
        
        # Determine actual file name on disk
        # 确定磁盘上的实际文件名
        actual_filename = os.path.basename(asset.file_path)
        dest_path = os.path.join(data_dir, actual_filename)
        shutil.copy2(asset.file_path, dest_path)
        
        # If the file was converted (e.g. PSB -> TIFF), we should ideally include the original too if available.
        # But for this prototype, we just package what's currently the 'active' file.
        # However, to be strict about BagIt and preservation, if we converted it, we should probably:
        # a) Package the TIFF as the "preservation copy" (if we consider it so)
        # b) OR package the original PSB (if we still have it)
        
        # Current logic: asset.file_path points to the TIFF after conversion.
        # asset.metadata_info['original_file_path'] points to the PSB.
        
        # Let's include BOTH if they differ, to ensure full preservation.
        # 如果文件已转换（例如 PSB -> TIFF），我们最好也包含原始文件。
        # 当前逻辑：asset.file_path 指向转换后的 TIFF。
        # asset.metadata_info['original_file_path'] 指向原始 PSB。
        # 让我们同时包含两者（如果不同），以确保完整保存。
        
        original_file_path = asset.metadata_info.get("original_file_path") if asset.metadata_info else None
        
        manifest_entries = []
        manifest_entries.append(f"{asset.metadata_info.get('fixity_sha256', 'unknown')}  data/{actual_filename}")

        if original_file_path and os.path.exists(original_file_path) and original_file_path != asset.file_path:
             original_basename = os.path.basename(original_file_path)
             dest_original_path = os.path.join(data_dir, original_basename)
             shutil.copy2(original_file_path, dest_original_path)
             # We don't have SHA256 for the converted file readily available without calc, 
             # but we have it for the original from ingest.
             # Note: The fixity_sha256 in DB is for the ORIGINAL file.
             manifest_entries.append(f"{asset.metadata_info.get('fixity_sha256', 'unknown')}  data/{original_basename}")
             
             # If we are including both, we should clarify which checksum belongs to which.
             # For this PoC, we assume the checksum in DB belongs to the original file.
             # The converted file's checksum is not yet calculated/stored.
             # So we mark the converted file as 'generated-file' in manifest? 
             # Or just recalculate it now.
             
             # Simple approach: Recalculate hash for the converted file
             import hashlib
             def calculate_sha256(filepath):
                sha256_hash = hashlib.sha256()
                with open(filepath, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                return sha256_hash.hexdigest()
             
             converted_hash = calculate_sha256(asset.file_path)
             # Update the entry for the converted file with correct hash
             manifest_entries[0] = f"{converted_hash}  data/{actual_filename}"

        
        # 2. Generate manifest-sha256.txt
        # 生成 manifest-sha256.txt
        with open(os.path.join(bag_root, "manifest-sha256.txt"), "w", encoding="utf-8") as f:
            for entry in manifest_entries:
                f.write(f"{entry}\n")
            
        # 3. Generate bagit.txt
        # 生成 bagit.txt
        with open(os.path.join(bag_root, "bagit.txt"), "w", encoding="utf-8") as f:
            f.write("BagIt-Version: 1.0\n")
            f.write("Tag-File-Character-Encoding: UTF-8\n")
            
        # 4. Generate bag-info.txt (Optional but good)
        # 生成 bag-info.txt
        with open(os.path.join(bag_root, "bag-info.txt"), "w", encoding="utf-8") as f:
            f.write(f"Source-Organization: MEAM Prototype\n")
            f.write(f"Bagging-Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"Payload-Oxum: {asset.file_size}.1\n")
            if original_file_path:
                 f.write(f"Original-File: {os.path.basename(original_file_path)}\n")
            
        # 5. Zip the directory
        # 打包目录
        zip_filename = f"{bag_name}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(bag_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir) # bag_123/data/foo.jpg
                    zipf.write(file_path, arcname)
                    
        # Cleanup temp dir after sending response
        background_tasks.add_task(shutil.rmtree, temp_dir)
        
        return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to generate bag: {str(e)}")
