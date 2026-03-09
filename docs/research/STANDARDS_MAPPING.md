# MDAMS Standards Mapping (Draft)

## Purpose

This document explains how major standards, frameworks, or reference models relate to MDAMS Prototype.

Its purpose is not to claim full formal compliance everywhere. Instead, it clarifies how the prototype selectively adopts ideas, structures, and implementation targets that are useful for a museum-oriented digital asset management system.

## Mapping Principle

At the prototype stage, standards should be used in a selective and conceptually meaningful way.

The project should avoid two extremes:
- ignoring standards entirely and becoming a generic file application;
- over-implementing standards so early that the prototype becomes too heavy to stabilize.

Therefore, MDAMS currently follows a **reference-alignment strategy**:
- implement where directly valuable;
- borrow concepts where full implementation is premature;
- document boundaries explicitly.

---

## 1. IIIF

### Role in MDAMS
IIIF is the clearest access-layer standard influence in the current prototype.

It contributes to:
- image delivery conventions;
- manifest-based representation of viewable resources;
- interoperability with compatible viewers;
- clearer separation between stored source files and access representations.

### In the Prototype
IIIF appears primarily through:
- manifest generation;
- image service exposure;
- viewer integration patterns;
- public URL and proxy path design.

### Why It Matters
IIIF helps the prototype demonstrate that access to museum digital objects is not limited to raw file download. It supports the argument that the system produces structured, interoperable access representations.

### Current Boundary
The prototype should not overclaim comprehensive IIIF implementation. The current emphasis is on demonstrating a workable IIIF-oriented access path, not exhausting the full IIIF ecosystem.

---

## 2. OAIS

### Role in MDAMS
OAIS functions mainly as a conceptual reference model rather than a fully implemented standard.

It informs:
- thinking about ingest;
- differentiation between managed information objects and raw files;
- preservation-aware workflow thinking;
- the idea that digital objects move through lifecycle stages;
- packaging/export awareness.

### In the Prototype
OAIS influence is visible in:
- ingest-oriented framing;
- preservation-oriented export thinking;
- process/lifecycle awareness;
- discussion of SIP/AIP-like ideas.

### Why It Matters
OAIS gives the prototype an archival/preservation logic beyond ordinary web file handling. It helps explain why fixity, metadata, and export/package concerns belong in the same system.

### Current Boundary
The prototype is not a full OAIS repository implementation. OAIS should be referenced as a conceptual guide, not claimed as fully realized institutional preservation infrastructure.

---

## 3. BagIt

### Role in MDAMS
BagIt contributes the clearest packaging/export reference in the current system.

It informs:
- packaging of digital asset content;
- export as a preservation-oriented operation rather than simple download;
- inclusion of payload and associated metadata/checksum logic.

### In the Prototype
BagIt influence appears in:
- BagIt ZIP export;
- export/package thinking tied to asset preservation and transfer;
- practical demonstration of structured packaging.

### Why It Matters
BagIt provides a tangible bridge between prototype implementation and preservation-aware practice. It helps show that the system handles digital assets as more than ad hoc uploaded files.

### Current Boundary
The prototype should describe BagIt support carefully: it demonstrates preservation-oriented export logic, but does not by itself establish a full preservation environment.

---

## 4. Metadata Standards and Structured Description

### Role in MDAMS
The prototype currently appears to support metadata capture/extraction more than formal, exhaustive metadata-standard implementation.

### In the Prototype
Relevant aspects include:
- descriptive metadata fields;
- technical metadata extraction;
- structured representation of asset information.

### Current Research Position
At this stage, the project should emphasize metadata role differentiation rather than overclaiming complete support for every museum metadata schema. Formal mapping can be expanded later if needed.

---

## 5. Practical Interpretation

The standards strategy of MDAMS Prototype can be summarized as follows:

- **IIIF**: practical access-layer implementation target;
- **OAIS**: conceptual lifecycle and preservation reference;
- **BagIt**: practical packaging/export reference;
- **metadata standards**: structured influence area, still open for deeper formalization.

This combination is strong enough to support a meaningful research argument while remaining feasible for a prototype.

## Research Implication

This mapping supports a key claim of the research track:

> A useful museum digital asset management prototype can be strengthened by selective, role-aware integration of standards and reference frameworks, without requiring full institutional-scale implementation at the earliest stage.
