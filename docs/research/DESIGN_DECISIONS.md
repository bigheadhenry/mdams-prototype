# MDAMS Design Decisions Log

## Purpose

This file records important design and architecture decisions that should support both implementation continuity and future academic writing.

Each entry should ideally answer:
- What decision was made?
- Why was it made?
- What alternatives were considered?
- What are the implications?
- Which research question(s) does it inform?

---

## Decision Template

### Decision Title
- Date:
- Status: proposed / adopted / revised / deprecated
- Related modules:
- Related research question(s):

#### Context

#### Decision

#### Alternatives Considered

#### Rationale

#### Implications

---

## Initial Seed Decisions

### Core product emphasis on the demoable core workflow
- Date: 2026-03-08
- Status: adopted
- Related modules: overall product scope, workflow design, docs
- Related research question(s): RQ1, RQ5, RQ6

#### Context
The project already contains multiple substantial functions, but prototype energy is limited. Expanding the feature surface further would make the system harder to explain, stabilize, and evaluate.

#### Decision
Prioritize stabilization of the demoable core workflow rather than broadening the feature set.

#### Alternatives Considered
- Continue expanding product breadth.
- Invest first in UI beautification.
- Focus first on peripheral business modules.

#### Rationale
A research-capable prototype must demonstrate a coherent core value chain. Without a stable core workflow, both implementation and academic explanation become fragmented.

#### Implications
- The project roadmap should prefer core-chain reliability over feature breadth.
- Evaluation should focus on end-to-end workflow success.
- New features should be judged by whether they strengthen the core research argument.

---

### Conservative configuration refactor policy
- Date: 2026-03-08
- Status: adopted
- Related modules: docker-compose, .env.example, deployment
- Related research question(s): RQ3, RQ6

#### Context
The project had partially externalized configuration but still contained important hardcoded runtime values. However, the IIIF/Manifest/Nginx pathing structure was known to be fragile.

#### Decision
Externalize configuration conservatively while avoiding casual changes to IIIF/Manifest/Nginx behavior.

#### Alternatives Considered
- Aggressive full configuration cleanup.
- Immediate restructuring of public URL logic.
- Path/layout simplification without validating implications.

#### Rationale
The prototype needed better configurability, but stability of the demonstrable workflow had higher priority than config purity.

#### Implications
- Configuration improvements should be incremental and validated.
- Architecture documentation should distinguish between intentional design and fragile implementation constraints.

---

### Treat the digital asset as the primary managed object
- Date: 2026-03-09
- Status: proposed
- Related modules: product model, API semantics, UI structure, research docs
- Related research question(s): RQ1, RQ2, RQ5

#### Context
The implementation contains files, metadata, derivatives, manifests, and export-oriented outputs, but without a sufficiently explicit product-level object hierarchy, the system risks appearing file-centric or feature-fragmented.

#### Decision
Use the digital asset as the main conceptual product object, and organize files, metadata, processing results, IIIF-facing representations, and export packages around it.

#### Alternatives Considered
- Treat uploaded file as the main object.
- Treat collection or museum object as the immediate primary object.
- Keep object semantics implicit and implementation-driven.

#### Rationale
An asset-centered framing best matches the prototype's current strengths: ingest, processing, metadata association, access representation, and export. It also offers the clearest bridge between engineering design and museum-domain interpretation.

#### Implications
- Future documentation and UI naming should gradually become more asset-centered.
- API and workflow descriptions should distinguish asset-level operations from file-level operations.
- This decision helps stabilize the conceptual model for both implementation and academic writing.

---

### Adopt selective standards alignment rather than full standards implementation
- Date: 2026-03-09
- Status: adopted
- Related modules: IIIF integration, export design, research framing
- Related research question(s): RQ4, RQ6

#### Context
The prototype draws value from standards and frameworks such as IIIF, OAIS, and BagIt, but a prototype-stage system cannot sustainably implement every standard in exhaustive depth.

#### Decision
Adopt a role-aware standards strategy: implement directly where practical value is high, borrow concepts where conceptual framing is useful, and explicitly document current boundaries.

#### Alternatives Considered
- Pursue stronger formal compliance claims early.
- Avoid explicit standards framing and present the system as generic DAM functionality.
- Attempt broad standards coverage before stabilizing the core workflow.

#### Rationale
Selective standards alignment preserves domain relevance without overwhelming the prototype with premature complexity. It also provides a stronger and more honest research argument.

#### Implications
- IIIF should remain the clearest access-layer implementation target.
- OAIS should be discussed mainly as a conceptual reference model.
- BagIt should remain a practical packaging/export reference.
- Research writing should distinguish implemented features from conceptual influence.

---

### Development and research must be synchronized as parallel tracks
- Date: 2026-03-09
- Status: adopted
- Related modules: docs, roadmap, research workflow
- Related research question(s): RQ5, RQ6

#### Context
The project is now mature enough that implementation work generates research material, but without explicit synchronization, key knowledge risks remaining scattered across chat, code, and memory.

#### Decision
Treat development and research-writing as synchronized parallel tracks. Major changes in implementation should produce research traces, and research clarification should feed back into development priorities and terminology.

#### Alternatives Considered
- Postpone writing until the prototype is mostly complete.
- Keep academic reflection separate from implementation records.
- Write only a final summary after development stabilizes.

#### Rationale
Parallel synchronization reduces knowledge loss, improves conceptual clarity, and increases the eventual quality of thesis/paper output.

#### Implications
- Development milestones should map to research questions and evidence types.
- Design rationale should be captured while decisions are fresh.
- Validation and failure events should be recorded not only as engineering facts but also as research material.
