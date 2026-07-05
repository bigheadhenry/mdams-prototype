"""Search Subscription API — 轻量搜索订阅功能

允许用户保存搜索过滤条件，后续通过检查接口获取匹配结果的最新数量。
不需要实际推送机制，只提供存储和手动检查接口。
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SearchSubscription
from ..permissions import CurrentUser, require_any_permission
from ..platform.registry import registry
from ..schemas import (
    SearchSubscriptionCheckResponse,
    SearchSubscriptionCreateRequest,
    SearchSubscriptionResponse,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SearchSubscriptionResponse, status_code=201)
def create_subscription(
    payload: SearchSubscriptionCreateRequest,
    user: CurrentUser = Depends(require_any_permission("platform.view", "application.create")),
    db: Session = Depends(get_db),
):
    """创建一个新的搜索订阅。保存搜索过滤条件以便后续检查。"""
    # Validate query_params is not empty
    if not payload.query_params:
        raise HTTPException(status_code=422, detail="query_params must not be empty")

    # Whitelist allowed filter keys to prevent injection via unexpected params
    ALLOWED_KEYS = {
        "q", "status", "resource_type", "profile_key", "preview_enabled",
        "source_system", "sort_by", "sort_order", "skip", "limit",
    }
    for key in payload.query_params:
        if key not in ALLOWED_KEYS:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown filter key: '{key}'. Allowed: {sorted(ALLOWED_KEYS)}",
            )

    subscription = SearchSubscription(
        user_id=user.user_id,
        name=payload.name,
        query_params=payload.query_params,
        active=True,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.get("", response_model=list[SearchSubscriptionResponse])
def list_subscriptions(
    active_only: bool = True,
    user: CurrentUser = Depends(require_any_permission("platform.view", "application.create")),
    db: Session = Depends(get_db),
):
    """列出当前用户的搜索订阅。"""
    query = db.query(SearchSubscription).filter(
        SearchSubscription.user_id == user.user_id
    )
    if active_only:
        query = query.filter(SearchSubscription.active.is_(True))
    query = query.order_by(SearchSubscription.created_at.desc())
    return query.all()


@router.delete("/{subscription_id}", response_model=dict)
def delete_subscription(
    subscription_id: int,
    user: CurrentUser = Depends(require_any_permission("platform.view", "application.create")),
    db: Session = Depends(get_db),
):
    """删除一个搜索订阅。"""
    subscription = db.query(SearchSubscription).filter(
        SearchSubscription.id == subscription_id,
        SearchSubscription.user_id == user.user_id,
    ).first()
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(subscription)
    db.commit()
    return {"ok": True, "removed": subscription_id}


@router.put("/{subscription_id}/check", response_model=SearchSubscriptionCheckResponse)
def check_subscription(
    subscription_id: int,
    user: CurrentUser = Depends(require_any_permission("platform.view", "application.create")),
    db: Session = Depends(get_db),
):
    """手动检查订阅是否有新匹配结果。

    根据订阅时保存的 query_params，重新查询平台资源并统计匹配总数。
    返回总数和自上次检查以来的新增数量（基于总数变化估算）。
    """
    subscription = db.query(SearchSubscription).filter(
        SearchSubscription.id == subscription_id,
        SearchSubscription.user_id == user.user_id,
    ).first()
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Reconstruct query from stored params
    q = subscription.query_params.get("q") or None
    status = subscription.query_params.get("status") or None
    resource_type = subscription.query_params.get("resource_type") or None
    profile_key = subscription.query_params.get("profile_key") or None
    source_system = subscription.query_params.get("source_system") or None
    preview_enabled_raw = subscription.query_params.get("preview_enabled")

    # Parse preview_enabled if present
    preview_enabled: bool | None = None
    if preview_enabled_raw is not None:
        if isinstance(preview_enabled_raw, bool):
            preview_enabled = preview_enabled_raw
        elif isinstance(preview_enabled_raw, str):
            preview_enabled = preview_enabled_raw.lower() in ("true", "1", "yes")
        else:
            preview_enabled = bool(preview_enabled_raw)

    # Query all matching resources — prefer search engine, fall back to adapters
    engine = None
    try:
        from ..services.search_engine.engine import get_engine
        engine = get_engine()
    except Exception:
        pass

    if engine and engine.health():
        from ..services.search_engine import SearchQuery
        sq = SearchQuery(
            q=q or "",
            filter={
                k: v for k, v in {
                    "status": status,
                    "resource_type": resource_type,
                    "profile_key": profile_key,
                    "source_system": source_system,
                    "preview_enabled": preview_enabled,
                }.items() if v is not None
            },
            limit=0,  # We only need count
        )
        resp = engine.search(sq)
        total_now = resp.total
    else:
        adapters = [registry.get(source_system)] if source_system else list(registry.all())
        if source_system and (not adapters or adapters[0] is None):
            total_now = 0
        else:
            resources: list = []
            for adapter in adapters:
                if adapter is None:
                    continue
                resources.extend(
                    adapter.list_unified_resources(
                        db,
                        q=q,
                        status=status,
                        resource_type=resource_type,
                        profile_key=profile_key,
                        preview_enabled=preview_enabled,
                    )
                )
            total_now = len(resources)

    # Calculate new items since last check
    last_count = getattr(subscription, "_last_count", None)
    previous_total = subscription.query_params.get("_last_total", 0)
    if isinstance(previous_total, (int, float)):
        previous_total = int(previous_total)
    else:
        previous_total = 0

    new_items = max(0, total_now - previous_total)

    # Update subscription
    subscription.last_checked_at = datetime.now(timezone.utc)
    subscription.query_params = dict(subscription.query_params)
    subscription.query_params["_last_total"] = total_now
    db.commit()

    checked_at = subscription.last_checked_at.isoformat() if subscription.last_checked_at else datetime.now(timezone.utc).isoformat()

    return SearchSubscriptionCheckResponse(
        id=subscription.id,
        name=subscription.name,
        checked_at=checked_at,
        total_items=total_now,
        new_items_since_last_check=new_items,
        message=f"Found {total_now} matching resources, {new_items} new since last check",
    )
