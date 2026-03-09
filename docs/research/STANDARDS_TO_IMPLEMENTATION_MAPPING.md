# Standards to Implementation Mapping

## Purpose

This document maps the current MDAMS Prototype implementation to the standards, reference models, and community frameworks now identified in the research track.

It is intentionally practical.

Its goal is not to claim full compliance. Instead, it answers four concrete questions for each standard/framework:
1. What role does the standard play?
2. What is already present in the current implementation?
3. What is missing or only implicit?
4. What is the realistic next step if the project wants stronger alignment?

---

## Mapping Legend

- **Current alignment level**
  - **Direct**: explicit implementation feature or output already exists
  - **Partial**: some implementation behaviors align, but not as a formalized standard mapping
  - **Conceptual**: mainly used as framing rather than concrete implementation
  - **Future-facing**: relevant mainly for later extension

---

## 1. IIIF

### Role
Access/presentation interoperability standard.

### Current alignment level
**Direct**

### Already present in MDAMS
- dynamic IIIF Manifest generation;
- IIIF-facing public URL structure;
- Cantaloupe-based image service integration;
- Mirador viewer integration;
- distinction between stored asset file and IIIF-facing access representation.

### Evidence from current project facts
The current demonstrable workflow already includes producing IIIF-facing access output and previewing through Mirador.

### What is still missing or implicit
- no claim yet of broad/full IIIF feature coverage;
- no explicit internal profile documenting which Presentation API fields are intentionally supported;
- unclear depth of support for richer structures such as complex ranges, annotations, multi-part objects, or institution-specific descriptive enrichment.

### Practical interpretation
IIIF is the strongest case of an actually implemented standards-aligned layer in MDAMS. It should be described as the clearest direct implementation target rather than merely conceptual inspiration.

### Realistic next step
- document the current manifest profile actually emitted by MDAMS;
- record which IIIF fields are stable, optional, or not yet supported;
- add a small validation/test procedure for manifest output.

---

## 2. BagIt

### Role
Packaging/export standard for preservation-oriented transfer and structuring.

### Current alignment level
**Direct**

### Already present in MDAMS
- BagIt ZIP package download/export;
- export logic tied to digital assets rather than generic file download;
- strong relationship to fixity-aware workflow thinking.

### Evidence from current project facts
The current demonstrable workflow ends with export as a BagIt-oriented package.

### What is still missing or implicit
- current documentation does not yet clearly describe how complete the bag structure is;
- not yet documented whether manifest algorithms, tag files, and package validation are formalized beyond the basic output path;
- bag profile or institution-specific packaging conventions are not yet described.

### Practical interpretation
BagIt is currently a real implementation feature, but the research writing should distinguish between “BagIt-oriented export is present” and “full institutional packaging/preservation environment is complete.”

### Realistic next step
- inspect and document the exact structure of the generated bag;
- record which BagIt-required files are present;
- if useful, add a simple validation check for exported bags.

---

## 3. OAIS

### Role
Conceptual archival/lifecycle reference model.

### Current alignment level
**Conceptual**

### Already present in MDAMS
- ingest-oriented framing;
- lifecycle/process awareness;
- preservation-aware export thinking;
- differentiation between raw files, managed asset records, and access outputs;
- SIP-like language in project description.

### Evidence from current project facts
The prototype workflow links ingest, metadata/fixity processing, access output, and package export, which is strongly compatible with OAIS-style lifecycle thinking.

### What is still missing or implicit
- no formal OAIS information model mapping;
- no explicit AIP/DIP/SIP modeling as first-class entities;
- no preservation planning, administration, or archival storage functions in full OAIS depth;
- no claim should be made that MDAMS is a complete OAIS repository.

### Practical interpretation
OAIS should currently be treated as an organizing conceptual frame for research explanation, not as a directly implemented standard.

### Realistic next step
- create a lightweight conceptual diagram mapping current MDAMS workflow stages to OAIS-inspired functions;
- explicitly document which OAIS functions are out of scope.

---

## 4. PREMIS

### Role
Preservation metadata framework centered on Objects, Events, Agents, and Rights.

### Current alignment level
**Partial**

### Already present in MDAMS
- asset-centered records that can act as proto-object entities;
- fixity generation/verification behavior;
- asynchronous processing and conversion steps;
- metadata extraction steps;
- timestamps and status fields;
- likely identifiable system/user/process actors at least implicitly in operations.

