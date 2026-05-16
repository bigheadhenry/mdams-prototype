# 3D Test Models

This folder contains a small sample package for Web viewer compatibility checks.

## Included versions

- `museum-vase-source.gltf`: external `gltf + bin + png` package
- `museum-vase-preview.glb`: single-file browser preview
- `museum-vase-detail.glb`: higher-detail preview
- `khronos-box.gltf`: online sample model from Khronos glTF Sample Assets, embedded glTF, CC BY 4.0.
- `khronos-triangle.gltf`: online sample model from Khronos glTF Sample Assets, embedded glTF, CC0 1.0.
- `horus.glb`: downloadable Sketchfab model from The British Museum, GLB, CC BY-NC-SA.

## Online sample sources

- Box: https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Box
- Triangle: https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Triangle
- Horus: https://sketchfab.com/3d-models/horus-e62f9907d04041e7bcd485e51063b8d5

## Purpose

Use these models to test:

- GLB single-file loading
- glTF with external BIN / PNG dependencies
- Web preview eligibility and version selection
- Browser rendering stability for a slightly denser mesh
