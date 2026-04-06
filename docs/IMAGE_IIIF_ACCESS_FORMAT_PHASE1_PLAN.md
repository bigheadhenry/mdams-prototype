# IMAGE_IIIF_ACCESS_FORMAT_PHASE1_PLAN

## Purpose

This document archives the agreed conclusions for Problem 4: the IIIF access-format strategy for large image formats such as PSB and large TIFF, with Mirador as the presentation client.

It is intended to complement:

- `IMAGE_RECORD_ROLE_SPLIT_PHASE1_PLAN.md`
- `IMAGE_RECORD_MATCHING_PHASE1_PLAN.md`
- `IMAGE_RECORD_VALIDATION_PHASE1_PLAN.md`

## Problem Statement

The system currently has a partial large-image conversion path, but it does not yet define a stable layered strategy for:

- original preservation files
- IIIF access derivatives
- Mirador-compatible delivery
- explicit metadata separation between original and access copies

The target is to establish a clear and stable format policy for online IIIF/Mirador access.

## Final Agreed Conclusions

### 1. Original and Access Files Must Be Separated

Original files and IIIF access files must be treated as separate layers.

- original files are retained for preservation and traceability
- access files are generated for online IIIF/Mirador delivery

### 2. Mirador Must Read IIIF Access Files, Not Originals

Mirador should only consume the IIIF presentation and image-service layer.

It should not directly depend on original source formats such as:

- `psb`
- very large `tif/tiff`

### 3. Recommended Access Format for PSB and Large TIFF

The recommended IIIF access derivative is:

- `BigTIFF + tiled + pyramid + deflate`

### 4. Required Metadata Separation

At minimum, technical metadata must explicitly record:

- `original_file_path`
- `iiif_access_file_path`
- `iiif_access_mime_type`

Recommended additional fields include:

- `original_file_name`
- `original_file_size`
- `original_mime_type`
- `iiif_access_file_name`
- `preview_image_path`
- `preview_image_name`
- `preview_image_mime_type`
- `conversion_method`
- `derivative_rule_id`
- `derivative_strategy`

### 5. Conversion Strategy

The processing chain should generate an access derivative instead of merely overwriting the source-file meaning.

The preferred architecture is:

- preserve original
- generate access derivative
- direct IIIF service to read the access derivative

## Detailed Explanation of the Recommended Access Format

### BigTIFF

`BigTIFF` extends standard TIFF to support very large files and large internal offsets.

Purpose:

- supports files larger than standard TIFF limits
- accommodates large tiled pyramidal images
- suitable for very large PSB- or TIFF-derived assets

### tiled

`tiled` means the TIFF is stored in small blocks rather than as long scanlines.

Purpose:

- enables partial region reads
- improves IIIF tile response performance
- avoids reading the whole image for a small viewport

### pyramid

`pyramid` means multiple resolution layers are stored in the same image structure.

Purpose:

- speeds up open, zoom, and pan behavior
- gives IIIF services native access to lower-resolution levels
- improves large-image interaction performance

### deflate

`deflate` is a lossless compression strategy.

Purpose:

- reduces file size without losing pixels
- is generally stable and compatible for large-image workflows
- is preferred over more fragile JPEG-in-TIFF paths for this project baseline

## Format Strategy Table

| Source Format | Keep Original | Generate IIIF Access Copy | Access Format | Mirador Reads Original | Notes |
| --- | --- | --- | --- | --- | --- |
| `psb` | yes | yes | `BigTIFF + tiled + pyramid + deflate` | no | preservation only for original |
| large `tif/tiff` | yes | yes | `BigTIFF + tiled + pyramid + deflate` | no | standard IIIF access path |
| small `tif/tiff` | yes | optional | original or access derivative | preferably no | phase 1 may still favor uniform access-copy logic |
| normal `jpg/jpeg` | yes | optional | original or light access copy | not recommended | may remain direct source if deployment permits |
| very large `jpg/jpeg` | yes | optional | pyramidal TIFF or lighter access derivative | no | depends on performance goals |
| `png/webp/gif` | yes | optional | TIFF or JPEG access copy | no | based on preview and zoom requirements |
| `jp2` | yes | deployment-dependent | original or TIFF derivative | not recommended by default | depends on server support |

