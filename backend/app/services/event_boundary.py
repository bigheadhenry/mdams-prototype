from __future__ import annotations

from typing import Final

# Shared minimal verbs for cross-system event discussion.
# These are intentionally small and research-facing rather than a full PREMIS model.
SHARED_EVENT_VERBS: Final[tuple[str, ...]] = (
    "register",
    "ingest",
    "validate",
    "extract",
    "convert",
    "bind",
    "publish",
    "export",
    "review",
    "preserve",
)

# Current implementation anchors used by the prototype today.
ASSET_LIFECYCLE_STEPS: Final[tuple[str, ...]] = (
    "object_created",
    "ingest_completed",
    "fixity_recorded",
    "metadata_extracted",
    "iiif_access_ready",
    "access_derivative_generated",
    "preview_ready",
    "output_ready",
)

THREE_D_PRODUCTION_EVENT_TYPES: Final[tuple[str, ...]] = (
    "register",
    "files_saved",
    "manifest_built",
    "web_preview",
    "storage_tier",
)

COLLABORATION_EVENT_STEPS: Final[tuple[str, ...]] = (
    "image_record_submit",
    "image_record_return",
    "image_record_bind_confirm",
    "image_record_replace_confirm",
)

APPLICATION_EVENT_STEPS: Final[tuple[str, ...]] = (
    "application_submit",
    "application_review",
    "delivery_export",
)

OUTPUT_EVENT_STEPS: Final[tuple[str, ...]] = (
    "manifest_generate",
    "iiif_access_generate",
    "export_generate",
)


def get_minimal_event_boundary() -> dict[str, tuple[str, ...]]:
    return {
        "shared_event_verbs": SHARED_EVENT_VERBS,
        "asset_lifecycle_steps": ASSET_LIFECYCLE_STEPS,
        "three_d_production_event_types": THREE_D_PRODUCTION_EVENT_TYPES,
        "collaboration_event_steps": COLLABORATION_EVENT_STEPS,
        "application_event_steps": APPLICATION_EVENT_STEPS,
        "output_event_steps": OUTPUT_EVENT_STEPS,
    }
