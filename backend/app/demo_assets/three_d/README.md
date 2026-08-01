# Three-D Demo Assets

These files are bundled backend seed assets for the MDAMS three-dimensional resource subsystem.

Startup seeding registers:

- Simple previewable model samples: Khronos Box, Khronos Triangle, and Horus.
- Fifteen additional official Khronos glTF 2.0 GLB samples covering animation, morph targets, skins, textures, vertex colors, UV channels, alpha blending, and buffer layouts.
- `demo-museum-vase-object`: a complete object with `original`, `v1-web`, and `v2-detail` versions.
- `demo-ancient-building-scene`: a package-style scene object with model, point cloud, oblique reference image, and production note files.

The seed service copies these files into `UPLOAD_DIR/three-d/{asset_id}/files/{role}/`, builds resource manifests, writes object metadata, file-role records, preservation fields, and production events.

The unified catalog contains exactly 20 independent seeded 3D digital objects (22 representations because the vase has three managed versions). Each official sample stores its model-specific source URL, README URL, author/credit, license, rights constraints, computed glTF structure counts, and SHA256 fixity metadata. Khronos models come from [KhronosGroup/glTF-Sample-Assets](https://github.com/KhronosGroup/glTF-Sample-Assets); the license recorded on each object is authoritative for that model.
