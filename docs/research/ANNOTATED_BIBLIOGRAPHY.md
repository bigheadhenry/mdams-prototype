# Annotated Bibliography (Working Draft)

## Purpose

This document begins converting the external source pool into an annotated bibliography that can directly support the MDAMS paper/research track.

Each entry records:
- source identification;
- access status;
- key observed points;
- relevance to MDAMS;
- possible research-question linkage.

This is a working draft, not a final citation-formatted bibliography.

---

## 1. IIIF Consortium. *Presentation API 3.0*.
- URL: https://iiif.io/api/presentation/3.0/
- Type: official technical specification
- Access status: directly fetched and verified

### Key observed points
- Stable version shown as 3.0.0.
- Designed to support rich online viewing environments for compound digital objects.
- Explicitly does not aim to provide metadata for harvesting and discovery.
- Defines core structures including Collection, Manifest, Canvas, Range, AnnotationPage, and Annotation.

### Relevance to MDAMS
- Strong foundation for the prototype's manifest-generation and access/presentation layer.
- Helps justify a conceptual separation between asset management, descriptive metadata work, and end-user presentation.
- Useful when explaining why IIIF is important but not sufficient as the whole metadata architecture.

### Likely research linkage
- RQ on standards alignment.
- RQ on why the prototype centers interoperability through IIIF access rather than attempting universal metadata standardization.

---

## 2. Kunze et al. *RFC 8493: The BagIt File Packaging Format (V1.0).* RFC Editor.
- URL: https://www.rfc-editor.org/rfc/rfc8493
- Type: official technical standard / RFC
- Access status: directly fetched and verified

### Key observed points
- BagIt is defined as hierarchical file layout conventions for storage and transfer of arbitrary digital content.
- A bag includes payload files and metadata tag files.
- The RFC highlights strong integrity assurances and direct file access.
- The specification notes broad use by preservation-oriented organizations.

### Relevance to MDAMS
- Strong standards basis for the prototype's BagIt ZIP export.
- Supports interpretation of export as preservation-aware packaging rather than simple download bundling.
- Aligns well with fixity workflows and chain-of-custody thinking.

### Likely research linkage
- RQ on preservation-oriented design.
- RQ on why export/package structure matters in a museum-oriented digital asset workflow.

---

## 3. OAIS Reference Model / ISO 14721 entry points.
- URLs:
  - http://www.oais.info/
  - https://www.iso.org/standard/87471.html
  - https://ccsds.org/Pubs/650x0m3.pdf
- Type: reference-model / standards-family entry
- Access status:
  - OAIS info page fetched
  - CCSDS PDF confirmed reachable by HEAD request
  - ISO entry located via search

### Key observed points
- OAIS is clearly established as a reference-model context for archival information systems.
- Official or standards-adjacent entry points are available.
- A fuller second-pass extraction is still needed before using detailed quotations.

### Relevance to MDAMS
- Useful as conceptual framing for ingest, packaging, archival information objects, lifecycle thinking, and preservation-aware workflows.
- Helps position MDAMS as informed by preservation concepts without claiming complete OAIS implementation.

### Likely research linkage
- RQ on conceptual architecture.
- RQ on how archival/preservation thinking shapes system boundaries and workflow design.

---

## 4. Crockett, Emily. *“DAM Becky, Look at That Asset”: Digital Asset Management in Cultural Heritage Institutions.* 2020.
- Repository page: https://cdr.lib.unc.edu/concern/masters_papers/v118rk462
- DOI: https://doi.org/10.17615/4vcy-ym50
- Download URL discovered: https://cdr.lib.unc.edu/downloads/k643b662s?locale=en
- Type: academic master's paper / cultural heritage DAM study
- Access status:
  - bibliographic page fetched successfully
  - PDF download reachable
  - current environment did not produce clean extracted text from PDF in this pass

### Key observed points
- Confirmed title, author, year, and DOI.
- Directly focused on digital asset management in cultural heritage institutions.
- High-probability relevance even before full-text extraction because of exact thematic overlap.

### Relevance to MDAMS
- Likely one of the most directly relevant research sources for positioning MDAMS in relation to museum/cultural-heritage DAM practice.
- Should help compare general DAM expectations with the preservation/interoperability emphases in MDAMS.

### Likely research linkage
- RQ on domain problem framing.
- RQ on why cultural heritage DAM differs from generic enterprise DAM.

### Follow-up needed
- Do a dedicated PDF text-extraction pass to capture argument structure, scope, and conclusions.

---

## 5. Padfield et al. *Practical applications of IIIF as a building block towards a digital National Collection.*
- URL: https://zenodo.org/records/6884885
- Type: project/final report page
- Access status: directly fetched and verified

### Key observed points
- Describes a project exploring how IIIF can connect digitised content across institutional silos.
- Highlights opportunities for describing, presenting, and re-using digital resources at scale.
- Frames IIIF as part of a realistic and sustainable approach to connecting large numbers of collections at national scale.
- Notes lower barriers to uptake, re-interpretation, and collaborative online resource building.

