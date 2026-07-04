"""
Cart API — 后端 Session 购物车

任何系统（MDAMS 前端、文物系统、外部系统）可通过 HTTP API 加车，
无需关心前端组件实现。购物车数据按用户 session 隔离存储。

提交购物车时自动转成 Application 申请单，复用现有审批交付流程。
"""
import random
import threading
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..permissions import CurrentUser, require_permission

# ── In-memory cart storage ──────────────────────────────────
# Keyed by user_id (str). Survives page refreshes but not server restart.
# Design for easy swap to database-backed storage (方案 C upgrade).
_carts: dict[str, list[dict]] = {}
_carts_lock = threading.RLock()  # Protects _carts from concurrent access


# ── Constants ────────────────────────────────────────────────

# Max cart size to prevent resource abuse
MAX_CART_ITEMS = 500

# Max items per import batch
MAX_IMPORT_BATCH = 200

# Allowed enum values for variant / format
ALLOWED_VARIANTS = {"current", "original", "low_res", "high_res", "thumbnail"}
ALLOWED_DELIVERY_FORMATS = {"image", "video", "document", "3d_model", "audio"}


# ── Schemas ─────────────────────────────────────────────────

class CartItemAddRequest(BaseModel):
    """Add item to cart — 外部系统通过此结构加车。"""
    source_system: str = Field(
        ..., description="来源系统标识，如 wenwu / image_2d", max_length=128
    )
    source_id: str = Field(
        ..., description="来源内唯一 ID", max_length=256
    )
    title: str = Field(
        ..., description="资源显示名称", max_length=512
    )
    resource_type: str | None = Field(
        None, description="资源类型", max_length=128
    )
    object_number: str | None = Field(
        None, description="文物编号", max_length=128
    )
    thumbnail_url: str | None = Field(
        None, description="缩略图 URL", max_length=2048
    )
    manifest_url: str | None = Field(
        None, description="IIIF/预览 URL", max_length=2048
    )
    requested_variant: str | None = Field(
        "current", description="请求变体", max_length=64
    )
    delivery_format: str | None = Field(
        "image", description="交付格式", max_length=64
    )
    note: str | None = Field(
        None, description="申请备注", max_length=2000
    )


class CartItemUpdateRequest(BaseModel):
    requested_variant: str | None = Field(None, max_length=64)
    delivery_format: str | None = Field(None, max_length=64)
    note: str | None = Field(None, max_length=2000)


class CartItemResponse(BaseModel):
    id: str
    source_system: str
    source_id: str
    title: str
    resource_type: str | None = None
    object_number: str | None = None
    thumbnail_url: str | None = None
    manifest_url: str | None = None
    requested_variant: str | None = "current"
    delivery_format: str | None = "image"
    note: str | None = None
    created_at: str


class CartSummary(BaseModel):
    items: list[CartItemResponse]
    total: int
    user_id: str


# ── Router ──────────────────────────────────────────────────

router = APIRouter(prefix="/cart", tags=["cart"])


def _get_cart(user_id: str) -> list[dict]:
    """Get or create cart for a user — lock-protected."""
    with _carts_lock:
        if user_id not in _carts:
            _carts[user_id] = []
        return _carts[user_id]


def _to_response(item: dict) -> CartItemResponse:
    return CartItemResponse(
        id=item["id"],
        source_system=item["source_system"],
        source_id=item["source_id"],
        title=item["title"],
        resource_type=item.get("resource_type"),
        object_number=item.get("object_number"),
        thumbnail_url=item.get("thumbnail_url"),
        manifest_url=item.get("manifest_url"),
        requested_variant=item.get("requested_variant", "current"),
        delivery_format=item.get("delivery_format", "image"),
        note=item.get("note"),
        created_at=item["created_at"],
    )


