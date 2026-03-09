# External Review Notes — 2026-03-09

## Scope of This Pass

This pass focused on establishing a first credible external reference base for the MDAMS research track, covering:
- official technical standards/specifications;
- academic research leads;
- IIIF practice/adoption leads;
- research methodology leads.

## What Was Successfully Verified

### 1. IIIF Presentation API 3.0
Verified via official IIIF search result and direct fetch.

Key confirmed points:
- stable version shown as 3.0.0;
- designed for rich online viewing of compound digital objects;
- explicitly not intended to provide harvesting/discovery metadata;
- defines core classes such as Manifest, Canvas, Collection, Range, AnnotationPage, and Annotation.

Research implication:
- supports a clean argument that IIIF in MDAMS belongs primarily to the access/presentation layer.

### 2. BagIt RFC 8493
Verified via RFC Editor search result and direct fetch.

Key confirmed points:
- BagIt is a hierarchical file layout convention for storage and transfer of arbitrary digital content;
- emphasizes payload + tag files;
- highlights strong integrity assurances and direct file access;
- notes wide use in preservation-related organizations.

Research implication:
- strongly supports MDAMS BagIt export as preservation-oriented packaging rather than generic file download.

### 3. OAIS entry points
Official and standards-related OAIS entry points were located.

Key confirmed points:
- OAIS is clearly an authoritative reference-model context;
- further extraction is still needed for better citation-quality notes.

Research implication:
- OAIS can already be used as a conceptual framing source, but should not yet be quoted in detail without a second pass.

## What Was Found But Not Yet Fully Retrieved

### Academic leads
- Digital Asset Management Systems in Museums
- DAM Becky, Look at That Asset
- Advancing cultural heritage: a decadal review of digital ...
- Design Science in Information Systems Research
- The design science research process ...

### IIIF practice/adoption leads
- Practical applications of IIIF report
- Navigating IIIF in Art Research
- Evolving Standards in Digital Cultural Heritage / IIIF 3D

## Current Retrieval Constraints Observed

- Some academic sources are blocked by 403 or publisher restrictions in direct fetch mode.
- This means next retrieval passes may need:
  - alternate copies;
  - abstract-page fetching;
  - bibliographic entry capture first, full text later.

## Immediate Research Benefit

Even this first pass already improves the research subproject in two ways:

1. It confirms that the project's standards framing is not speculative.
2. It identifies a realistic external review agenda for the next stage.

## Recommended Next Pass

1. prioritize accessible open sources from repositories, Zenodo, institutional repositories, and arXiv-like mirrors;
2. collect bibliographic metadata for blocked publisher pages;
3. build annotated entries tied to specific MDAMS research questions.
