# Three-D Demo Assets

These files are bundled backend seed assets for the MDAMS three-dimensional resource subsystem.

Startup seeding registers:

- Simple previewable model samples: Khronos Box, Khronos Triangle, and Horus.
- `demo-museum-vase-object`: a complete object with `original`, `v1-web`, and `v2-detail` versions.
- `demo-ancient-building-scene`: a package-style scene object with model, point cloud, oblique reference image, and production note files.

The seed service copies these files into `UPLOAD_DIR/three-d/{asset_id}/files/{role}/`, builds resource manifests, writes object metadata, file-role records, preservation fields, and production events.
