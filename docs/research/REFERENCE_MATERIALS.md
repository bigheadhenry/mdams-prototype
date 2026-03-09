# Reference Materials (Initial Collection)

## Purpose

This document collects early reference materials for the MDAMS research track, including technical standards, conceptual frameworks, public specifications, and directions for academic/industry review.

This is an initial working collection, not yet a polished bibliography.

---

## A. Core Technical Standards / Official Specifications

### 1. IIIF Presentation API 3.0
- Source: IIIF Consortium
- URL: https://iiif.io/api/presentation/3.0/
- Search status: verified via official IIIF site search result and direct fetch
- Current observed notes:
  - Official stable version shown as 3.0.0
  - Objective: provide the information necessary for a rich online viewing environment for compound digital objects
  - Explicitly states that it does **not** aim to provide metadata for harvesting and discovery/search indexing
  - Defines core resource types including Collection, Manifest, Canvas, Range, AnnotationPage, and Annotation
  - Strong relevance to structured presentation of digitized cultural objects across institutions
- Relevance to MDAMS:
  - direct support for manifest-oriented access representation
  - supports the argument that MDAMS should distinguish access/presentation from broader discovery metadata concerns
  - provides a strong standards basis for IIIF-facing access workflow claims

### 2. IIIF Project / Consortium Overview
- Source: IIIF
- URL: https://iiif.io/
- Search status: verified via official IIIF site search result and direct fetch
- Current observed notes:
  - IIIF is supported by a global consortium
  - Used by aggregators, research institutions, national libraries, archives, museums, software companies, and digital agencies
- Relevance to MDAMS:
  - supports the case that IIIF is an established interoperability direction in galleries, libraries, archives, and museums

### 3. BagIt File Packaging Format (RFC 8493)
- Source: RFC Editor / IETF informational RFC
- URL: https://www.rfc-editor.org/rfc/rfc8493
- Search status: verified via RFC Editor search result and direct fetch
- Current observed notes:
  - BagIt is defined as a set of hierarchical file layout conventions for storage and transfer of arbitrary digital content
  - A bag contains payload files plus metadata tag files
  - Key strengths explicitly described in the RFC include strong integrity assurances and direct file access
  - The RFC notes broad use in digital preservation-related organizations including the Library of Congress and university libraries
  - Core required structure includes `bagit.txt`, one or more `manifest-<algorithm>.txt`, and a `data/` payload directory
- Relevance to MDAMS:
  - directly supports preservation-oriented export/package design
  - aligns well with fixity-aware asset packaging
  - provides a solid basis for describing the prototype's BagIt ZIP output as structured packaging rather than generic download

### 4. OAIS Reference Model / ISO 14721
- Sources:
  - OAIS information site: http://www.oais.info/
  - ISO entry discovered in search: https://www.iso.org/standard/87471.html
  - CCSDS PDF source discovered in search: https://ccsds.org/Pubs/650x0m3.pdf
- Search status: official/near-official entry points identified; lightweight fetch on OAIS info site succeeded
- Current observed notes:
  - OAIS is clearly established as a reference model context for archival information systems
  - Official/standards-related entry points have been located, but a fuller text extraction and citation-quality note still needs a dedicated follow-up pass
- Relevance to MDAMS:
  - conceptual reference for ingest, lifecycle thinking, package concepts, and preservation-aware system framing

---

## B. Initial Academic / Research Leads

### 1. Digital Asset Management Systems in Museums
- Source type: research/thesis-style document
- Search result URL: https://jscholarship.library.jhu.edu/server/api/core/bitstreams/9193efe7-80a3-471d-a58a-609215762eef/content
- Search status: discovered by search, direct fetch blocked with 403 in current environment
- Potential relevance:
  - likely directly relevant to museum DAMS framing
  - should be revisited through alternative access path or bibliographic lookup

### 2. “DAM Becky, Look at That Asset”: Digital Asset Management in Cultural ...
- Source type: academic paper / master's paper lead
- URL: https://cdr.lib.unc.edu/concern/masters_papers/v118rk462
- Search status: discovered, not yet fetched
- Potential relevance:
  - likely useful for cultural-heritage DAM practice framing

