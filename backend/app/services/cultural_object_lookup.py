from __future__ import annotations

import hashlib

from ..schemas import (
    CulturalObjectLookupRecord,
    CulturalObjectLookupResponse,
    CulturalObjectSampleListResponse,
)

TEMPORARY_OBJECT_NUMBER_TOKENS = {
    "暂无号",
    "暫無號",
    "无号",
    "無號",
    "none",
    "n/a",
    "na",
    "temp-none",
}

OBJECT_LEVELS = ["一级", "二级", "三级", "一般"]
OBJECT_CATEGORIES = [
    ("陶瓷", "青花瓷", "陶瓷组"),
    ("书画", "绘画", "书画组"),
    ("金属器", "铜器", "工艺组"),
    ("玉石器", "玉器", "工艺组"),
    ("织绣", "织物", "织绣组"),
]

OBJECT_NAME_TEMPLATES = {
    "陶瓷": [
        "青花缠枝莲纹瓶",
        "粉彩花卉纹盘",
        "斗彩云龙纹罐",
        "白釉暗花梅瓶",
        "霁蓝釉描金尊",
    ],
    "书画": [
        "山水图轴",
        "花鸟图册页",
        "行书诗卷",
        "人物故事图轴",
        "墨竹图页",
    ],
    "金属器": [
        "铜鎏金香炉",
        "错银云纹壶",
        "鎏金瑞兽摆件",
        "铜镜",
        "金属花觚",
    ],
    "玉石器": [
        "白玉龙纹佩",
        "青玉如意",
        "碧玉炉顶",
        "玉璧",
        "玛瑙杯",
    ],
    "织绣": [
        "缂丝团花纹轴",
        "刺绣龙袍片",
        "云锦纹样残片",
        "织金锦料",
        "宫廷绣品",
    ],
}


def _build_predefined_mock_objects() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {
        "故00154701": {
            "object_name": "乾隆款粉彩九桃天球瓶",
            "object_level": "一级",
            "object_category": "陶瓷",
            "object_subcategory": "粉彩瓷",
            "management_group": "陶瓷组",
        }
    }

    for index in range(1, 100):
        object_number = f"故{index:08d}"
        category, subcategory, group = OBJECT_CATEGORIES[(index - 1) % len(OBJECT_CATEGORIES)]
        level = OBJECT_LEVELS[(index - 1) % len(OBJECT_LEVELS)]
        templates = OBJECT_NAME_TEMPLATES[category]
        name_seed = templates[(index - 1) % len(templates)]
        records[object_number] = {
            "object_name": f"测试{name_seed}{index:03d}",
            "object_level": level,
            "object_category": category,
            "object_subcategory": subcategory,
            "management_group": group,
        }

    return records


MOCK_CULTURAL_OBJECTS = _build_predefined_mock_objects()


def _normalize_object_number(value: str) -> str:
    normalized = "".join(str(value or "").split()).strip()
    return normalized


def _is_temporary_object_number(value: str) -> bool:
    return value.lower() in TEMPORARY_OBJECT_NUMBER_TOKENS


def _build_generated_record(object_number: str) -> CulturalObjectLookupRecord:
    digest = hashlib.sha1(object_number.encode("utf-8")).digest()
    category, subcategory, group = OBJECT_CATEGORIES[digest[0] % len(OBJECT_CATEGORIES)]
    level = OBJECT_LEVELS[digest[1] % len(OBJECT_LEVELS)]
    suffix = object_number[-6:] if len(object_number) >= 6 else object_number
    return CulturalObjectLookupRecord(
        object_number=object_number,
        object_name=f"模拟文物{suffix}",
        object_level=level,
        object_category=category,
        object_subcategory=subcategory,
        management_group=group,
        source="mock_generated",
        source_label="模拟文物接口",
        is_temporary_number=False,
    )


def lookup_cultural_object_by_number(object_number: str) -> CulturalObjectLookupResponse:
    normalized = _normalize_object_number(object_number)
    if not normalized:
        raise ValueError("Object number is required")

    if _is_temporary_object_number(normalized):
        return CulturalObjectLookupResponse(
            query=object_number,
            normalized_object_number=None,
            found=False,
            lookup_status="temporary_none",
            message="当前记录使用“暂无号”，允许继续录入、上传和入库。",
            record=None,
        )

    if normalized.upper().startswith("404") or normalized.lower() == "not-found":
        return CulturalObjectLookupResponse(
            query=object_number,
            normalized_object_number=normalized,
            found=False,
            lookup_status="not_found",
            message="模拟接口未找到对应文物信息。",
            record=None,
        )

    predefined = MOCK_CULTURAL_OBJECTS.get(normalized)
    if predefined is not None:
        return CulturalObjectLookupResponse(
            query=object_number,
            normalized_object_number=normalized,
            found=True,
            lookup_status="matched",
            message="已命中预置模拟文物数据。",
            record=CulturalObjectLookupRecord(
                object_number=normalized,
                object_name=predefined["object_name"],
                object_level=predefined["object_level"],
                object_category=predefined["object_category"],
                object_subcategory=predefined["object_subcategory"],
                management_group=predefined["management_group"],
                source="mock_predefined",
                source_label="模拟文物接口",
                is_temporary_number=False,
            ),
        )

    return CulturalObjectLookupResponse(
        query=object_number,
        normalized_object_number=normalized,
        found=True,
        lookup_status="matched",
        message="未命中预置样本，已返回按文物号生成的模拟数据。",
        record=_build_generated_record(normalized),
    )


def list_cultural_object_samples(*, q: str | None = None, limit: int = 100) -> CulturalObjectSampleListResponse:
    normalized_q = "".join(str(q or "").split()).strip().lower()
    items: list[CulturalObjectLookupRecord] = []
    for object_number, payload in sorted(MOCK_CULTURAL_OBJECTS.items()):
        record = CulturalObjectLookupRecord(
            object_number=object_number,
            object_name=payload["object_name"],
            object_level=payload["object_level"],
            object_category=payload["object_category"],
            object_subcategory=payload["object_subcategory"],
            management_group=payload["management_group"],
            source="mock_predefined",
            source_label="模拟文物接口",
            is_temporary_number=False,
        )
        if normalized_q:
            haystack = " ".join(
                filter(
                    None,
                    [
                        record.object_number,
                        record.object_name,
                        record.object_category,
                        record.object_subcategory,
                    ],
                )
            ).lower()
            if normalized_q not in haystack:
                continue
        items.append(record)

    return CulturalObjectSampleListResponse(total=len(items), items=items[: max(1, min(limit, 100))])
