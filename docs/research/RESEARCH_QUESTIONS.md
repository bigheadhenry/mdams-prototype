# MDAMS Research Questions

## Main Research Question

How can a museum-oriented digital asset management prototype be designed and implemented so that it supports a coherent core workflow from ingest to access and preservation-oriented export while remaining technically feasible as a modern web prototype?

## Sub-questions

### RQ1. Domain and Scope
What are the essential functional and conceptual requirements of a museum digital asset management prototype, and how should its scope be constrained at the prototype stage?

### RQ2. Conceptual Modeling
What should be treated as the system's primary managed object, and how should assets, files, metadata, derivatives, access representations, and export packages relate to one another?

### RQ3. Architecture and Implementation
How can a modern web architecture support the core MDAMS workflow, including ingest, metadata extraction, fixity generation, asynchronous processing, IIIF access, and export?

### RQ4. Standards Alignment
How can ideas or components from standards/frameworks such as IIIF, OAIS, and BagIt be integrated into a lightweight prototype without overloading the system with premature complexity?

### RQ5. Prototype Validation
What criteria should be used to evaluate whether the prototype successfully demonstrates the core value of a museum digital asset management system?

### RQ6. Trade-offs and Limitations
What tensions emerge between domain fidelity, engineering simplicity, and prototype feasibility during implementation, and how should these be discussed as research findings rather than treated only as technical debt?

## Working Hypothesis

A useful MDAMS prototype does not need to implement a full production-scale museum information system. It is sufficient, at the prototype stage, to establish a stable and explainable core chain linking:

- ingest,
- metadata/fixity processing,
- derivative/access generation,
- IIIF-facing presentation,
- and preservation-oriented export.

## Notes

These questions are intentionally framed to support both:
- architectural/design reflection;
- and future formal academic writing.

They may be refined as the prototype evolves.
