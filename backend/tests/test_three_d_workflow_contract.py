import pytest

from app.services.three_d_workflow import (
    PUBLICATION_STATUSES,
    REPRESENTATION_TYPES,
    can_transition_publication_status,
    get_three_d_workflow_contract,
    validate_display_contract,
    validate_object_representation_invariants,
    validate_registration_contract,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def _representation(**overrides):
    record = {
        "title": "陶罐三维表现",
        "resource_group": "vase-001",
        "representation_type": "web_display",
        "version_label": "v1",
        "storage_tier": "delivery",
        "status": "ready",
        "is_current": True,
        "is_web_preview": True,
        "web_preview_status": "ready",
        "publication_status": "published",
    }
    record.update(overrides)
    return record


def _web_files(filename="vase.glb"):
    return [{"role": "model", "filename": filename, "actual_filename": filename}]


def _issue_codes(result):
    return {issue.code for issue in result.issues}


def test_workflow_contract_exposes_frozen_vocabularies():
    contract = get_three_d_workflow_contract()

    assert contract["representation_types"] == REPRESENTATION_TYPES
    assert contract["publication_statuses"] == PUBLICATION_STATUSES
    assert contract["web_model_extensions"] == ("glb", "gltf")


def test_minimum_registration_contract_accepts_explicit_representation():
    result = validate_registration_contract(_representation(publication_status="draft"))

    assert result.valid


@pytest.mark.parametrize("field", ["title", "resource_group", "representation_type", "version_label", "storage_tier"])
def test_minimum_registration_contract_rejects_missing_fields(field):
    result = validate_registration_contract(_representation(**{field: ""}))

    assert not result.valid
    assert any(issue.field == field for issue in result.issues)


def test_registration_contract_rejects_inferred_or_unknown_representation_type():
    missing = validate_registration_contract(_representation(representation_type=""))
    unknown = validate_registration_contract(_representation(representation_type="web-v2"))

    assert "required_field_missing" in _issue_codes(missing)
    assert "invalid_representation_type" in _issue_codes(unknown)


def test_minimum_display_contract_accepts_published_glb_and_gltf():
    assert validate_display_contract(_representation(), _web_files("vase.glb")).valid
    assert validate_display_contract(_representation(), _web_files("vase.gltf")).valid


def test_display_contract_rejects_non_web_model_and_incomplete_statuses():
    result = validate_display_contract(
        _representation(
            status="processing",
            is_web_preview=False,
            web_preview_status="pending",
            publication_status="approved",
        ),
        _web_files("vase.obj"),
    )

    assert {
        "resource_not_ready",
        "web_preview_not_enabled",
        "web_preview_not_ready",
        "representation_not_published",
        "web_model_missing",
    }.issubset(_issue_codes(result))


def test_original_master_cannot_be_published_or_exposed():
    record = _representation(representation_type="original_master")

    display_result = validate_display_contract(record, _web_files())
    object_result = validate_object_representation_invariants([record])

    assert "original_master_not_publishable" in _issue_codes(display_result)
    assert "original_master_exposed" in _issue_codes(object_result)


def test_object_allows_one_current_version_per_representation_type():
    result = validate_object_representation_invariants(
        [
            _representation(version_label="v1", is_web_preview=False, web_preview_status="disabled"),
            _representation(version_label="v2", is_web_preview=False, web_preview_status="disabled"),
        ]
    )

    assert "multiple_current_representations" in _issue_codes(result)


def test_object_allows_only_one_ready_default_web_representation():
    result = validate_object_representation_invariants(
        [
            _representation(version_label="v1", is_current=False),
            _representation(
                representation_type="mobile_lightweight",
                version_label="v1",
                is_current=False,
            ),
        ]
    )

    assert "multiple_default_web_representations" in _issue_codes(result)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "validating"),
        ("validating", "approved"),
        ("validating", "rejected"),
        ("approved", "published"),
        ("published", "withdrawn"),
        ("withdrawn", "draft"),
        ("rejected", "draft"),
    ],
)
def test_publication_state_machine_accepts_declared_transitions(current, target):
    assert can_transition_publication_status(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "published"),
        ("validating", "published"),
        ("published", "draft"),
        ("rejected", "published"),
        ("unknown", "draft"),
    ],
)
def test_publication_state_machine_rejects_shortcuts(current, target):
    assert not can_transition_publication_status(current, target)