## Conversion Rules

### Mandatory Conversion

Conversion to IIIF access derivative is mandatory when:

- source format is `psb`
- source format is `tif/tiff` and exceeds size or pixel thresholds
- original format cannot stably support IIIF image delivery

### Suggested Thresholds

Recommended baseline thresholds:

- TIFF file size `>= 50 MB`
- or pixel count `>= 25,000,000`
- JPEG may use a higher threshold such as:
  - file size `>= 120 MB`
  - or pixel count `>= 60,000,000`

### Recommended Derivative Generation Settings

For access-copy generation:

- output format: `BigTIFF`
- compression: `deflate`
- tile enabled: `true`
- tile size: `256 x 256`
- pyramid enabled: `true`
- BigTIFF enabled: `true`

### Derivative Output Requirements

Generated access derivatives should:

- preserve original dimensions
- record conversion method
- record derivative path and MIME type
- become the preferred IIIF image-service source

## Storage Structure

### Recommended Layered Storage Model

Two storage layers are recommended:

- `originals`
- `derivatives/iiif-access`

### Recommended Directory Layout

```text
uploads/
  originals/
    asset-123/
      master.psb
  derivatives/
    asset-123/
      iiif-access.pyramidal.tiff
      preview.jpg
```

### Recommended Metadata Ownership

Recommended meaning:

- original paths and metadata describe preservation source
- access-copy paths describe online IIIF source
- preview paths describe lightweight preview layer

### Recommended `asset.file_path` Strategy

Phase 1 should avoid ambiguous semantics for `asset.file_path`.

Preferred long-term strategy:

- `asset.file_path` represents the original preserved file
- `iiif_access_file_path` represents the IIIF delivery source

At minimum, IIIF routing must prefer `iiif_access_file_path`.

## IIIF Routing Rule

The IIIF service path should resolve in this order:

1. `iiif_access_file_path`
2. fallback only if explicitly allowed by policy

Mirador should only access the manifest and IIIF image service, never source files directly.

## Recommended State Flow

### Suggested States

- `ingest_received`
- `original_stored`
- `derivative_pending`
- `derivative_processing`
- `iiif_ready`
- `validation_failed`
- `error`

### Standard Flow

1. upload received
2. original stored
3. derivative policy decides whether access copy is needed
4. if needed, enter derivative queue
5. derivative generation runs
6. on success, become `iiif_ready`
7. on failure, become `error`

### Typical PSB Flow

```text
upload PSB
-> ingest_received
-> original_stored
-> derivative_pending
-> derivative_processing
-> iiif_ready
```

### Replacement Flow

When an image is replaced:

```text
replace new file
-> ingest_received
-> original_stored
-> derivative_pending / derivative_processing
-> iiif_ready
```

Previous derivative-ready status must not be inherited blindly.

## Phase 1 Recommended Scope

Phase 1 should implement:

- mandatory PSB conversion to `BigTIFF + tiled + pyramid + deflate`
- threshold-driven conversion for large TIFF
- explicit metadata separation between original and IIIF access files
- IIIF routing preferring `iiif_access_file_path`
- Mirador reading only the IIIF manifest path
- replacement triggering reprocessing and revalidation

Phase 1 should not yet attempt:

- universal conversion for every source format
- multiple derivative variants per asset
- complex cold/hot storage tiering
- automatic cleanup of all historical derivative versions

## Acceptance Criteria

This access-format phase is complete when:

1. PSB originals are preserved and not used directly for Mirador delivery
2. PSB access copies are generated as `BigTIFF + tiled + pyramid + deflate`
3. large TIFF can be converted into the same access-derivative format
4. technical metadata distinguishes original and IIIF access paths
5. IIIF routing prefers access-copy paths
6. Mirador works only through manifest and IIIF image-service endpoints
7. replacement of an image triggers derivative regeneration logic when required

## Out-of-Scope Reminder

The following are intentionally deferred:

- full normalization of all raster formats
- multi-variant access derivative management
- advanced storage lifecycle automation
- historical derivative cleanup policy
