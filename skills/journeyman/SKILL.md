---
name: journeyman
description: Structured design-first workflow for turning rough product, feature, or system requests into Journeyman artifacts. Use when Codex needs to perform raw intake, request-type routing, evidence-labeled requirement refinement, behavioral/domain modeling, happy-path statechart generation or a justified alternative artifact, scenario/handoff planning, dashboard review preparation, or accepted design-contract creation.
---

# Journeyman

Use this skill as the primary operator surface for Journeyman. The skill owns design interpretation and artifact authorship. CLI tools only scaffold, hash, validate, inspect, and launch the read-only dashboard.

## Operating Boundary

- Do not treat Journeyman as an intake application, package-maturity system, plugin-packaging project, runtime enforcement layer, or cross-agent portability framework.
- Preserve raw user input verbatim in `requirements.raw.md`; never rewrite it during refinement.
- Keep the workflow file-based and git-friendly.
- Use `yes | no | auto` as stage decisions. `auto` can only make reversible, low-risk decisions inside one stage and must stop at the stage boundary with a decision summary.
- Never use `auto` for security, authorization, privacy, billing, payment, entitlement, destructive action, data retention/deletion, external ownership, user-visible commitments, SLAs, legal, compliance, or regulatory decisions.
- Use the support CLI for deterministic checks: `journeyman init`, `journeyman hash`, `journeyman validate`, and `journeyman dashboard`.

Read `references/artifact-contract.md` when creating or reviewing artifacts.

## Workflow

1. **Raw Intake**
   - Capture the exact user request into `requirements.raw.md`.
   - Create or update `context.yaml` with known systems, actors, glossary, constraints, codebase pointers, related artifacts, and out-of-scope boundaries.
   - If starting from an empty folder, run `journeyman init <design-dir>` first.

2. **Routing And Refinement**
   - Classify the request before shaping it: stateful workflow, simple content/task transform, CRUD/data model, integration/handoff flow, debugging/regression, planning/spec request, or other.
   - Recommend one primary artifact: statechart, sequence diagram, dependency DAG, checklist, data contract, or acceptance matrix.
   - Write `requirements.refined.yaml` with evidence-labeled requirements, source references, confidence, scope fence, negative acceptance criteria, unknowns, dependencies seed, handoffs seed, glossary updates, and decisions.
   - Write `normalization.diff.yaml` showing what was added, inferred, renamed, grouped, omitted, contradicted, or assumed.

3. **Behavioral And Domain Modeling**
   - Keep domain concepts tidy: actors, systems, states, events/triggers, transitions, artifacts, dependencies, handoffs, glossary terms, assumptions, and unknowns must be explicit.
   - Treat inferred dependencies, handoffs, and glossary terms as unverified seeds with confidence labels.
   - Ask at most the configured clarification budget, default three, and only when the answer changes happy path, ownership, acceptance criteria, or external dependency behavior.

4. **Selected Artifact**
   - For stateful workflows, write `statechart.happy.yaml` first. Keep it small, legible, and focused on the successful path.
   - For non-statechart work, do not force a chart. Write one `artifact.*.yaml` with `artifact_type`, `rationale`, and artifact-specific content.
   - Write every stage choice into `decisions.log.yaml`.

5. **Scenario And Handoff Expansion**
   - For statechart-worthy designs that have passed happy-path review, write `scenarios.yaml`, `statechart.full.yaml`, and `handoffs.yaml`.
   - Add only high-priority scenarios. Map each high-priority scenario to at least one state or transition.
   - Keep owner, input artifact, output artifact, dependency, and failure path explicit for every handoff.
   - Ensure every handoff id is referenced by at least one full-chart transition `handoff_ref`.

6. **Validation And Review**
   - Run `journeyman validate <design-dir>` before claiming a design is ready for review.
   - Run `journeyman dashboard <design-dir>` to launch the read-only local viewer.
   - Use `journeyman dashboard <design-dir> --export <path>` when a static read-only review HTML file is needed.
   - A design can be accepted only when validation passes and `review.status.yaml` records the accepted or revision-required state and design phase.

## Phase 1 Proof Cases

- Password reset or login recovery must prove the statechart path.
- Background export or report generation must prove async dependency and handoff expansion.
- Commit-message rewrite must prove the escape hatch by declining statechart output and producing a better artifact.
- Treat task success, artifact generated, artifact validated, evaluation evidence, and repo integration as separate claims.