def _validate_variant_format(variant: str | None, delivery_format: str | None) -> None:
    """Validate requested_variant and delivery_format against allowed values."""
    if variant is not None and variant not in ALLOWED_VARIANTS:
        allowed = ", ".join(sorted(ALLOWED_VARIANTS))
        raise HTTPException(
            status_code=422,
            detail=f"Invalid requested_variant '{variant}'. Allowed: {allowed}",
        )
    if delivery_format is not None and delivery_format not in ALLOWED_DELIVERY_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_DELIVERY_FORMATS))
        raise HTTPException(
            status_code=422,
            detail=f"Invalid delivery_format '{delivery_format}'. Allowed: {allowed}",
        )


@router.get("", response_model=CartSummary)
def list_cart(user: CurrentUser = Depends(require_permission("application.create"))):
    """查看当前用户的购物车内容。"""
    cart = _get_cart(user.user_id)
    return CartSummary(
        items=[_to_response(item) for item in cart],
        total=len(cart),
        user_id=user.user_id,
    )


@router.post("/items", response_model=CartItemResponse)
def add_to_cart(
    payload: CartItemAddRequest,
    user: CurrentUser = Depends(require_permission("application.create")),
):
    """加入购物车。外部系统只需传 source_system + source_id + title 即可。"""
    # Validate variant/format early
    _validate_variant_format(payload.requested_variant, payload.delivery_format)

    with _carts_lock:
        cart = _get_cart(user.user_id)

        if len(cart) >= MAX_CART_ITEMS:
            raise HTTPException(
                status_code=413,
                detail=f"购物车已满（上限 {MAX_CART_ITEMS} 项），无法继续添加",
            )

        # 去重：同一来源同一 ID 不重复添加
        for item in cart:
            if item["source_system"] == payload.source_system and item["source_id"] == payload.source_id:
                raise HTTPException(status_code=409, detail="该资源已在申请车中")

        new_item = {
            "id": uuid.uuid4().hex[:12],
            "source_system": payload.source_system,
            "source_id": payload.source_id,
            "title": payload.title,
            "resource_type": payload.resource_type,
            "object_number": payload.object_number,
            "thumbnail_url": payload.thumbnail_url,
            "manifest_url": payload.manifest_url,
            "requested_variant": payload.requested_variant or "current",
            "delivery_format": payload.delivery_format or "image",
            "note": payload.note,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        cart.append(new_item)

    return _to_response(new_item)


@router.delete("/items/{item_id}", response_model=dict)
def remove_from_cart(
    item_id: str,
    user: CurrentUser = Depends(require_permission("application.create")),
):
    """从购物车移除一项。"""
    with _carts_lock:
        cart = _get_cart(user.user_id)
        for i, item in enumerate(cart):
            if item["id"] == item_id:
                cart.pop(i)
                return {"removed": item_id, "ok": True}
    raise HTTPException(status_code=404, detail="Item not found in cart")


@router.patch("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: str,
    payload: CartItemUpdateRequest,
    user: CurrentUser = Depends(require_permission("application.create")),
):
    """修改购物车中某项的 variant/format/note。"""
    # Validate variant/format early
    _validate_variant_format(payload.requested_variant, payload.delivery_format)

    with _carts_lock:
        cart = _get_cart(user.user_id)
        for item in cart:
            if item["id"] == item_id:
                if payload.requested_variant is not None:
                    item["requested_variant"] = payload.requested_variant
                if payload.delivery_format is not None:
                    item["delivery_format"] = payload.delivery_format
                if payload.note is not None:
                    item["note"] = payload.note
                return _to_response(item)
    raise HTTPException(status_code=404, detail="Item not found in cart")


@router.delete("", response_model=dict)
def clear_cart(user: CurrentUser = Depends(require_permission("application.create"))):
    """清空购物车。"""
    with _carts_lock:
        _carts[user.user_id] = []
    return {"cleared": True, "ok": True}


# ── Submit cart as application ─────────────────────────────

class CartSubmitRequest(BaseModel):
    requester_name: str = Field(..., description="申请人", max_length=128)
    requester_org: str | None = Field(None, description="所属机构", max_length=256)
    contact_email: str | None = Field(None, description="联系邮箱", max_length=320)
    purpose: str = Field(..., description="申请用途：出版配图/展览展示/学术研究等", max_length=1024)
    usage_scope: str | None = Field(None, description="使用范围", max_length=1024)


# ── Batch import ─────────────────────────────────────────────

class CartImportRequest(BaseModel):
    """批量导入购物车请求体。"""
    items: list[CartItemAddRequest] = Field(
        ..., description="待加车的资源列表", max_length=MAX_IMPORT_BATCH
    )


class CartImportResponse(BaseModel):
    """批量导入响应。"""
    ok: bool = True
    added: int = 0
    duplicates: int = 0
    failed: list[dict] = Field(default_factory=list, description="导入失败的条目及原因")
    cart_total: int = 0


# ── Object-number image lookup ───────────────────────────────

class CartLookupRecord(BaseModel):
    """按文物号查询到的关联影像记录。"""
    source_system: str
    source_id: str
    title: str
    thumbnail_url: str | None = None
    resolution: str | None = None
    photographer: str | None = None
    shoot_date: str | None = None
    content: str | None = None
    file_size: int | None = None
    mime_type: str | None = None


class CartLookupResponse(BaseModel):
    """关联影像查询结果。"""
    object_number: str
    total: int
    page: int
    size: int
    items: list[CartLookupRecord] = Field(default_factory=list)


@router.post("/submit", response_model=dict)
def submit_cart(
    payload: CartSubmitRequest,
    user: CurrentUser = Depends(require_permission("application.create")),
):
    """将购物车内容转为正式申请单，提交后进入审批流程。"""
    from ..database import SessionLocal
    from ..models import Application, ApplicationItem
    from ..services.application_delivery import build_application_export_package
    from ..routers.applications import _build_application_no, _write_audit_log

    # Atomically snapshot and clear the cart under lock
    with _carts_lock:
        cart = _carts.get(user.user_id, [])
        if not cart:
            raise HTTPException(status_code=400, detail="购物车为空，无法提交")
        # Snapshot the cart content before clearing
        cart_snapshot = list(cart)
        _carts[user.user_id] = []

    db = SessionLocal()
    try:
        application = Application(
            application_no=_build_application_no(),
            requester_name=payload.requester_name,
            requester_org=payload.requester_org,
            contact_email=payload.contact_email,
            purpose=payload.purpose,
            usage_scope=payload.usage_scope,
            status="submitted",
        )
        db.add(application)
        db.flush()

        for item in cart_snapshot:
            app_item = ApplicationItem(
                application_id=application.id,
                asset_id=None,  # 无本地资产关联，通过 source 定位
                source_system=item["source_system"],
                source_id=item["source_id"],
                resource_type=item.get("resource_type"),
                resource_title=item["title"],
                manifest_url=item.get("manifest_url"),
                source_label=item.get("source_system"),
                object_number=item.get("object_number"),
                requested_variant=item.get("requested_variant"),
                delivery_format=item.get("delivery_format"),
                note=item.get("note"),
            )
            db.add(app_item)

        _write_audit_log(
            application_id=application.id,
            action="submitted",
            from_status=None,
            to_status="submitted",
            actor=user,
            review_note=None,
            db=db,
        )

        db.commit()
        db.refresh(application)

        return {
            "ok": True,
            "application_no": application.application_no,
            "application_id": application.id,
            "item_count": len(cart_snapshot),
            "message": "申请单已提交，进入审批流程",
        }
    except Exception:
        db.rollback()
        # Restore cart items on failure so the user can retry
        with _carts_lock:
            # Only restore if cart is still empty (user hasn't added new items)
            if not _carts.get(user.user_id):
                _carts[user.user_id] = cart_snapshot
        raise
    finally:
        db.close()


# ── Batch import ─────────────────────────────────────────────


@router.post("/import", response_model=CartImportResponse)
def import_cart_items(
    payload: CartImportRequest,
    user: CurrentUser = Depends(require_permission("application.create")),
):
    """批量导入资源到购物车。自动去重，返回新增/重复/失败统计。"""
    # Validate each item's variant/format before mutating cart
    for item in payload.items:
        _validate_variant_format(item.requested_variant, item.delivery_format)

    with _carts_lock:
        cart = _get_cart(user.user_id)
        existing_pairs: set[tuple[str, str]] = {
            (item["source_system"], item["source_id"]) for item in cart
        }

        # Check if adding would exceed max cart size
        available_slots = MAX_CART_ITEMS - len(cart)
        if available_slots <= 0:
            raise HTTPException(
                status_code=413,
                detail=f"购物车已满（上限 {MAX_CART_ITEMS} 项），无法批量导入",
            )

        # Truncate payload if it would exceed max cart size
        items_to_process = payload.items[:available_slots]

        added = 0
        duplicates = 0
        failed: list[dict] = []

        for idx, item in enumerate(payload.items):
            pair = (item.source_system, item.source_id)

            if pair in existing_pairs:
                duplicates += 1
                continue

            if added >= available_slots:
                # Silently stop — remaining items are truncated
                break

            try:
                new_item = {
                    "id": uuid.uuid4().hex[:12],
                    "source_system": item.source_system,
                    "source_id": item.source_id,
                    "title": item.title,
                    "resource_type": item.resource_type,
                    "object_number": item.object_number,
                    "thumbnail_url": item.thumbnail_url,
                    "manifest_url": item.manifest_url,
                    "requested_variant": item.requested_variant or "current",
                    "delivery_format": item.delivery_format or "image",
                    "note": item.note,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                cart.append(new_item)
                existing_pairs.add(pair)
                added += 1
            except Exception as exc:
                failed.append({"index": idx, "source_id": item.source_id, "reason": str(exc)})

        return CartImportResponse(
            ok=len(failed) == 0,
            added=added,
            duplicates=duplicates,
            failed=failed,
            cart_total=len(cart),
        )


# ── Object-number image lookup ───────────────────────────────

CONTENT_LABELS = ["正面", "背面", "侧面", "局部", "底部", "顶部", "俯视", "微距"]

PHOTOGRAPHERS = [
    "张莹",
    "李军",
    "王磊",
    "陈静",
    "赵刚",
    "刘芳",
]

MIME_TYPES = ["image/tiff", "image/jpeg", "image/jp2", "image/png"]


def _generate_mock_lookup_records(
    object_number: str,
    *,
    content_filter: str | None = None,
    photographer_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[CartLookupRecord], int]:
    """生成按文物号查询的模拟影像数据。

    NOTE: 模拟数据仅用于开发/演示环境。生产环境应关闭此回退逻辑，
    确保 DB 查询失败时返回 503 而非模拟数据，避免信息泄露。
    """
    import hashlib

    digest = hashlib.sha1(object_number.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:4], "big")

    rng = random.Random(seed)
    total_mock = (seed % 20) + 3  # 3–22 条模拟影像

    records: list[CartLookupRecord] = []
    for i in range(total_mock):
        content = rng.choice(CONTENT_LABELS)
        photographer = rng.choice(PHOTOGRAPHERS)
        year = 2024 if rng.random() < 0.6 else 2023
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        shoot_date_iso = f"{year:04d}-{month:02d}-{day:02d}"

        # Apply filters
        if content_filter and content_filter not in content:
            continue
        if photographer_filter and photographer_filter != photographer:
            continue
        if date_from and shoot_date_iso < date_from.isoformat():
            continue
        if date_to and shoot_date_iso > date_to.isoformat():
            continue

        width = rng.choice([2000, 4000, 6000, 8000])
        height = rng.choice([1500, 3000, 4000, 6000])
        resolution = f"{width}x{height}"
        file_size = rng.randint(5_000_000, 200_000_000)  # 5MB–200MB
        mime_type = rng.choice(MIME_TYPES)

        records.append(
            CartLookupRecord(
                source_system="image_2d_cultural_object",
                source_id=f"mock-img-{object_number}-{i + 1:02d}",
                title=f"{content}影像 — {object_number}",
                thumbnail_url=None,  # No real thumbnail for mock data — avoid path leakage
                resolution=resolution,
                photographer=photographer,
                shoot_date=shoot_date_iso,
                content=content,
                file_size=file_size,
                mime_type=mime_type,
            )
        )

    total = len(records)
    start = (page - 1) * size
    end = start + size
    return records[start:end], total


@router.get("/lookup", response_model=CartLookupResponse)
def lookup_cart_by_object_number(
    object_number: str = Query(..., description="文物编号", min_length=2, max_length=128),
    content: str | None = Query(None, description="影像内容（正面/背面/局部…）"),
    photographer: str | None = Query(None, description="摄影师"),
    date_from: date | None = Query(None, description="拍摄日期起始（ISO 格式）"),
    date_to: date | None = Query(None, description="拍摄日期截止（ISO 格式）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页条数"),
    user: CurrentUser = Depends(require_permission("application.create")),
):
    """按文物号查询关联影像，支持按内容/摄影师/日期范围筛选。

    优先查询数据库中的 ImageRecord / Asset 表，若未找到真实数据则返回模拟结果。
    """
    if not object_number:
        raise HTTPException(status_code=400, detail="参数 object_number 不能为空")

    # ── Try database lookup first ─────────────────────────
    try:
        from ..database import SessionLocal
        from ..models import ImageRecord, Asset, ThreeDCollectionObject
        from sqlalchemy import or_

        db = SessionLocal()
        try:
            # Find ThreeDCollectionObject by object_number
            col_obj = (
                db.query(ThreeDCollectionObject)
                .filter(ThreeDCollectionObject.object_number == object_number)
                .first()
            )

            db_records: list[CartLookupRecord] = []
            if col_obj is not None:
                # Query ImageRecord linked to this collection_object_id
                query = (
                    db.query(ImageRecord, Asset)
                    .outerjoin(Asset, Asset.image_record_id == ImageRecord.id)
                    .filter(ImageRecord.collection_object_id == col_obj.id)
                )

                if content:
                    query = query.filter(
                        or_(
                            ImageRecord.title.ilike(f"%{content}%"),
                            ImageRecord.metadata_info["content"].as_string().ilike(f"%{content}%"),
                        )
                    )

                for img_rec, asset in query.all():
                    meta = img_rec.metadata_info or {}
                    db_records.append(
                        CartLookupRecord(
                            source_system="image_2d_cultural_object",
                            source_id=str(img_rec.id),
                            title=img_rec.title or f"影像 #{img_rec.record_no}",
                            thumbnail_url=f"/api/assets/{asset.id}/thumbnail" if asset else None,
                            resolution=f"{asset.width or '?'}x{asset.height or '?'}"
                            if asset and hasattr(asset, 'width')
                            else None,
                            photographer=meta.get("photographer"),
                            shoot_date=img_rec.created_at.strftime("%Y-%m-%d") if img_rec.created_at else None,
                            content=meta.get("content"),
                            file_size=asset.file_size if asset else None,
                            mime_type=asset.mime_type if asset else None,
                        )
                    )

            if db_records:
                # Apply date filters (Python side for JSON-metadata fields)
                filtered = db_records
                if photographer:
                    filtered = [r for r in filtered if r.photographer == photographer]
                if date_from:
                    filtered = [r for r in filtered if r.shoot_date and r.shoot_date >= date_from.isoformat()]
                if date_to:
                    filtered = [r for r in filtered if r.shoot_date and r.shoot_date <= date_to.isoformat()]

                total = len(filtered)
                start = (page - 1) * size
                end = start + size
                return CartLookupResponse(
                    object_number=object_number,
                    total=total,
                    page=page,
                    size=size,
                    items=filtered[start:end],
                )
        finally:
            db.close()
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Cart lookup DB query failed, falling back to mock data", exc_info=True
        )
        # Fall through to mock data on any DB error
        pass

    # ── Fallback: generated mock data ──────────────────────
    items, total = _generate_mock_lookup_records(
        object_number,
        content_filter=content,
        photographer_filter=photographer,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )

    return CartLookupResponse(
        object_number=object_number,
        total=total,
        page=page,
        size=size,
        items=items,
    )
