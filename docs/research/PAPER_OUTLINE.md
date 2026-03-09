# MDAMS Paper Outline (Draft)

## Tentative Title

Design and Implementation of a Museum Digital Asset Management System Prototype: From Ingest to IIIF-Based Access and Preservation-Oriented Export

## 1. Introduction
- Background: growth of museum digital resources and need for manageable digital objects.
- Problem: many systems are either too broad, too infrastructure-heavy, or poorly aligned with cultural heritage workflows.
- Research objective: design and validate a prototype focused on the core MDAMS workflow.
- Contribution statement.

## 2. Background and Related Concepts
- Museum digital assets and digital object management.
- DAMS vs repository vs collection management context.
- IIIF overview.
- OAIS as a conceptual reference.
- BagIt as export/packaging reference.

## 3. Research Problem and Design Goals
- What the prototype is trying to prove.
- Scope boundaries.
- Why the project focuses on a core workflow instead of full institutional coverage.
- Design goals: ingest, metadata, fixity, derivatives, access, export.

## 4. Conceptual Model
- Primary managed object.
- Relationship between asset, file, metadata, derivative, access representation, export package.
- Implications for UI, API, and storage logic.

## 5. System Architecture and Implementation
- Overall architecture.
- Backend, frontend, asynchronous task system.
- Storage and file-processing flow.
- IIIF-related components.
- Export mechanism.

## 6. Core Workflow Validation
- Representative workflow scenario.
- Ingest steps.
- Metadata/fixity generation.
- Derivative/access generation.
- IIIF access demonstration.
- Export/package generation.

## 7. Discussion
- Design trade-offs.
- Standards integration vs prototype simplicity.
- Engineering constraints encountered.
- What remains outside the current prototype scope.

## 8. Conclusion and Future Work
- Summary of prototype value.
- Limits of the current implementation.
- Future directions: richer metadata modeling, workflow management, preservation depth, institutional integration.

## Optional Appendices / Supporting Materials
- architecture diagrams;
- workflow diagrams;
- sample manifests or package structures;
- deployment notes;
- screenshots.
