from __future__ import annotations

import json
import logging
import re
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..permissions import CurrentUser, ensure_current_user, require_permission
from ..services.iiif_access import is_iiif_ready
from ..services.metadata_layers import get_metadata_layers

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

ALLOWED_ACTIONS = {
    "zoom_in",
    "zoom_out",
    "pan_left",
    "pan_right",
    "pan_up",
    "pan_down",
    "reset_view",
    "fit_to_window",
    "search_assets",
    "open_compare",
    "switch_compare_mode",
    "close_compare",
    "noop",
}


class MiradorSearchResult(BaseModel):
    asset_id: int
    title: str
    manifest_url: str
    resource_id: str
    object_number: str | None = None
    filename: str | None = None
    score: float = 0.0
    reasons: list[str] = Field(default_factory=list)


class MiradorAIRequest(BaseModel):
    prompt: str
    current_asset_id: int | None = None
    current_manifest_url: str | None = None
    current_title: str | None = None
    current_object_number: str | None = None
    current_resource_id: str | None = None
    max_candidates: int = 5


class MiradorAIPlan(BaseModel):
    action: Literal[
        "zoom_in",
        "zoom_out",
        "pan_left",
        "pan_right",
        "pan_up",
        "pan_down",
        "reset_view",
        "fit_to_window",
        "search_assets",
        "open_compare",
        "switch_compare_mode",
        "close_compare",
        "noop",
    ]
    assistant_message: str
    requires_confirmation: bool = False
    search_query: str | None = None
    search_results: list[MiradorSearchResult] = Field(default_factory=list)
    target_asset: MiradorSearchResult | None = None
    compare_mode: Literal["single", "side_by_side"] | None = None
    pan_pixels: int | None = None
    zoom_factor: float | None = None


def _short_prompt(prompt: str, limit: int = 80) -> str:
    compact = " ".join(prompt.split())
    return compact if len(compact) <= limit else f"{compact[:limit].rstrip()}..."


def _api_base_url(request: Request) -> str:
    if config.API_PUBLIC_URL:
        return config.API_PUBLIC_URL.rstrip("/")

    forwarded_host = request.headers.get("x-forwarded-host")
    forwarded_proto = request.headers.get("x-forwarded-proto", "http")
    if forwarded_host:
        prefix = request.headers.get("x-forwarded-prefix", "").rstrip("/")
        if prefix:
            return f"{forwarded_proto}://{forwarded_host}{prefix}"
        return f"{forwarded_proto}://{forwarded_host}/api"

    host = request.headers.get("host") or "localhost:8000"
    if ":3000" in host:
        return f"{request.url.scheme}://{host}/api"
    return f"{request.url.scheme}://{host}"


def _asset_visibility_scope(asset: Asset) -> str:
    visibility_scope = getattr(asset, "visibility_scope", None)
    if visibility_scope:
        return str(visibility_scope)
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    core = metadata.get("core") if isinstance(metadata, dict) else {}
    if isinstance(core, dict) and core.get("visibility_scope") not in (None, ""):
        return str(core.get("visibility_scope"))
    return "open"


def _asset_collection_object_id(asset: Asset) -> int | None:
    collection_object_id = getattr(asset, "collection_object_id", None)
    if isinstance(collection_object_id, int):
        return collection_object_id
    if isinstance(collection_object_id, str) and collection_object_id.isdigit():
        return int(collection_object_id)
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    core = metadata.get("core") if isinstance(metadata, dict) else {}
    if isinstance(core, dict):
        value = core.get("collection_object_id")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def _is_asset_visible_to_user(asset: Asset, user: CurrentUser) -> bool:
    from ..permissions import can_access_visibility_scope

    return can_access_visibility_scope(
        user,
        visibility_scope=_asset_visibility_scope(asset),
        collection_object_id=_asset_collection_object_id(asset),
    )


def _flatten_metadata_text(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, dict):
        pieces: list[str] = []
        for item in value.values():
            pieces.extend(_flatten_metadata_text(item))
        return pieces
    if isinstance(value, list):
        pieces: list[str] = []
        for item in value:
            pieces.extend(_flatten_metadata_text(item))
        return pieces
    return [str(value)]


