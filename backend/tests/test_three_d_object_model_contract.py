import ast
from pathlib import Path

import pytest

from app.models import ThreeDAsset, ThreeDDigitalObject
from app.routers.three_d import router
from app.schemas import ThreeDAssetOut, ThreeDDetailResponse, ThreeDDigitalObjectOut
from app.services.three_d_objects import (
    build_digital_object_key,
    infer_representation_type,
    normalize_publication_status,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_digital_object_owns_representations_through_required_foreign_key():
    asset_table = ThreeDAsset.__table__
    object_table = ThreeDDigitalObject.__table__

    assert object_table.name == "three_d_digital_objects"
    assert object_table.c.object_key.unique is True
    assert asset_table.c.three_d_object_id.nullable is False
    assert {foreign_key.target_fullname for foreign_key in asset_table.c.three_d_object_id.foreign_keys} == {
        "three_d_digital_objects.id"
    }
    assert ThreeDDigitalObject.representations.property.mapper.class_ is ThreeDAsset


def test_representation_and_publication_vocabularies_are_database_constrained():
    constraint_sql = {
        str(constraint.sqltext)
        for constraint in ThreeDAsset.__table__.constraints
        if getattr(constraint, "sqltext", None) is not None
    }

    assert any("original_master" in sql and "web_display" in sql for sql in constraint_sql)
    assert any("draft" in sql and "published" in sql and "withdrawn" in sql for sql in constraint_sql)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"explicit": "web_display", "version_label": "original"}, "web_display"),
        ({"metadata": {"core": {"representation_type": "research_detail"}}}, "research_detail"),
        ({"version_label": "original-v1"}, "original_master"),
        ({"version_label": "mobile-light"}, "mobile_lightweight"),
        ({"version_label": "web-v2"}, "web_display"),
        ({"version_label": "edited-v1"}, "derivative"),
    ],
)
def test_representation_type_inference_is_deterministic(kwargs, expected):
    assert infer_representation_type(**kwargs) == expected


def test_publication_status_defaults_preserve_legacy_preview_behavior():
    assert normalize_publication_status(None) == "draft"
    assert normalize_publication_status(None, preview_ready=True) == "published"
    assert normalize_publication_status("approved", preview_ready=True) == "approved"


def test_object_key_keeps_collection_scope_and_legacy_group():
    assert build_digital_object_key(42, "vase-001") == "collection:42:group:vase-001"
    assert build_digital_object_key(None, "scan-batch") == "collection:none:group:scan-batch"


def test_api_contract_exposes_object_and_representation_fields():
    assert {"three_d_object_id", "representation_type", "publication_status"}.issubset(
        ThreeDAssetOut.model_fields
    )
    assert {"three_d_object_id", "representation_type", "publication_status"}.issubset(
        ThreeDDetailResponse.model_fields
    )
    assert {"object_key", "representation_count", "lifecycle_status"}.issubset(
        ThreeDDigitalObjectOut.model_fields
    )
    assert any(route.path == "/three-d/digital-objects" for route in router.routes)


def test_migration_extends_the_current_alembic_head():
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "a1b2c3d4e5f6_add_three_d_digital_objects.py"
    )
    tree = ast.parse(migration_path.read_text(encoding="utf-8"))
    assignments = {
        node.target.id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id in {"revision", "down_revision"}
    }
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}

    assert assignments == {
        "revision": "a1b2c3d4e5f6",
        "down_revision": "f5a6b7c8d9e0",
    }
    assert {"upgrade", "downgrade"}.issubset(functions)
