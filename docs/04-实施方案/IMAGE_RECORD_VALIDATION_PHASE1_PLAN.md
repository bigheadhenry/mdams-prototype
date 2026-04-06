# IMAGE_RECORD_VALIDATION_PHASE1_PLAN

## Purpose

This document archives the agreed conclusions for Problem 3: validation design for the split workflow between metadata entry staff and photographers.

It is intended to pair with:

- `IMAGE_RECORD_ROLE_SPLIT_PHASE1_PLAN.md`
- `IMAGE_RECORD_MATCHING_PHASE1_PLAN.md`

## Problem Statement

The current system mainly validates technical ingest details, but lacks a structured validation model aligned with the new workflow.

Validation now needs to support:

- metadata-entry submission quality
- file binding and replacement quality
- risk-based operator confirmation
- state-aware revalidation after replacement

## Final Agreed Conclusions

### 1. Two-stage Validation

Validation is split into two stages:

1. record submission validation
2. post-bind or post-replace validation

### 2. Three-level Validation Outcome

Validation results are classified into:

- blocking error
- strong warning requiring confirmation
- informational hint

### 3. Replacement Revalidation

When an image is replaced:

- previous successful validation must be invalidated
- validation must be rerun
- record status must return to `uploaded_pending_validation`

## Stage A: Record Submission Validation

This validation runs when a metadata entry user submits an `ImageRecord` from:

- `draft`
- `returned`

to:

- `ready_for_upload`

### A1. Blocking Errors

The following must block submission:

- `record_no` missing
- `record_no` not unique
- `title` missing
- `visibility_scope` missing or invalid
- `profile_key` missing or invalid
- `project_name` missing
- `image_category` missing
- `assigned_photographer_user_id` missing
- current status does not allow submission
- profile minimum required field missing:
  - `business_activity.main_location`
  - `movable_artifact.object_name`
  - `immovable_artifact.building_name`
  - `ancient_tree.archive_number`

### A2. Strong Warnings

The following do not block submission but should require explicit operator confirmation when shown:

- `object_number` missing
- `capture_time` missing
- `photographer` missing
- `copyright_owner` missing
- title appears too short or placeholder-like

### A3. Informational Hints

The following may be shown as hints only:

- tags missing
- `record_account` missing
- `image_record_time` missing
- optional enrichment fields not yet generated

## Stage B: Post-bind or Post-replace Validation

This validation runs after a photographer uploads a file and explicitly confirms:

- bind
- replace

### B1. Blocking Errors

The following must block binding or replacement:

- selected record does not exist
- current user is not the assigned photographer
- current record status does not allow upload
- uploaded file is empty
- upload is incomplete
- hash generation failed
- hash/fixity validation failed
- file is unreadable
- dimensions cannot be extracted
- file type is not allowed
- a second active binding is being attempted instead of replacement
- replacement context is inconsistent with current record state
- uploaded file hash already exists in the system as another effective image object
- replacement file hash is identical to the current effective bound image

### B2. Strong Warnings

The following should not block, but should require explicit confirmation:

- file name does not contain `record_no`
- file name does not contain `object_number`
- TIFF contains layer or multi-page risk
- PSD/PSB contains layer risk
- file is unusually large and processing may be slow
- PSB requires background conversion before preview

### B3. Informational Hints

The following may be shown as hints only:

- file naming does not follow recommended naming convention
- generation of IIIF access derivative is recommended
- extension normalization is recommended

## Duplicate Hash Policy

The agreed rule is:

- duplicate file hash is a blocking error

Recommended interpretation:

1. if the same hash is already used by another effective image object, block
2. if replacement uploads the exact same file content as the current active image, also block

This prevents duplicate active occupancy of the same image content.

## File Name Consistency Policy

The agreed rule is:

- file name not containing `record_no` or `object_number` is a strong warning, not a blocker

This means operators can still proceed after confirmation, but the system should clearly surface the mismatch.

## Validation Result Model

Recommended validation result structure:

- `validation_status`
- `validation_summary`
- `validation_report`

Recommended status values:

- `not_run`
- `passed`
- `warning`
- `failed`

Recommended rule-entry fields:

- `code`
- `level`
- `field`
- `message`
- `blocking`
- `requires_confirmation`

## Recommended Service Design

Suggested service file:

- `backend/app/services/image_record_validation.py`

Suggested entry points:

1. `validate_image_record_for_submit(image_record)`
2. `validate_bound_image_record(image_record, asset)`

Both should return a unified structured result.

## Recommended Frontend Presentation

### Metadata Entry Side

Submission validation should:

- show blocking issues at the top of the form
- anchor field-related issues to the corresponding fields
- show strong warnings in a visible but non-destructive area

### Photographer Side

Post-upload validation should:

- show file analysis and validation summary before formal bind
- disable confirmation buttons for blocking issues
- require secondary confirmation when strong warnings exist

## MVP Rule Set

### Submission MVP

Blocking:

- `record_no` exists and is unique
- `title` exists
- `visibility_scope` valid
- `profile_key` valid
- `project_name` exists
- `image_category` exists
- `assigned_photographer_user_id` exists
- profile minimum required fields exist

Warning:

- `object_number` missing

### Bind/Replace MVP

Blocking:

- assigned photographer check
- status allows upload
- file format allowed
- file readable
- hash available and valid
- dimensions extractable
- duplicate hash blocked
- replacement-only rule enforced when current image exists

Warning:

- filename missing `record_no`
- filename missing `object_number`
- layer risk
- very large file
- PSB conversion path

## Acceptance Criteria

This validation phase is complete when:

1. submission validation runs before `ready_for_upload`
2. missing assigned photographer blocks submission
3. bind and replace actions both trigger post-file validation
4. duplicate hash blocks effective bind
5. filename mismatch produces strong warning rather than block
6. replacement invalidates previous successful validation
7. replacement returns the record to `uploaded_pending_validation`

## Out-of-Scope Reminder

The following are intentionally deferred:

- advanced semantic content validation
- OCR or image-content-based metadata consistency checks
- automated recommendation ranking
- cross-record machine learning matching
