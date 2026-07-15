from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence


REPRESENTATION_TYPES: Final[tuple[str, ...]] = (
    "original_master",
    "web_display",
    "mobile_lightweight",
    "research_detail",
    "derivative",
)

PUBLICATION_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "validating",
    "approved",
    "published",
    "withdrawn",
    "rejected",
)

PUBLICATION_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    "draft": frozenset({"validating"}),
    "validating": frozenset({"approved", "rejected"}),
    "approved": frozenset({"published", "draft"}),
    "published": frozenset({"withdrawn"}),
    "withdrawn": frozenset({"draft"}),
    "rejected": frozenset({"draft"}),
}

DISPLAY_REPRESENTATION_TYPES: Final[frozenset[str]] = frozenset(
    {"web_display", "mobile_lightweight", "research_detail", "derivative"}
)
WEB_MODEL_EXTENSIONS: Final[frozenset[str]] = frozenset({"glb", "gltf"})


@dataclass(frozen=True)
class ThreeDContractIssue:
    code: str
    field: str
    message: str


@dataclass(frozen=True)
class ThreeDContractResult:
    issues: tuple[ThreeDContractIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _value(record: Mapping[str, Any], key: str) -> Any:
    if key in record and record[key] not in (None, ""):
        return record[key]
    for section_name in ("core", "management", "collection", "preservation", "raw_metadata"):
        section = _mapping(record.get(section_name))
        if key in section and section[key] not in (None, ""):
            return section[key]
    return None


def _text(record: Mapping[str, Any], key: str) -> str:
    value = _value(record, key)
    return str(value).strip() if value is not None else ""


def _bool(record: Mapping[str, Any], key: str) -> bool:
    value = _value(record, key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _issue(code: str, field: str, message: str) -> ThreeDContractIssue:
    return ThreeDContractIssue(code=code, field=field, message=message)


def validate_registration_contract(record: Mapping[str, Any]) -> ThreeDContractResult:
    """Validate the minimum contract for a representation entering management."""

    issues: list[ThreeDContractIssue] = []
    for field, message in (
        ("title", "三维表现必须有可识别标题。"),
        ("resource_group", "三维表现必须归属一个数字对象分组。"),
        ("version_label", "三维表现必须声明版本标签。"),
        ("storage_tier", "三维表现必须声明存储层级。"),
    ):
        if not _text(record, field):
            issues.append(_issue("required_field_missing", field, message))

    representation_type = _text(record, "representation_type")
    if not representation_type:
        issues.append(
            _issue(
                "required_field_missing",
                "representation_type",
                "三维表现必须显式声明表现类型，不能再由版本标签推断。",
            )
        )
    elif representation_type not in REPRESENTATION_TYPES:
        issues.append(
            _issue(
                "invalid_representation_type",
                "representation_type",
                f"不支持的表现类型：{representation_type}。",
            )
        )

    publication_status = _text(record, "publication_status") or "draft"
    if publication_status not in PUBLICATION_STATUSES:
        issues.append(
            _issue(
                "invalid_publication_status",
                "publication_status",
                f"不支持的发布状态：{publication_status}。",
            )
        )

    return ThreeDContractResult(tuple(issues))


def _has_web_model(files: Sequence[Mapping[str, Any]]) -> bool:
    for file_record in files:
        if _text(file_record, "role").lower() != "model":
            continue
        filename = _text(file_record, "actual_filename") or _text(file_record, "filename")
        extension = Path(filename).suffix.lower().lstrip(".")
        if extension in WEB_MODEL_EXTENSIONS:
            return True
    return False


def validate_display_contract(
    record: Mapping[str, Any],
    files: Sequence[Mapping[str, Any]],
) -> ThreeDContractResult:
    """Validate the minimum contract for a representation exposed in the Web viewer."""

    issues = list(validate_registration_contract(record).issues)
    representation_type = _text(record, "representation_type")

    if representation_type == "original_master":
        issues.append(
            _issue(
                "original_master_not_publishable",
                "representation_type",
                "原始保存级表现不能直接作为 Web 展示表现。",
            )
        )
    elif representation_type and representation_type not in DISPLAY_REPRESENTATION_TYPES:
        issues.append(
            _issue(
                "representation_not_displayable",
                "representation_type",
                "该表现类型不允许进入 Web 展示。",
            )
        )

    if _text(record, "status") != "ready":
        issues.append(_issue("resource_not_ready", "status", "资源处理状态必须为 ready。"))
    if not _bool(record, "is_web_preview"):
        issues.append(_issue("web_preview_not_enabled", "is_web_preview", "必须显式允许 Web 展示。"))
    if _text(record, "web_preview_status") != "ready":
        issues.append(
            _issue("web_preview_not_ready", "web_preview_status", "Web 展示状态必须为 ready。")
        )
    if _text(record, "publication_status") != "published":
        issues.append(
            _issue("representation_not_published", "publication_status", "表现必须完成审批并发布。")
        )
    if not _has_web_model(files):
        issues.append(
            _issue(
                "web_model_missing",
                "files",
                "Web 展示表现必须包含角色为 model 的 GLB 或 glTF 文件。",
            )
        )

    return ThreeDContractResult(tuple(issues))


def validate_object_representation_invariants(
    representations: Sequence[Mapping[str, Any]],
) -> ThreeDContractResult:
    """Validate invariants shared by all representations of one digital object."""

    issues: list[ThreeDContractIssue] = []
    current_by_type: dict[str, int] = {}
    default_web_count = 0

    for record in representations:
        representation_type = _text(record, "representation_type")
        if _bool(record, "is_current") and representation_type:
            current_by_type[representation_type] = current_by_type.get(representation_type, 0) + 1
        if _bool(record, "is_web_preview") and _text(record, "web_preview_status") == "ready":
            default_web_count += 1
        if representation_type == "original_master" and (
            _bool(record, "is_web_preview") or _text(record, "publication_status") == "published"
        ):
            issues.append(
                _issue(
                    "original_master_exposed",
                    "representation_type",
                    "原始保存级表现不能发布或设为默认 Web 表现。",
                )
            )

    for representation_type, count in current_by_type.items():
        if count > 1:
            issues.append(
                _issue(
                    "multiple_current_representations",
                    "is_current",
                    f"表现类型 {representation_type} 同时存在 {count} 个 current 版本。",
                )
            )
    if default_web_count > 1:
        issues.append(
            _issue(
                "multiple_default_web_representations",
                "is_web_preview",
                "同一三维数字对象只能有一个就绪的默认 Web 表现。",
            )
        )

    return ThreeDContractResult(tuple(issues))


def can_transition_publication_status(current: str, target: str) -> bool:
    current_status = current.strip().lower()
    target_status = target.strip().lower()
    if current_status not in PUBLICATION_STATUSES or target_status not in PUBLICATION_STATUSES:
        return False
    if current_status == target_status:
        return True
    return target_status in PUBLICATION_TRANSITIONS[current_status]


def get_three_d_workflow_contract() -> dict[str, Any]:
    return {
        "representation_types": REPRESENTATION_TYPES,
        "publication_statuses": PUBLICATION_STATUSES,
        "publication_transitions": {
            key: tuple(sorted(value)) for key, value in PUBLICATION_TRANSITIONS.items()
        },
        "display_representation_types": tuple(sorted(DISPLAY_REPRESENTATION_TYPES)),
        "web_model_extensions": tuple(sorted(WEB_MODEL_EXTENSIONS)),
    }