### Evidence from current project facts
The prototype already performs ingest, fixity processing, metadata extraction, derivative-related processing, and package/export actions — all of which are strong candidates for PREMIS-like event interpretation.

### What is still missing or implicit
- PREMIS Objects, Events, Agents, and Rights are not yet formalized as explicit system entities or metadata structures;
- no stable event vocabulary yet for ingest, validation, conversion, or export actions;
- provenance/process history may exist operationally without being modeled as preservation metadata;
- rights information does not appear to be strongly developed.

### Practical interpretation
MDAMS appears to have several **proto-PREMIS behaviors** already, especially around events and object-level technical state, but not yet a formal PREMIS implementation. This is a strong research point: the prototype can be described as preservation-aware and PREMIS-informable without overclaiming compliance.

### Realistic next step
- define a minimal PREMIS-inspired event model for current workflow actions;
- record a small controlled vocabulary for events such as ingest, checksum generation, metadata extraction, conversion, manifest generation, and export;
- identify the minimum agent/right/object information worth capturing.

---

## 5. NISO Z39.87

### Role
Technical metadata standard for digital still images.

### Current alignment level
**Partial**

### Already present in MDAMS
- image metadata extraction;
- image-focused workflow orientation;
- large-image handling and derivative processing;
- IIIF image-serving context that depends on meaningful image characterization.

### Evidence from current project facts
The prototype already extracts image metadata and supports large-image scenarios such as PSB / BigTIFF handling.

### What is still missing or implicit
- no explicit internal crosswalk from extracted fields to Z39.87 elements;
- unclear whether format registry references, capture-related fields, image creation metadata, or technical characterization coverage are complete;
- no published technical metadata profile for image assets.

### Practical interpretation
MDAMS already behaves like an image-aware system, but its current technical metadata handling appears more implementation-driven than standards-profile-driven. Z39.87 is therefore a very strong candidate for formalizing the image technical metadata subset later.

### Realistic next step
- inspect currently extracted image metadata fields;
- create a small crosswalk showing which fields align to selected Z39.87 concepts;
- define a “minimum viable technical metadata profile” for still images in the prototype.

---

## 6. CS3DP (Community Standards for 3D Data Preservation)

### Role
Community guidance for lifecycle, metadata, preservation, legal, and access issues around 3D data.

### Current alignment level
**Future-facing**

### Already present in MDAMS
- not much direct 3D-specific implementation evidence at present;
- only the broader lifecycle-oriented perspective is currently relevant.

### What is still missing or implicit
- no 3D asset model;
- no 3D viewer/service chain;
- no 3D-specific metadata profile;
- no 3D preservation workflow.

### Practical interpretation
CS3DP should not be treated as a current implementation-aligned standard for MDAMS. Its value is as a structured reference for future expansion beyond still-image-centered workflows.

### Realistic next step
- keep it in the research track as a future extension reference;
- revisit only if 3D support becomes a concrete roadmap item.

---

## Cross-Standard Interpretation

The current implementation does **not** align with all standards in the same way. A more accurate reading is:

- **IIIF** = strongest direct implementation alignment;
- **BagIt** = direct export/package alignment;
- **OAIS** = conceptual reference model;
- **PREMIS** = partial but promising preservation-metadata alignment;
- **NISO Z39.87** = partial but promising technical-image-metadata alignment;
- **CS3DP** = future-facing extension reference.

This layered interpretation is stronger than a generic “the system follows standards” claim because it distinguishes:
- actual implemented standards-facing features,
- conceptually adopted frameworks,
- and future enrichment directions.

---

## Research Value

This mapping supports a strong thesis/paper claim:

> MDAMS Prototype demonstrates that a museum-oriented digital asset management prototype can combine direct implementation of selected interoperability/export standards with selective conceptual adoption of preservation and metadata frameworks, producing a system that is both technically demonstrable and research-meaningful without overstating formal compliance.

---

## Recommended Follow-Up Work

1. Add a PREMIS-inspired event table for the current workflow.
2. Add a Z39.87-inspired image technical metadata crosswalk.
3. Document the current IIIF manifest profile actually emitted by the prototype.
4. Inspect one real BagIt export and document its structure.
5. Add an OAIS-inspired scope diagram showing what is in and out of current prototype scope.
