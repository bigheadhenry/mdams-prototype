from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import Asset
import shutil
import os
from datetime import datetime
from typing import List
from pydantic import BaseModel
from urllib.parse import quote

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
    db_asset = Asset(
        filename=file.filename,
        file_path=file_location,
        file_size=file_size,
        mime_type=file.content_type,
        status="ready"
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    return db_asset

@app.get("/iiif/{asset_id}/manifest")
def get_iiif_manifest(asset_id: int, db: Session = Depends(get_db)):
    """
    Generate IIIF Presentation API 3.0 Manifest dynamically from Asset metadata.
    根据资产元数据动态生成 IIIF Presentation API 3.0 Manifest。
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Base URLs from Environment Variables
    # 从环境变量获取基础 URL
    # API_PUBLIC_URL should point to the Nginx entry point (e.g., http://192.168.5.13:3000/api)
    # CANTALOUPE_PUBLIC_URL should point to the Cantaloupe server (e.g., http://192.168.5.13:8182/iiif/2)
    
    api_base_url = os.getenv("API_PUBLIC_URL", "http://localhost:8000")
    # Remove trailing slash if present
    if api_base_url.endswith("/"):
        api_base_url = api_base_url[:-1]

    cantaloupe_base_url = os.getenv("CANTALOUPE_PUBLIC_URL", "http://localhost:8182/iiif/2")
    if cantaloupe_base_url.endswith("/"):
        cantaloupe_base_url = cantaloupe_base_url[:-1]

    
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
    image_service_id = f"{cantaloupe_base_url}/{quote(asset.filename)}"

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
                "height": 1000, 
                "width": 1000,
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
    # 如果有额外元数据则注入
    if asset.metadata_info:
        for key, value in asset.metadata_info.items():
             manifest["metadata"].append({
                 "label": {"en": [key]},
                 "value": {"en": [str(value)]}
             })


    return manifest

@app.get("/assets", response_model=List[AssetOut])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = db.query(Asset).offset(skip).limit(limit).all()
    return assets
