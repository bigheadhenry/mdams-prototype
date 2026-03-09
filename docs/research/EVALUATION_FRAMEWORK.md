# MDAMS Evaluation Framework (Draft)

## Purpose

This document defines how the prototype should be evaluated as a research-oriented system, not merely as a codebase with implemented features.

## Evaluation Position

The prototype should be evaluated primarily on whether it demonstrates a coherent and explainable core workflow for museum digital asset management.

The goal is not to prove institutional completeness. The goal is to prove that the prototype successfully establishes and validates the essential chain from ingest to access and preservation-oriented export.

## Evaluation Dimensions

### 1. Workflow Coherence
Can the prototype support a logically complete workflow rather than isolated features?

Questions:
- Can a digital resource be ingested as a meaningful managed object?
- Does the workflow connect ingest, analysis, access, and export?
- Are the stages conceptually understandable?

### 2. Asset-Centered Modeling
Does the prototype behave as a digital asset management system rather than a loose file utility?

Questions:
- Is there a clear primary managed object?
- Are files, metadata, derivatives, and access representations meaningfully related?
- Does the product language reflect the model?

### 3. Metadata and Integrity Support
Does the prototype provide meaningful support for metadata and fixity-oriented management?

Questions:
- Can technical/descriptive metadata be captured or extracted?
- Can checksums/fixity information be generated and viewed?
- Are these treated as part of the asset lifecycle?

### 4. Access Capability
Does the prototype provide a viable access layer for digital objects?

Questions:
- Can access representations be generated?
- Can IIIF-related outputs be produced and viewed?
- Is access clearly distinguished from preservation/original storage?

### 5. Preservation-Oriented Export
Does the prototype demonstrate awareness of packaging/export for long-term management?

Questions:
- Can the system produce an exportable package?
- Is the package conceptually tied to preservation-oriented workflows?
- Is export treated as part of the product architecture, not an afterthought?

### 6. Technical Feasibility and Stability
Is the prototype sufficiently stable to support demonstration and analysis?

Questions:
- Can the main workflow run end-to-end?
- Are asynchronous processes observable enough to debug?
- Is deployment/configuration manageable?

### 7. Research Value
Does the prototype generate useful insights beyond implementation itself?

Questions:
- Does it expose meaningful design trade-offs?
- Does it help clarify how standards can be adapted in a prototype?
- Does it reveal useful boundaries between product ambition and implementation reality?

## Evidence Types

The following can serve as evaluation evidence:
- successful end-to-end demo runs;
- generated manifests and packages;
- screenshots of workflow states;
- architecture and workflow diagrams;
- logged design decisions;
- records of failures and their implications;
- comparison between intended and actual workflow behavior.

## Current Priority

At the current stage, the strongest evaluation target is the demonstrable core chain:

1. ingest;
2. metadata/fixity processing;
3. derivative/access generation;
4. IIIF-facing access;
5. export/package generation.

If this chain is stable and explainable, the prototype already has strong research value even without full enterprise-level coverage.
