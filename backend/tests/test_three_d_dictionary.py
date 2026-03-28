import pytest

from app.services.three_d_dictionary import build_three_d_metadata_dictionary


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_three_d_metadata_dictionary_exposes_core_and_domain_sections():
    dictionary = build_three_d_metadata_dictionary()

    assert dictionary.schema_version == "1.0"
    section_keys = [section.key for section in dictionary.sections]
    assert section_keys == ["core", "collection", "technical", "management", "preservation", "production"]

    core_fields = {field.key: field for field in dictionary.sections[0].fields}
    assert core_fields["title"].required is True
    assert core_fields["resource_group"].required is True
    assert core_fields["web_preview_status"].layer == "core"

    collection_fields = {field.key for field in dictionary.sections[1].fields}
    assert {"object_number", "object_name", "object_type", "collection_unit"}.issubset(collection_fields)

    preservation_fields = {field.key for field in dictionary.sections[4].fields}
    assert {"storage_tier", "preservation_status", "preservation_note"}.issubset(preservation_fields)

    production_fields = {field.key for field in dictionary.sections[5].fields}
    assert {"stage", "event_type", "status", "actor", "evidence"}.issubset(production_fields)