def _asset_metadata_layers(asset: Asset) -> dict[str, object]:
    return get_metadata_layers(
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


def _extract_title(asset: Asset) -> str:
    metadata_layers = _asset_metadata_layers(asset)
    core = metadata_layers.get("core", {}) if isinstance(metadata_layers, dict) else {}
    title = core.get("title") if isinstance(core, dict) else None
    return str(title or asset.filename or f"Asset {asset.id}")


def _extract_object_number(asset: Asset) -> str | None:
    metadata_layers = _asset_metadata_layers(asset)
    core = metadata_layers.get("core", {}) if isinstance(metadata_layers, dict) else {}
    value = core.get("object_number") if isinstance(core, dict) else None
    return str(value) if value not in (None, "") else None


def _normalize_query(query: str) -> list[str]:
    return [token for token in re.split(r"\s+", query.strip().lower()) if token]


def _score_asset(asset: Asset, query: str) -> tuple[float, list[str]]:
    tokens = _normalize_query(query)
    if not tokens:
        return 0.0, []

    metadata_layers = _asset_metadata_layers(asset)
    core = metadata_layers.get("core", {}) if isinstance(metadata_layers, dict) else {}
    searchable_values = [
        asset.filename or "",
        asset.file_path or "",
        asset.process_message or "",
        _extract_title(asset),
        str(core.get("resource_id") or "") if isinstance(core, dict) else "",
        str(core.get("object_number") or "") if isinstance(core, dict) else "",
        " ".join(_flatten_metadata_text(asset.metadata_info or {})),
    ]
    haystack = "\n".join(searchable_values).lower()
    score = 0.0
    reasons: list[str] = []
    for token in tokens:
        if token in haystack:
            score += 1.0
            reasons.append(token)
    if query.strip().lower() in haystack:
        score += 2.0
        reasons.append("exact")
    return score, reasons


def _build_manifest_url(request: Request, asset_id: int) -> str:
    return f"{_api_base_url(request)}/iiif/{asset_id}/manifest"


def _build_search_result(request: Request, asset: Asset, score: float, reasons: list[str]) -> MiradorSearchResult:
    metadata_layers = _asset_metadata_layers(asset)
    core = metadata_layers.get("core", {}) if isinstance(metadata_layers, dict) else {}
    resource_id = str(core.get("resource_id") or f"image_2d:{asset.id}") if isinstance(core, dict) else f"image_2d:{asset.id}"
    return MiradorSearchResult(
        asset_id=asset.id,
        title=_extract_title(asset),
        manifest_url=_build_manifest_url(request, asset.id),
        resource_id=resource_id,
        object_number=_extract_object_number(asset),
        filename=asset.filename,
        score=round(score, 3),
        reasons=reasons,
    )


def _search_assets(
    db: Session,
    user: CurrentUser,
    request: Request,
    query: str,
    *,
    limit: int = 5,
    current_asset_id: int | None = None,
) -> list[MiradorSearchResult]:
    assets = db.query(Asset).order_by(Asset.created_at.desc(), Asset.id.desc()).all()
    results: list[MiradorSearchResult] = []
    for asset in assets:
        if current_asset_id is not None and asset.id == current_asset_id:
            continue
        if not _is_asset_visible_to_user(asset, user):
            continue
        if not is_iiif_ready(asset):
            continue
        score, reasons = _score_asset(asset, query)
        if score > 0:
            results.append(_build_search_result(request, asset, score, reasons))

    results.sort(key=lambda item: (-item.score, item.title.lower(), item.asset_id))
    return results[:limit]


def _extract_json_object(text: str) -> dict[str, object] | None:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _heuristic_plan(prompt: str) -> MiradorAIPlan:
    normalized = prompt.strip().lower()

    if any(keyword in normalized for keyword in ["zoom in", "放大", "拉近", "大一点", "大些"]):
        return MiradorAIPlan(action="zoom_in", assistant_message="已放大当前画面。", zoom_factor=2.0)
    if any(keyword in normalized for keyword in ["zoom out", "缩小", "远一点", "小一点"]):
        return MiradorAIPlan(action="zoom_out", assistant_message="已缩小当前画面。", zoom_factor=0.5)
    if any(keyword in normalized for keyword in ["左移", "向左", "往左"]):
        return MiradorAIPlan(action="pan_left", assistant_message="已向左平移画面。", pan_pixels=120)
    if any(keyword in normalized for keyword in ["右移", "向右", "往右"]):
        return MiradorAIPlan(action="pan_right", assistant_message="已向右平移画面。", pan_pixels=120)
    if any(keyword in normalized for keyword in ["上移", "向上", "往上"]):
        return MiradorAIPlan(action="pan_up", assistant_message="已向上平移画面。", pan_pixels=120)
    if any(keyword in normalized for keyword in ["下移", "向下", "往下"]):
        return MiradorAIPlan(action="pan_down", assistant_message="已向下平移画面。", pan_pixels=120)
    if any(keyword in normalized for keyword in ["重置", "恢复", "归位", "回到原位"]):
        return MiradorAIPlan(action="reset_view", assistant_message="已重置视图。")
    if any(keyword in normalized for keyword in ["适配", "适合屏幕", "填充窗口", "fit"]):
        return MiradorAIPlan(action="fit_to_window", assistant_message="已适配到窗口。")
    if any(keyword in normalized for keyword in ["关闭对比", "关闭比较", "退出对比", "退出比较", "单图", "返回单图"]):
        return MiradorAIPlan(
            action="switch_compare_mode",
            assistant_message="已准备切回单图模式，请确认后执行。",
            requires_confirmation=True,
            compare_mode="single",
        )
    if any(keyword in normalized for keyword in ["比较模式", "对比模式", "双窗", "并排", "打开对比模式"]):
        return MiradorAIPlan(
            action="switch_compare_mode",
            assistant_message="我会切换到比较模式，请确认后执行。",
            requires_confirmation=True,
            compare_mode="side_by_side",
        )
    if any(keyword in normalized for keyword in ["对比", "比较", "打开", "找图", "搜索", "类似", "相似"]):
        return MiradorAIPlan(
            action="open_compare",
            assistant_message="我先帮你找相关图像，找到后请确认是否打开对比。",
            requires_confirmation=True,
            search_query=prompt.strip(),
            compare_mode="side_by_side",
        )

    return MiradorAIPlan(action="noop", assistant_message="我暂时还不能确定你的意思，你可以换种说法。")


async def _call_openai_plan(payload: MiradorAIRequest) -> dict[str, object] | None:
    if not config.OPENAI_API_KEY:
        logger.info("ai.mirador.openai_skipped reason=no_api_key current_asset_id=%s", payload.current_asset_id)
        return None

    system_prompt = (
        "You translate user instructions for a Mirador IIIF viewer into a single JSON object. "
        "Return JSON only, no markdown, no prose. Allowed actions: zoom_in, zoom_out, pan_left, pan_right, "
        "pan_up, pan_down, reset_view, fit_to_window, search_assets, open_compare, switch_compare_mode, "
        "close_compare, noop. If the user wants to compare another image, use open_compare. If the user wants "
        "to switch the viewer between compare and single modes, use switch_compare_mode and set compare_mode to "
        "side_by_side or single. Keep assistant_message short and helpful."
    )
    user_prompt = {
        "prompt": payload.prompt,
        "current_asset_id": payload.current_asset_id,
        "current_title": payload.current_title,
        "current_object_number": payload.current_object_number,
        "current_manifest_url": payload.current_manifest_url,
        "current_resource_id": payload.current_resource_id,
    }

    request_body = {
        "model": config.OPENAI_MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
    }

    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        logger.info(
            "ai.mirador.openai_request prompt=%s model=%s current_asset_id=%s",
            _short_prompt(payload.prompt),
            config.OPENAI_MODEL,
            payload.current_asset_id,
        )
        async with httpx.AsyncClient(timeout=config.OPENAI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{config.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers=headers,
                json=request_body,
            )
            response.raise_for_status()
    except Exception as exc:
        logger.warning("ai.mirador.openai_failed prompt=%s error=%s", _short_prompt(payload.prompt), exc)
        return None

    data = response.json()
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = str(message.get("content") or "").strip()
    parsed = _extract_json_object(content)
    if not isinstance(parsed, dict):
        logger.warning("ai.mirador.openai_invalid_json prompt=%s", _short_prompt(payload.prompt))
        return None

    logger.info(
        "ai.mirador.openai_response action=%s requires_confirmation=%s search_query=%s",
        parsed.get("action"),
        parsed.get("requires_confirmation"),
        parsed.get("search_query"),
    )
    return parsed


def _coerce_action(raw_action: object) -> str:
    action = str(raw_action or "noop").strip()
    return action if action in ALLOWED_ACTIONS else "noop"


def _plan_from_payload(payload: dict[str, object]) -> MiradorAIPlan:
    action = _coerce_action(payload.get("action"))
    assistant_message = str(payload.get("assistant_message") or "已处理你的指令。")
    requires_confirmation = bool(payload.get("requires_confirmation", False))
    search_query = payload.get("search_query")
    compare_mode = payload.get("compare_mode")
    pan_pixels = payload.get("pan_pixels")
    zoom_factor = payload.get("zoom_factor")

    return MiradorAIPlan(
        action=action,  # type: ignore[arg-type]
        assistant_message=assistant_message,
        requires_confirmation=requires_confirmation,
        search_query=str(search_query).strip() if isinstance(search_query, str) and search_query.strip() else None,
        compare_mode=compare_mode if compare_mode in {"single", "side_by_side"} else None,  # type: ignore[arg-type]
        pan_pixels=int(pan_pixels) if isinstance(pan_pixels, (int, float)) else None,
        zoom_factor=float(zoom_factor) if isinstance(zoom_factor, (int, float)) else None,
    )


@router.post("/mirador/interpret", response_model=MiradorAIPlan)
async def interpret_mirador_command(
    payload: MiradorAIRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    user = ensure_current_user(user)
    logger.info(
        "ai.mirador.interpret_received user_id=%s current_asset_id=%s prompt=%s",
        getattr(user, "id", None),
        payload.current_asset_id,
        _short_prompt(payload.prompt),
    )

    parsed = await _call_openai_plan(payload)
    plan = _plan_from_payload(parsed) if parsed else _heuristic_plan(payload.prompt)
    logger.info(
        "ai.mirador.interpret_plan action=%s requires_confirmation=%s search_query=%s compare_mode=%s source=%s",
        plan.action,
        plan.requires_confirmation,
        plan.search_query,
        plan.compare_mode,
        "openai" if parsed else "heuristic",
    )

    if plan.search_query:
        plan.search_results = _search_assets(
            db,
            user,
            request,
            plan.search_query,
            limit=max(1, min(payload.max_candidates, 8)),
            current_asset_id=payload.current_asset_id,
        )
        logger.info(
            "ai.mirador.search_results query=%s count=%s current_asset_id=%s",
            plan.search_query,
            len(plan.search_results),
            payload.current_asset_id,
        )

    if plan.action == "open_compare":
        plan.requires_confirmation = True
        if plan.target_asset is None and plan.search_results:
            plan.target_asset = plan.search_results[0]
        if not plan.search_query:
            plan.search_query = payload.prompt.strip()
        if not plan.search_results and plan.search_query:
            plan.search_results = _search_assets(
                db,
                user,
                request,
                plan.search_query,
                limit=max(1, min(payload.max_candidates, 8)),
                current_asset_id=payload.current_asset_id,
            )
        if not plan.search_results:
            plan.action = "search_assets"
            plan.requires_confirmation = False
            plan.assistant_message = "我还没有找到足够明确的候选图像，你可以换个关键词再试一次。"
            logger.info(
                "ai.mirador.compare_fallback_to_search current_asset_id=%s prompt=%s",
                payload.current_asset_id,
                _short_prompt(payload.prompt),
            )
    elif plan.action == "switch_compare_mode":
        plan.requires_confirmation = True
        if plan.compare_mode not in {"single", "side_by_side"}:
            lowered = payload.prompt.strip().lower()
            if any(keyword in lowered for keyword in ["关闭", "退出", "单图", "返回"]):
                plan.compare_mode = "single"
            else:
                plan.compare_mode = "side_by_side"

    if plan.action == "search_assets" and not plan.assistant_message:
        plan.assistant_message = "我已经找到一些候选图像，你可以从中选择一张继续比较。"

    if plan.target_asset is None and plan.search_results:
        plan.target_asset = plan.search_results[0]
        logger.info(
            "ai.mirador.default_target_selected asset_id=%s title=%s",
            plan.target_asset.asset_id,
            plan.target_asset.title,
        )

    if not plan.search_results and plan.action in {"search_assets", "open_compare"}:
        plan.assistant_message = plan.assistant_message or "当前没有找到匹配的图像。"
        logger.info(
            "ai.mirador.no_results action=%s current_asset_id=%s prompt=%s",
            plan.action,
            payload.current_asset_id,
            _short_prompt(payload.prompt),
        )

    logger.info(
        "ai.mirador.interpret_finished action=%s requires_confirmation=%s search_count=%s target_asset_id=%s compare_mode=%s",
        plan.action,
        plan.requires_confirmation,
        len(plan.search_results),
        plan.target_asset.asset_id if plan.target_asset else None,
        plan.compare_mode,
    )
    return plan


@router.get("/assets/search", response_model=list[MiradorSearchResult])
def search_assets(
    q: str,
    request: Request,
    limit: int = 5,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    user = ensure_current_user(user)
    logger.info("ai.mirador.search_endpoint query=%s limit=%s", _short_prompt(q), limit)
    return _search_assets(db, user, request, q, limit=max(1, min(limit, 20)))
