# Testing Strategy

This project uses layered testing so failures are easier to localize.

## Test Layers

- `unit`: pure helper functions, metadata rules, and small deterministic logic.
- `contract`: schema contracts and response shape validation.
- `integration`: route + database + filesystem behavior.
- `smoke`: critical happy-path flows that should stay green at all times.
- `system`: multi-step subsystem flows that span upload, storage, detail, and platform exposure.

## Recommended Execution Order

1. Run unit and contract tests first.
2. Run integration tests after route or storage changes.
3. Run smoke/system tests before merging larger feature changes.
4. Run frontend lint/build/test after UI or contract changes.

## Current Backend Coverage

- `test_metadata_layers.py`: metadata layering and profile detection.
- `test_three_d_dictionary.py`: 3D metadata dictionary contract.
- `test_three_d_production.py`: 3D production chain record creation.
- `test_platform_directory.py`: platform directory and unified resource contract.
- `test_three_d_subsystem.py`: 3D subsystem end-to-end flow.
- `test_routes_smoke.py`: core asset upload and detail smoke path.
- `test_health.py`: health and readiness checks.
- `test_ingest.py`: ingest response contract and failure handling.

## Rules

- Every new feature should add at least one contract or integration test.
- Bug fixes should add a regression test at the narrowest layer that proves the fix.
- Smoke tests should remain small and stable.
- Avoid putting everything into one broad end-to-end test unless the behavior truly spans layers.
