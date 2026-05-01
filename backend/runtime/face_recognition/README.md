Local face recognition runtime layout
====================================

This directory is the minimized home for the Face-V2.0 logic inside mdams-prototype.

Expected structure
------------------

```text
backend/runtime/face_recognition/
|- models/
|  |- buffalo_l/
|     |- 1k3d68.onnx
|     |- 2d106det.onnx
|     |- det_10g.onnx
|     |- genderage.onnx
|     |- w600k_r50.onnx
|- index/
   |- meta.json
   |- embeddings.pkl
   |- faces/               # optional thumbnails copied from the old project
```

How to migrate from Face-V2.0
-----------------------------

1. Copy the old recognition models into `models/buffalo_l/`.
2. Copy the old face index files from `Face-V2.0/data/` into `index/`.
3. Enable the feature in `.env`:

```env
FACE_RECOGNITION_ENABLED=1
FACE_RECOGNITION_PROVIDER=local
FACE_RECOGNITION_MODEL_ROOT=/app/runtime/face_recognition
FACE_RECOGNITION_INDEX_DIR=/app/runtime/face_recognition/index
```

Notes
-----

- The mdams integration keeps only the read-only recognition flow.
- Upload scanning, clustering UI, and standalone Face-V2.0 pages are intentionally not copied here.
- If you still want to keep a separate recognition service during transition, set `FACE_RECOGNITION_PROVIDER=auto` or `remote`.