### 3. Advancing cultural heritage: a decadal review of digital ...
- Source type: Nature-related review lead
- URL: https://www.nature.com/articles/s40494-025-01714-x
- Search status: discovered, not yet fetched
- Potential relevance:
  - may help frame broader digital cultural heritage trends and technology context

### 4. Design Science in Information Systems Research
- Source type: foundational methodology lead
- URL: https://www.jstor.org/stable/25148625
- Search status: discovered by search, direct fetch blocked with 403 in current environment
- Potential relevance:
  - strong candidate for methodological framing if the paper adopts design science / prototype research language

### 5. The design science research process: a model for producing and presenting information systems research
- Source type: methodology lead
- Search result indicates accessible variants via ResearchGate / arXiv-like mirrors
- Search status: discovered, not yet fetched
- Potential relevance:
  - useful for framing how prototype building becomes research output

---

## C. Initial IIIF Practice / Adoption Leads

### 1. Practical applications ... IIIF - Final Report
- Source type: practice/report lead
- URL: https://zenodo.org/records/6884885/files/Practical%20Applications%20of%20IIIF%20-%20Final%20Report%20v.pdf
- Search status: discovered, not yet fetched
- Potential relevance:
  - likely useful for practical IIIF adoption and implementation examples

### 2. Navigating IIIF in Art Research: How Two Institutions Engage with ...
- Source type: scholarly article lead
- URL: https://www.journals.uchicago.edu/doi/abs/10.1086/735803?journalCode=adx
- Search status: discovered, not yet fetched
- Potential relevance:
  - likely useful for institutional practice and adoption analysis

### 3. Evolving Standards in Digital Cultural Heritage - Developing a IIIF 3D ...
- Source type: book/chapter lead
- URL: https://link.springer.com/chapter/10.1007/978-3-031-35593-6_3
- Search status: discovered, not yet fetched
- Potential relevance:
  - useful for broader standards-evolution discussion in cultural heritage contexts

---

## D. Industry / Practice Observation Directions

The following industry/practice areas should be tracked as contextual material:

- museum collection systems vs digital asset management systems;
- digital preservation platforms and repository tools;
- IIIF ecosystem adoption and viewer/server tooling;
- large-image handling in heritage digitization workflows;
- convergence or divergence between DAM, repository, and preservation platform roles.

---

## E. Current Working Interpretation

At this stage, the strongest confirmed standards base for MDAMS research consists of:
- IIIF for access representation;
- BagIt for preservation-oriented export/package logic;
- OAIS for conceptual preservation/lifecycle framing;
- PREMIS for preservation metadata concepts and entities;
- NISO Z39.87 for technical metadata of digital still images.

The current research literature collection is still at the lead-gathering stage, but the first pass has already identified promising directions in:
- museum DAMS;
- IIIF institutional adoption;
- design science / prototype methodology;
- broader digital cultural heritage review literature.

User-provided standards material has also expanded the standards horizon to include community guidance for 3D data preservation (CS3DP), which is not yet central to current MDAMS scope but may be valuable for future extension analysis.

## F. Progress Update After Second Retrieval Pass

The second retrieval pass achieved the following concrete advances:
- directly verified two Zenodo-hosted IIIF practice/project sources;
- verified bibliographic metadata and DOI for Crockett's 2020 cultural-heritage DAM paper;
- confirmed the CCSDS OAIS PDF is reachable;
- created a first working `ANNOTATED_BIBLIOGRAPHY.md` for the research track.

## G. Next Retrieval Priorities

1. Extract and summarize at least 3 accessible academic sources for museum/cultural-heritage DAMS.
2. Perform a dedicated PDF text-extraction pass for Crockett's paper.
3. Retrieve a cleaner OAIS official summary/citation note from CCSDS/ISO-adjacent materials.
4. Retrieve at least 1 foundational design-science/prototype-methodology source accessible in full text.
5. Expand the annotated bibliography into citation-ready entries plus thematic synthesis notes.
