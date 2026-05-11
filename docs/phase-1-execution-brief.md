# Phase 1 Execution Brief

Use this brief when beginning implementation. The full planning baseline remains [docs/2026-05-11-design-first-statechart-workbench-plan.md](2026-05-11-design-first-statechart-workbench-plan.md).

## Objective

Build the smallest skill-owned, file-based Journeyman workflow that proves two claims:

1. A statechart-worthy request can produce a useful happy-path chart.
2. A non-statechart request can be correctly declined and routed to a better artifact.

Do not build a formal intake application, dashboard editing, broad dashboard scope, plugin packaging, cross-agent portability, runtime enforcement hooks, or multi-actor visualization in Phase 1.

The repo-local Journeyman skill owns intake, routing, behavioral/domain modeling, refinement, statechart or alternative artifact generation, and acceptance checkpoints. CLI code is deterministic support only: scaffold, hash, validate, inspect artifacts, and launch the read-only local dashboard viewer.

## Required Inputs

The skill-owned workflow must support at least:

- raw prompt or chat source copied into `requirements.raw.md`
- file source copied verbatim into `requirements.raw.md`
- stdin source copied verbatim into `requirements.raw.md`

Chat-export intake can be stubbed behind a contract if needed, but the artifact shape must account for source references. The CLI should not implement an intake command in Phase 1 because interpretation ownership belongs to the skill.

## Required Artifacts

For each design run, create a folder like:

```text
designs/<run-id>/
  requirements.raw.md
  context.yaml
  requirements.refined.yaml
  normalization.diff.yaml
  decisions.log.yaml
  statechart.happy.yaml
  review.status.yaml
```

For non-statechart requests, replace `statechart.happy.yaml` with the selected alternative artifact, such as:

```text
artifact.checklist.yaml
artifact.acceptance-matrix.yaml
artifact.sequence.yaml
artifact.data-contract.yaml
```

## First Commands

Preferred command shape:

```bash
journeyman init designs/password-reset
# Use the Journeyman skill to populate artifacts from examples/requests/password-reset.md.
journeyman hash designs/password-reset
journeyman validate designs/password-reset
journeyman dashboard designs/password-reset

journeyman init designs/commit-message
# Use the Journeyman skill to populate artifacts from examples/requests/commit-message.md.
journeyman hash designs/commit-message
journeyman validate designs/commit-message
journeyman dashboard designs/commit-message
```

Naming can change during implementation, but the behavior should not.

## Required Fixtures

Create these before claiming Phase 1 complete:

- `examples/requests/password-reset.md`
- `examples/requests/commit-message.md`
- `examples/expected/password-reset/`
- `examples/expected/commit-message/`

The password-reset fixture proves the statechart path. The commit-message fixture proves the escape hatch.

## Minimum Validation Gates

The validator must fail when:

- `requirements.raw.md` is missing or its hash no longer matches downstream source references.
- `normalization.diff.yaml` is missing.
- a requirement lacks `evidence` or `source_ref`.
- `scope_fence` is incomplete and the design is not marked partial.
- `blocking_now` unknowns remain in an accepted design.
- `auto` is used for a banned sensitive category.
- a statechart-worthy request has unreachable states.
- a non-statechart request lacks a recommended alternative artifact and rationale.
- downstream artifacts reference stale parent artifact versions.

## First Implementation Order

1. Define artifact schemas.
2. Create the Journeyman skill workflow and artifact contract reference.
3. Implement CLI scaffolding and source/parent hash checks.
4. Implement validation.
5. Implement the read-only local dashboard viewer.
6. Add the two proof fixtures authored through the skill workflow.
7. Verify the fixtures with CLI validation.

Do not expand beyond the read-only local dashboard viewer until these steps are working.

## Completion Definition

Phase 1 is complete only when:

- both proof fixtures exist,
- generated artifacts pass validation,
- the statechart fixture produces a reviewable happy path,
- the escape-hatch fixture declines statechart output,
- every AI or rule-based decision is inspectable in `decisions.log.yaml`,
- and a reviewer can understand what changed from raw input to refined requirements.
