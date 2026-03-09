# MDAMS Concept Model (Draft)

## Purpose

This document defines the current conceptual model for MDAMS Prototype at the product/architecture level. It is intended to guide future implementation, documentation, and academic writing.

## Core Position

The prototype should treat the **digital asset** as the primary managed object.

The system is not centered on isolated files, nor on an all-encompassing museum collection-management model. It is centered on a manageable digital asset that can move through ingest, verification, access, and export.

## Core Entities

### 1. Asset
The main managed object in the system.

An asset represents a logically coherent digital object or digital resource package that the system ingests, processes, and makes available.

Typical responsibilities:
- identity within the system;
- linkage to one or more files;
- descriptive and technical metadata association;
- process status;
- access and export relationships.

### 2. File Object
A file physically associated with an asset.

Possible subtypes:
- original file;
- normalized file;
- derivative/access file;
- auxiliary file.

Typical responsibilities:
- storage path/reference;
- format and size;
- checksum/fixity value;
- relationship to processing stage.

### 3. Metadata Record
Metadata associated with the asset and/or its files.

Possible categories:
- descriptive metadata;
- technical metadata;
- structural metadata;
- administrative metadata.

The prototype does not need full formal standard implementation everywhere, but it should clearly distinguish metadata roles.

### 4. Process Event
A recorded event in the asset lifecycle.

Examples:
- ingest started;
- file analyzed;
- checksum generated;
- derivative generated;
- manifest created;
- export package generated.

This entity is important for both observability and research discussion.

### 5. Access Representation
A representation intended for viewing or external access.

Examples:
- IIIF manifest;
- preview image;
- viewer-ready derivative.

This is distinct from the original preservation-oriented file.

### 6. Export Package
A packaging/export representation of the asset.

Examples:
- BagIt ZIP;
- preservation-oriented bundle;
- ingest/export package snapshot.

## Relationship Sketch

Asset
- has one or more File Objects
- has one or more Metadata Records
- has zero or more Process Events
- has zero or more Access Representations
- has zero or more Export Packages

File Objects may:
- produce derivative File Objects;
- contribute technical metadata;
- feed Access Representations;
- be included in Export Packages.

## Conceptual Boundaries

### What this model is trying to avoid
- treating every uploaded file as a complete product object;
- collapsing preservation, access, and metadata concerns into a single undifferentiated record;
- overcommitting to a fully institutional collection-management ontology too early.

### What this model is trying to support
- a stable core workflow;
- clear product terminology;
- explainable architecture;
- future extension toward richer museum-domain modeling.

## Current Working Implication

UI, API, and documentation should gradually move toward asset-centered language and structure, even if the underlying implementation remains partially file-driven during the prototype stage.
