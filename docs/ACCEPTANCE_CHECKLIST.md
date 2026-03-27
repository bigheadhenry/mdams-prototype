# MDAMS Prototype Main Chain Acceptance Checklist

This checklist covers the current priority path:

`upload -> ingest -> convert -> manifest -> preview -> download`

Use it for:
- local startup validation
- regression checks after config changes
- demo preflight
- quick failure diagnosis

## 1. Environment

- `docker compose config` succeeds
- `docker compose ps` shows `backend`, `frontend`, `db`, `redis`, `worker`, and `cantaloupe`
- `http://localhost:3000` opens without a white screen
- `http://localhost:8000/health` returns `healthy`
- `http://localhost:8000/ready` returns `healthy`

## 2. Upload And Ingest

- A supported image can be selected in the frontend
- Upload returns success
- The new asset appears in the asset list
- Asset detail opens after upload
- `GET /assets` returns the uploaded record

## 3. Metadata

- Asset detail shows filename, size, mime type, and status
- Width and height are present when the sample provides them
- Technical metadata is rendered in the detail view
- No unexpected server error appears in the metadata section

## 4. Conversion

- PSB sample triggers the background conversion flow
- Worker logs show the conversion task running
- Converted output is written back to the asset record
- The asset status eventually becomes `ready` or a clear error state

## 5. IIIF

- `GET /assets/{id}/manifest` returns a valid manifest
- Manifest IDs resolve correctly
- The manifest references the expected image service URL
- Mirador can load the manifest
- The IIIF image service can fetch the converted or source image

## 6. Download

- Current file download returns HTTP 200
- BagIt ZIP download returns HTTP 200
- Downloaded content matches the selected asset

## 7. Failure Checks

- DB downtime surfaces as a clear health check failure
- Missing upload directory surfaces as a clear health check failure
- Failed conversion is visible in the asset detail status
- Manifest generation failures are visible in the API response

## 8. Minimum Pass Criteria

Treat the current build as acceptable only if all of the following pass:

- frontend opens
- `/health` and `/ready` are healthy
- asset upload works
- asset list updates
- asset detail loads
- metadata is visible
- conversion either succeeds or fails clearly
- manifest is accessible
- Mirador can load at least one ready asset
- current file download works
- BagIt download works

## 9. Suggested Next Check

After this checklist is green, the next useful step is:

1. split the backend routes into smaller modules
2. add a narrow backend health test
3. tighten the asset detail data contract

