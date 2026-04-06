# Image Derivative Policy

This project keeps the original uploaded image, but records a recommendation for how that image should be served for IIIF/Mirador preview.

## Why this exists

- Big TIFF/PSB files are expensive to read on the first request.
- Ordinary JPEG files are already display-friendly and usually do not need conversion.
- We want a rule that is explicit, stable, and visible in asset metadata.

## Policy table

| Source format | Typical condition | Recommended strategy | Why |
| --- | --- | --- | --- |
| TIFF / PSB | File size >= 50 MB or pixel count >= 25 MP | `generate_pyramidal_tiff` | A pyramidal tiled TIFF is much easier for IIIF servers to read and tile. |
| JPEG | File size >= 120 MB or pixel count >= 60 MP | `generate_access_jpeg` | A very large JPEG can use a lighter access copy, but does not need a pyramidal TIFF by default. |
| JPEG | Below the large-file threshold | `keep_original` | JPEG is already a reasonable display format. |
| PNG / WebP / other formats | Default | `keep_original` | Avoid unnecessary conversion unless a specific workflow needs it. |

## Notes

- This policy is a recommendation layer, not a forced conversion step.
- The original file remains the archival source.
- The recommendation is written into technical metadata so it can be inspected from the asset detail page and IIIF metadata.
- If a future workflow needs automatic derivative generation, this policy can be reused as the decision layer.
