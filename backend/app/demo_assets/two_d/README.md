# Two-D Demo Assets

This directory contains the 20 real-image records used by the MDAMS startup test dataset.

- Source: The Metropolitan Museum of Art Collection API.
- Selection: public-domain objects with downloadable JPEG images, diversified across painting/manuscript, decorative art, textiles, musical instruments, arms and armor, and jewelry.
- Rights: The Met Open Access / CC0 1.0. See <https://www.metmuseum.org/about-the-met/policies-and-documents/open-access>.
- Files: `met-{objectID}.jpg` contains the access image and `source_metadata/met-{objectID}.json` preserves the complete API record retrieved for the object.

At startup, the seed service copies the images to `UPLOAD_DIR/two-d/met-open-access/`, creates one approved ingest sheet with 20 image records, registers 20 ready assets, calculates SHA256 checksums and dimensions, and writes complete management, technical, profile, rights, and raw-source metadata layers. The seed is idempotent, so restarts update these records without creating duplicates.
