# User-Provided Standards Notes — 2026-03-09

## Source Package

User provided archive:
- `元数据标准规范文档.zip`

Archive was successfully extracted and inspected.

## Extracted Documents

1. `CS3DP/Community Standards for 3D Data Preservation.pdf`
2. `NISO/ANSI-NISO Z39.87-2006 (R2017), Data Dictionary - Technical Metadata for Digital Still Images.pdf`
3. `PREMIS/PREMIS 3 Ontology - LC Linked Data Services and Vocabularies.pdf`
4. `PREMIS/premis-3-0-final.pdf`
5. `PREMIS/understanding-premis.pdf`

---

## 1. PREMIS 3.0 Data Dictionary

### Basic identification
- Title: *PREMIS Data Dictionary for Preservation Metadata, version 3.0*
- Responsible body: PREMIS Editorial Committee
- Date observed in front matter: June 2015, revised November 2015
- Public standards page noted in document: http://www.loc.gov/standards/premis

### Key observed points from extracted pages
- The document presents itself as a comprehensive and practical resource for implementing preservation metadata.
- The structure clearly includes:
  - Introduction
  - Background
  - PREMIS Data Model
  - General Topics on Structure and Use
  - Implementation Considerations
  - The PREMIS Data Dictionary Version 3.0
  - Special Topics
  - Glossary
- The visible contents confirm that PREMIS is organized around major entities including:
  - Objects
  - Events
  - Agents
  - Rights
- The special-topics section explicitly includes topics highly relevant to MDAMS:
  - format information
  - environment
  - object characteristics and composition level
  - fixity, integrity, authenticity
  - digital signatures
  - non-core metadata

### Immediate relevance to MDAMS
- PREMIS is strongly relevant as a preservation-metadata framework.
- It maps well to current prototype concerns such as:
  - fixity checking
  - preservation events/process recording
  - agents involved in ingest/processing
  - rights and long-term management concerns
- PREMIS is likely especially useful for strengthening the conceptual model around ingest events, derivative generation events, validation/fixity events, and preservation-oriented metadata beyond descriptive fields.

### Working interpretation
MDAMS should probably not aim to claim full PREMIS implementation at this stage, but PREMIS provides a strong vocabulary and conceptual reference for preservation-oriented metadata design decisions.

---

## 2. NISO Z39.87 Technical Metadata for Digital Still Images

### Basic identification
- Title: *ANSI/NISO Z39.87-2006 (R2017): Data Dictionary – Technical Metadata for Digital Still Images*
- Standards body: National Information Standards Organization (NISO)
- Approval observed: approved December 18, 2006; reaffirmed April 3, 2017

### Key observed points from extracted pages
- The abstract explicitly states that the standard defines a set of metadata elements for raster digital images.
- Its goals include enabling users to:
  - develop digital image files,
  - exchange them,
  - interpret them.
- The abstract also explicitly emphasizes:
  - interoperability between systems, services, and software;
  - long-term management;
  - continuing access to digital image collections.
- Early contents show that the dictionary includes sections for:
  - basic digital object information,
  - identifiers,
  - file size,
  - format designation,
  - format registry information.

### Immediate relevance to MDAMS
- This is highly relevant to the image-focused side of MDAMS, especially where still-image derivatives, IIIF image delivery, and technical image characterization are involved.
- It provides a stronger standards basis for technical metadata modeling around digital still images than relying only on ad hoc extracted fields.
- It may be useful when formalizing what technical image metadata should be captured at ingest.

### Working interpretation
NISO Z39.87 can serve as a technical-metadata reference point for image assets in MDAMS, especially if the project later refines a more explicit technical metadata profile for master images and derivatives.

---

## 3. CS3DP — Community Standards for 3D Data Preservation

### Basic identification
- Title observed: *3D Data Creation to Curation: Community Standards for 3D Data Preservation*
- Editors observed: Jennifer Moore, Adam Rountrey, Hannah Scates Kettler
- Publisher observed: Association of College and Research Libraries / American Library Association
- Year observed: 2022

### Key observed points from extracted pages
- The contents reveal a broad end-to-end treatment of 3D data, including:
  - best practices for 3D data preservation;
  - management and storage of 3D data;
  - metadata requirements for 3D data;
  - copyright and legal issues;
  - access to 3D data.
- The metadata chapter explicitly situates 3D metadata in relation to the digital asset life cycle.
- The access chapter highlights discovery, technology limitations, audiences, and next-step recommendations.

### Immediate relevance to MDAMS
- Even though MDAMS is not yet a dedicated 3D system, this source is very useful as a forward-looking standards/community reference.
- It may help frame a later expansion path if the project broadens beyond still images and documents toward 3D cultural heritage assets.
- It is also valuable methodologically because it shows how a community standard can span creation, management, metadata, preservation, rights, and access as one connected workflow.

### Working interpretation
CS3DP should be treated as a complementary, domain-expansion reference rather than a current core standard for the prototype. It may become more central if the project later adds 3D asset support.

---

## 4. PREMIS Ontology PDF

### Current status
- File identified: `PREMIS 3 Ontology - LC Linked Data Services and Vocabularies.pdf`
- Current extraction result: PDF opened, but useful text was not extracted in the first pass.

### Preliminary interpretation
- This likely supports a linked-data / ontology representation of PREMIS concepts.
- It may become relevant if the research track later explores semantic-web or linked-data representations of preservation metadata.

### Follow-up needed
- A second-pass extraction or alternate source retrieval is needed before making detailed claims.

---

## 5. understanding-premis.pdf

### Current status
- File identified and extracted from the archive.
- Not yet deeply reviewed in this pass.

### Preliminary interpretation
- This is likely an explanatory or introductory companion to PREMIS.
- It may be useful for converting PREMIS from a standards reference into a more accessible narrative for the paper's conceptual framing section.

### Follow-up needed
- Perform a dedicated extraction and summary pass.

---

## Cross-Source Interpretation

The user-provided package significantly strengthens the metadata-standards side of the MDAMS research track.

At this point, the standards landscape around MDAMS can be described more concretely as:
- **IIIF** for access/presentation interoperability;
- **BagIt** for preservation-oriented package/export structure;
- **OAIS** for conceptual archival/lifecycle framing;
- **PREMIS** for preservation metadata concepts and entities;
- **NISO Z39.87** for technical metadata of digital still images;
- **CS3DP** as a useful community reference for future 3D/preservation-oriented expansion.

## Recommended Next Uses in the Research Track

1. Add PREMIS explicitly to `STANDARDS_MAPPING.md` and `DESIGN_DECISIONS.md`.
2. Consider whether current MDAMS ingest/fixity/task logs can be interpreted as proto-PREMIS events.
3. Consider whether current image characterization can be aligned with selected NISO Z39.87 elements.
4. Keep CS3DP as a future-facing reference unless/until 3D asset support becomes an actual scope item.
5. Run a dedicated second pass on `understanding-premis.pdf` and the PREMIS ontology source.
