# Current Project Facts for Research Use

## Purpose

This document captures the current observed facts of the MDAMS Prototype that can be directly reused in research writing.

It is intentionally grounded in the current repository state and existing project documentation, rather than ideal future design.

## Current Project Position

MDAMS Prototype is currently best understood as a high-value technical prototype for museum / exhibition digital resource scenarios, rather than as a complete production-grade DAMS.

Its strongest validated direction is the core chain connecting:
- asset ingest;
- metadata/fixity processing;
- large-image handling;
- IIIF-oriented access;
- export/package output;
- and containerized deployment in a real experimental environment.

## Current Implemented Capabilities

Based on the repository documentation, the current implemented scope includes:

### Backend-side capabilities
- basic file upload;
- SIP-style ingest interface;
- SHA256 fixity generation/verification;
- asset listing and deletion;
- dynamic IIIF Manifest generation;
- BagIt ZIP package download;
- asynchronous PSB-to-BigTIFF conversion;
- image metadata extraction.

### Frontend-side capabilities
- dashboard/basic admin entry;
- asset table browsing;
- upload flow;
- delete and download actions;
- Mirador integration for preview;
- ingest-oriented demo flow.

### Deployment/infrastructure capabilities
- Docker Compose-based deployment structure;
- backend/frontend/database/redis/worker/cantaloupe/filebrowser service composition;
- accommodation for lab-like deployment constraints such as local Linux server and NAS/NFS-related storage realities.

## Current Strongest Demonstrable Workflow

The current demonstrable workflow can be described as:

1. upload a digital file;
2. create or update an asset record;
3. generate fixity and extract technical metadata;
4. trigger asynchronous processing when needed;
5. produce IIIF-facing access output;
6. preview through Mirador;
7. export as a BagIt-oriented package.

This workflow is especially meaningful for large-image scenarios such as PSB / BigTIFF handling.

## Current Architectural Facts

Based on project documentation, the main architecture currently consists of:

- **Frontend**: React + Vite + TypeScript + Ant Design
- **Backend**: FastAPI + SQLAlchemy
- **Task Processing**: Celery + Redis
- **Database**: PostgreSQL
- **IIIF Image Service**: Cantaloupe
- **Viewer**: Mirador
- **Deployment**: Docker Compose

## Current Data-Model Fact

The currently documented implementation centers on an `Asset` entity as the core structured record, with fields such as file name, relative file path, file size, MIME type, metadata JSON, timestamps, and status.

This is important for research because it shows that the implementation already has an asset-centered tendency, even if the conceptual model still needs further clarification and enrichment.

## Current Major Gaps

The current project documentation also makes clear that the following are not yet mature:
- richer cataloging / descriptive models;
- derivative relationship modeling;
- advanced search and filtering;
- asset detail presentation;
- request / delivery workflows;
- user and permission systems;
- clearer modular backend structure in later phases.

## Current Stage Conclusion

The current prototype has moved beyond idea-stage experimentation. It already supports a meaningful technical narrative and a demonstrable workflow. However, its present research value lies less in institutional completeness and more in its ability to validate a coherent museum-oriented digital asset management chain under realistic engineering constraints.