### Relevance to MDAMS
- Strong practice-oriented evidence that IIIF has cross-institutional value beyond a narrow viewer integration story.
- Useful for arguing that interoperability and reuse are practical institutional concerns, not only technical ideals.
- Can help nuance the relationship between presentation, aggregation, reuse, and discovery.

### Likely research linkage
- RQ on interoperability strategy.
- RQ on why standards-based access matters for future reuse and cross-collection integration.

---

## 6. *The Practical Applications of IIIF: Project Outcomes and Future Directions.*
- URL: https://zenodo.org/records/6587144
- Type: project outcomes / webinar materials repository
- Access status: directly fetched and verified

### Key observed points
- Provides demonstrator-oriented evidence of IIIF use in practice.
- Includes examples such as Simple Site, Simple Discovery, IIIF Collection Explorer, Tudor Paintings Research Project/InvenioRDM repository pilot, and Digirati Manifest Editor.
- Indicates an ecosystem of tools and implementations rather than isolated specification use.

### Relevance to MDAMS
- Valuable as practice evidence showing what kinds of real systems and demonstrators grow around IIIF.
- Supports positioning MDAMS not as an isolated prototype but as part of a broader standards-driven ecosystem.
- Useful when discussing future extensibility and ecosystem compatibility.

### Likely research linkage
- RQ on implementation/ecosystem context.
- RQ on how prototype choices relate to existing IIIF-enabled infrastructures and tools.

---

## 7. PREMIS Editorial Committee. *PREMIS Data Dictionary for Preservation Metadata, version 3.0.*
- Standard page noted in document: http://www.loc.gov/standards/premis
- Type: preservation metadata standard / data dictionary
- Access status: user-provided PDF extracted and partially reviewed

### Key observed points
- Version 3.0, dated June 2015 and revised November 2015.
- Structured around Objects, Events, Agents, and Rights.
- Includes implementation considerations and special topics such as format information, environment, fixity, integrity, authenticity, and digital signatures.
- Presents itself as a practical resource for implementing preservation metadata.

### Relevance to MDAMS
- Very strong fit for preservation-oriented conceptual modeling.
- Especially relevant to ingest processing, event recording, fixity workflows, derivative-generation provenance, and rights-related preservation context.
- Helps describe current MDAMS mechanisms as proto-preservation-metadata structures even if the system does not yet implement PREMIS formally.

### Likely research linkage
- RQ on preservation-oriented system design.
- RQ on how operational workflow events can be represented or interpreted as preservation metadata.

---

## 8. NISO. *ANSI/NISO Z39.87-2006 (R2017): Data Dictionary – Technical Metadata for Digital Still Images.*
- Type: technical metadata standard
- Access status: user-provided PDF extracted and partially reviewed

### Key observed points
- Defines metadata elements for raster digital images.
- Explicitly supports development, exchange, interpretation, interoperability, long-term management, and continuing access.
- Includes early sections on digital object information, identifiers, file size, format designation, and format registry.

### Relevance to MDAMS
- Strong candidate standard for image technical metadata profiling in the prototype.
- Particularly relevant where the system manages still-image masters, derivatives, and image-serving workflows.
- Could inform a more disciplined ingest metadata profile for digital still images.

### Likely research linkage
- RQ on asset-level technical metadata design.
- RQ on how image-focused technical metadata can be standardized in a museum-oriented prototype.

---

## 9. Moore, Rountrey, and Scates Kettler (eds.). *3D Data Creation to Curation: Community Standards for 3D Data Preservation.*
- Type: community standard / edited volume
- Access status: user-provided PDF extracted and partially reviewed

### Key observed points
- Covers best practices, management and storage, metadata requirements, legal issues, and access for 3D data.
- Explicitly addresses metadata requirements in relation to the digital asset life cycle.
- Treats 3D preservation as an end-to-end workflow from creation to curation.

### Relevance to MDAMS
- Not yet a core standard for the current prototype scope, but highly useful as a future-facing expansion reference.
- Shows how preservation, metadata, rights, access, and lifecycle concerns can be integrated for complex media types.

### Likely research linkage
- RQ on future extensibility.
- RQ on how the current prototype might generalize beyond still-image-centered workflows.

---

## Current Working Observations Across Sources

The current annotated set suggests a coherent external framing for MDAMS:
- **IIIF** supports access representation and interoperability;
- **BagIt** supports structured preservation/export packaging;
- **OAIS** supports conceptual lifecycle and archival framing;
- **PREMIS** supports preservation metadata entities and event-oriented modeling;
- **NISO Z39.87** supports technical metadata for digital still images;
- **Cultural-heritage DAM literature** supports domain-specific problem framing;
- **IIIF practice reports** help move the argument from standards theory to institutional applicability;
- **CS3DP** offers a future-facing expansion perspective for more complex asset types.

## Immediate Next Steps

1. Extract full text or at least substantial sections from Crockett's paper.
2. Add at least 2 more directly relevant academic sources on museum/cultural-heritage DAMS.
3. Add at least 1 methodology source for design science / prototype research.
4. Convert these entries later into citation-style bibliography plus thematic synthesis notes.
