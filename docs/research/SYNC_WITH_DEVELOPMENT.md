# Synchronization Mechanism Between Development Track and Research Track

## Purpose

This document defines how the MDAMS development project and the MDAMS research-writing subproject should stay synchronized.

The goal is to ensure that implementation work continuously produces research material, and that research framing continuously sharpens implementation priorities.

## Principle

Development and research should not be treated as two separate timelines.

Instead:
- development produces evidence;
- research organizes that evidence;
- research clarifies concepts and evaluation criteria;
- clarified concepts feed back into development decisions.

## Sync Rules

### Rule 1. Major implementation changes must leave a research trace
When a major technical or product decision is made, at least one of the following should be updated:
- `DESIGN_DECISIONS.md`
- `CONCEPT_MODEL.md`
- `STANDARDS_MAPPING.md`
- `EVALUATION_FRAMEWORK.md`
- `PAPER_OUTLINE.md`

Examples:
- redefining the primary managed object;
- changing ingest workflow semantics;
- changing IIIF generation logic;
- restructuring derivative handling;
- changing export/package scope.

### Rule 2. Each development milestone should be mappable to a research question
Before or after a milestone, ask:
- Which research question does this inform?
- Does this milestone provide evidence, clarification, or limitation?
- Should the result appear in the future paper as method, implementation, validation, or discussion?

### Rule 3. Demo validation is research evidence
Successful end-to-end demonstrations should be recorded not only as engineering success but also as validation evidence.

Examples:
- asset ingest completed end-to-end;
- fixity generation completed;
- IIIF manifest/viewer chain works;
- export package generated and inspected.

### Rule 4. Failures are also research material
Implementation failures, fragile integrations, and scope constraints should not disappear into chat logs.
They should feed:
- discussion;
- limitations;
- trade-off analysis;
- future work.

### Rule 5. Research framing should constrain feature expansion
When considering a new feature, ask:
- Does it strengthen the core research argument?
- Does it help validate the prototype's central workflow?
- Is it conceptually central, or only a peripheral product temptation?

If the answer is weak, the feature should probably not be prioritized.

## Recommended Operating Rhythm

### After a meaningful development session
Record:
- what changed;
- why it mattered;
- what it implies conceptually;
- whether it validates, complicates, or narrows the research argument.

### After a meaningful research clarification
Reflect into development:
- terminology updates;
- concept model adjustments;
- UI/API naming improvements;
- revised implementation priorities.

## Suggested Minimal Workflow

1. Development change occurs.
2. Check whether the change affects product meaning, architecture, workflow, or standards alignment.
3. If yes, update at least one research document.
4. If the change validates a core chain, record it as evidence.
5. If the change exposes a limitation, record it as discussion material.

## Current Priority for Synchronization

At the current stage, synchronization should especially focus on:
- defining the core managed object;
- clarifying the ingest-to-access workflow;
- documenting standards alignment boundaries;
- collecting validation evidence for the prototype's demonstrable core chain.
