# Reference Resource Import Mapping

## Goal

This document defines how files and sidecar metadata under `reference/资源包` should be transformed into the current MDAMS 2D ingest shape.

The target is not to import the reference package as a zip-like bundle. The target is:

- select one primary 2D image per resource folder
- generate one SIP-ready manifest per selected image
- preserve the original sidecar JSON files in `raw_metadata`
- normalize external profile names into the internal MDAMS profile model

## Source Package Shape

Each reference resource folder usually contains:

- one primary image file such as `.jpg`, `.jpeg`, or `.tif`
- one or more `FireShot Capture *.jpg` screenshots
- one `*.json` source sidecar
- one `*.unified.json` normalized sidecar

Only the primary image should be imported as the MDAMS asset file.

## Primary File Selection

Selection rule:

1. choose image files only: `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.png`, `.psb`
2. exclude `FireShot Capture *` if a non-screenshot image exists
3. prefer `.tif` or `.tiff` over screenshot JPEGs when both exist
4. if the folder contains only screenshots, fall back to the screenshot and emit a warning

## Profile Mapping

External reference package values do not fully match the current internal profile keys.

| Reference package value | Internal MDAMS profile key |
| --- | --- |
| `activity` | `business_activity` |
| `tree` | `ancient_tree` |
| `building` | `immovable_artifact` |
| `cultural_object` | `movable_artifact` |
| `archaeology` | `archaeology` |
| `other` | `other` |

Folder category fallback:

| Folder category | Internal MDAMS profile key |
| --- | --- |
| `业务活动影像` | `business_activity` |
| `古树影像` | `ancient_tree` |
| `文物建筑影像` | `immovable_artifact` |
| `文物影像` | `movable_artifact` |
| `考古影像` | `archaeology` |
| `其他影像` | `other` |

## Metadata Mapping

The generated manifest writes layered metadata so it can flow through the current ingest pipeline cleanly.

### `core`

| Manifest field | Source |
| --- | --- |
| `source_system` | fixed: `reference_resource_pack` |
| `source_label` | fixed: `Reference Resource Pack` |
| `resource_type` | fixed: `image_2d_cultural_object` |
| `title` | `unified.title`, then `metadata_layers.core.title`, then folder name |
| `status` | fixed: `ready` |
| `visibility_scope` | CLI parameter, default `open` |

### `management`

| Manifest field | Source |
| --- | --- |
| `project_type` | `unified.source_label` or category folder |
| `project_name` | resource folder name |
| `photographer` | first `unified.creators[]` or `metadata_layers.core.creator` |
| `photographer_org` | `metadata_layers.core.creator_org` |
| `copyright_owner` | `unified.rights` or `metadata_layers.core.rights` |
| `capture_time` | `metadata_layers.core.capture_date` or `unified.updated_at` |
| `image_category` | `unified.source_label` or category folder |
| `image_name` | `unified.title` |
| `capture_content` | `metadata_layers.core.content` or `unified.summary` |
| `remark` | `unified.summary` |
| `tags` | `unified.keywords` |
| `record_account` | `metadata_layers.core.recorded_by` |
| `record_time` | `metadata_layers.core.recorded_at` or `unified.updated_at` |

### `technical`

| Manifest field | Source |
| --- | --- |
| `original_file_name` | selected primary image filename |
| `image_file_name` | selected primary image filename |
| `identifier_type` | fixed: `reference_source_id` |
| `identifier_value` | `unified.source_id` |
| `file_size` | filesystem stat of the selected primary image |
| `checksum_algorithm` | fixed: `SHA256` |
| `checksum` | computed from the selected primary image |
| `fixity_sha256` | same as `checksum` |
| `ingest_method` | fixed: `reference_manifest` |
| `original_file_path` | absolute path of the selected primary image |
| `original_mime_type` | guessed from file extension |
| `source_json_file` | raw sidecar JSON filename when present |
| `source_unified_json_file` | unified sidecar filename when present |

### `profile`

The generated manifest always writes a normalized internal `profile.key`.

Profile-specific fields are intentionally conservative:

- `movable_artifact.object_name` uses the normalized title
- `immovable_artifact.building_name` uses the resource folder name
- `ancient_tree.archive_number` uses the resource folder name
- `archaeology.archaeology_image_category` uses the source label

If the source package does not provide a stable value, the generator leaves the field blank instead of guessing.

### `raw_metadata`

The generator preserves:

- the full `*.unified.json` payload
- the full source `*.json` payload
- extracted `metadata_layers.modality`
- extracted `metadata_layers.source_record`
- the relative folder path
- the selected primary image path

## Known Limits

- Some source sidecars already contain mojibake or upstream encoding problems. Those values are preserved, not repaired automatically.
- The current manifest generator prepares files for ingest. It does not call the ingest API by itself.
- `access_level` in the reference package is not one-to-one with the current MDAMS `visibility_scope` model, so the manifest generator uses a CLI parameter instead.

## Generated Outputs

`backend/scripts/generate_reference_manifests.py` writes:

- one `*.manifest.json` per resource folder
- one `import-plan.json` summary file
- optionally, a staged copy of the selected primary image beside each manifest
