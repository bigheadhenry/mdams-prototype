# IMAGE_RECORD_MATCHING_PHASE1_PLAN

## Purpose

This document archives the agreed conclusions for Problem 2: the image-record-to-file matching mechanism for photographers. It is intended to pair with `IMAGE_RECORD_ROLE_SPLIT_PHASE1_PLAN.md` and serve as the implementation baseline for the matching workflow.

## Problem Statement

After metadata entry staff create and submit a single-image `ImageRecord`, photographers need a safe and efficient way to:

- find their assigned ready-for-upload records
- upload a single image file for a selected record
- explicitly confirm the binding
- replace an already bound image when needed

The system must avoid duplicate active bindings, reduce misbinding risk, and keep state transitions traceable.

## Final Agreed Conclusions

### 1. Matching Flow

The matching flow must use:

- select record first
- upload image second

The system must not use a "upload first, guess record later" workflow in phase 1.

### 2. Record Pool Visibility

Photographers are not allowed to view unassigned ready-for-upload records.

By default, a photographer can only access records that satisfy both:

- `status = ready_for_upload`
- `assigned_photographer_user_id = current_user.id`

### 3. Workbench Structure

The photographer workbench should be split into two levels:

1. ready-for-upload record pool
2. upload and matching page for one selected record

### 4. Explicit Confirmation

Image binding must not become effective immediately after file upload.

Required flow:

1. upload file
2. system performs temporary file analysis
3. photographer explicitly clicks one of:
   - confirm bind
   - confirm replace

Without confirmation, no formal binding is created.

### 5. Binding Rule

`ImageRecord` and `Asset` remain strictly `1:1`.

Rules:

- if no image is bound yet, one image may be bound
- if an image is already bound, a second active binding is not allowed
- the only allowed action in that case is replacement

### 6. Replacement Rule

Replacement is allowed.

Replacement consequences:

- the new file becomes the only current active binding
- the old file is no longer treated as the current effective resource
- the old file is retained only in audit history
- replacement returns the record to `uploaded_pending_validation`

### 7. State After Bind or Replace

After a successful bind or replacement, the record should move to:

- `uploaded_pending_validation`

The record should not go directly to a final completed state in phase 1.

### 8. Primary Search Keys

The primary search keys for the photographer record pool are:

- `record_no`
- `object_number`
- `title` or `image_name`

## Recommended Photographer Workbench Design

## Level 1: Ready-for-upload Record Pool

This is the photographer's task entry page.

Recommended visible fields:

- record number
- title
- object number
- project name
- image category
- assigned photographer
- submitted time
- status

Recommended default filters:

- status = `ready_for_upload`
- assigned photographer = current user

Recommended manual filters:

- record number
- object number
- title or image name
- project name

Recommended actions:

- `进入上传匹配`
- `替换图片` when a current binding already exists

## Level 2: Upload and Matching Page

Recommended layout:

- left side: image record summary
- right side: file upload and confirmation area

Recommended record summary:

- record number
- title
- object number
- project name
- profile
- metadata entry user
- assigned photographer
- current status
- current bind status

Recommended upload-side elements:

- choose file
- file analysis result
- hash, dimensions, format
- risk hints
- current bind information
- confirm bind button
- confirm replace button

## Required Action Model

Recommended operational sequence:

1. photographer opens one assigned record
2. uploads one file
3. system performs temporary analysis
4. system displays file summary and warnings
5. photographer explicitly confirms bind or replace
6. record enters `uploaded_pending_validation`

## Recommended Backend Action Design

Suggested endpoints:

1. `GET /api/image-records/ready-for-upload`
2. `GET /api/image-records/{id}`
3. `POST /api/image-records/{id}/upload-temp`
4. `POST /api/image-records/{id}/confirm-bind`
5. `POST /api/image-records/{id}/confirm-replace`

Minimal acceptable simplification for MVP:

- `POST /api/image-records/{id}/upload-and-bind`
- `POST /api/image-records/{id}/replace`

However, the preferred design is to keep upload and confirmation logically separate.

## System Assistance Rules

Phase 1 system assistance may include:

- detect whether the file hash already exists in the system
- check whether file name contains the record number or object number
- check whether the extension is within allowed upload formats
- detect whether a current active binding already exists

These are assistance signals only. They should not replace explicit operator confirmation.

## Replacement Constraints

Recommended replacement rules:

1. replacement may only occur on the same selected record
2. the UI should show current image information before replacement
3. the old image should lose current-effective status after replacement
4. replacement should generate an audit event
5. replacement should trigger re-validation through `uploaded_pending_validation`

## MVP Scope

Phase-1 matching MVP includes:

- my ready-for-upload record pool
- single-record upload page
- file analysis summary after upload
- explicit confirm-bind action
- explicit confirm-replace action
- state transition to `uploaded_pending_validation`

Phase-1 matching MVP excludes:

- batch upload with automatic dispatch
- automatic candidate recommendation
- upload-first matching
- intelligent multi-record guessing
- automatic grouping

## Acceptance Criteria

This matching phase is complete when:

1. photographers can only see their own assigned ready-for-upload records
2. a photographer can open one record and upload one candidate file
3. the system shows a temporary analysis result before formal bind
4. formal binding only occurs after explicit confirmation
5. a second active image cannot be added to the same record
6. a replacement can be executed with explicit confirmation
7. replacement sends the record back to `uploaded_pending_validation`

## Out-of-Scope Reminder

The following are intentionally deferred:

- batch auto-matching
- smart recommendation ranking
- multi-file matching
- automatic grouping or collection-level image bundling
