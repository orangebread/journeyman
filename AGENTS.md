# Agent Instructions

This repository builds Journeyman, a design-first statechart workbench.

Before substantial planning, design, or implementation work, restate the request and state execution mode. Use `main-agent only` unless delegated work is explicitly allowed and concretely justified.

## Product Boundary

Journeyman is not a package-maturity, plugin-packaging, formal intake application, or cross-agent portability project. Do not recreate the old `.behavior` package governance system, generated Codex/Claude surfaces, dual lifecycle state machines, `packageReady`, `workflowProven`, runtime enforcement hooks, or an application shell unless the user explicitly changes scope.

The product workflow is:

```text
raw user request
  -> raw intake and request-type routing
  -> interpreted requirements with evidence labels
  -> happy-path statechart or justified alternative
  -> high-priority scenario expansion
  -> dependency and handoff mapping
  -> visual dashboard review
  -> accepted design contract
```

Treat [docs/2026-05-11-design-first-statechart-workbench-plan.md](docs/2026-05-11-design-first-statechart-workbench-plan.md) as the planning baseline. Treat [docs/phase-1-execution-brief.md](docs/phase-1-execution-brief.md) as the first implementation handoff.

## Phase 1 Only Until Proven

Build Phase 1 first. Do not start dashboard editing, broad dashboard scope, multi-actor visualization, plugin packaging, formal intake application, or broad framework work until Phase 1 evidence exists.

The primary operator surface is the repo-local Journeyman Codex skill in [skills/journeyman/SKILL.md](skills/journeyman/SKILL.md). The skill owns intake, routing, behavioral/domain modeling, refinement, statechart or alternative artifact generation, and acceptance checkpoints. CLI code may scaffold, hash, validate, inspect artifacts, and launch the read-only dashboard only; it must not independently generate core interpretations.

Phase 1 must implement or stub with durable contracts:

- file, stdin, or chat-export intake that writes immutable `requirements.raw.md`
- `context.yaml`
- `requirements.refined.yaml`
- `normalization.diff.yaml`
- `decisions.log.yaml`
- `statechart.happy.yaml` when a statechart is recommended
- an alternative artifact when a statechart is not recommended
- validation for source hashes, scope fence, evidence labels, unresolved blocking unknowns, sensitive `auto` misuse, reachability, and stale artifact versions

Phase 1 is not complete until there is evidence for both:

- a statechart-worthy request produces a useful happy-path chart
- a non-statechart request is correctly declined and routed to a better artifact

Use password reset or login recovery as the primary statechart proof case. Use commit-message rewrite as the escape-hatch proof case.

## Intake Rules

Raw user input is source evidence. Preserve it verbatim. Do not overwrite `requirements.raw.md`; create a new version when the user intentionally replaces the source.

Refinement must produce a normalization diff that records what AI added, inferred, renamed, grouped, omitted, contradicted, or assumed.

Every extracted requirement must carry:

- `explicit`
- `inferred`
- `assumed`
- `unknown`
- `contradicted`

Do not treat inferred dependencies, handoffs, or glossary terms as verified truth. Seed them with confidence labels and require later validation.

Use a configurable clarification budget, defaulting to three blocking questions. Ask only when the answer changes the happy path, ownership, acceptance criteria, or external dependency behavior.

## `auto` Safety

`auto` may batch reversible, low-risk decisions inside one stage. It must stop at the stage boundary with a decision summary.

`auto` is not allowed for decisions that determine:

- security or authorization behavior
- privacy behavior
- billing, payment, or entitlement behavior
- destructive actions
- data retention or deletion
- external system ownership
- user-visible commitments, guarantees, or SLAs
- legal, compliance, or regulatory obligations

Those decisions require explicit `yes` approval or must remain unresolved.

## Artifact Discipline

All generated artifacts should include:

- `schema_version`
- `artifact_version`
- `created_at`
- `updated_at`
- `source_hash`
- `parent_artifact_versions`

When an upstream artifact changes, downstream artifacts are stale until regenerated or explicitly accepted as still valid.

Dashboard work must be read-only until artifact schemas and validation are stable. Do not create a second source of truth in the UI.

## Verification

Before claiming Phase 1 complete, verify at minimum:

- raw intake preserves source text and stable hash
- request-type routing can recommend statechart and non-statechart artifacts
- statechart output has reachable states and valid transitions
- non-statechart output includes a rationale and alternative artifact
- every `auto` decision is logged and outside banned categories
- no accepted design has unresolved `blocking_now` unknowns
- stale downstream artifacts are detected after upstream changes

For later phases, keep the same skill-owned boundary. Scenario expansion, handoff mapping, full charts, actor lanes, event passes, and dashboard filtering must remain artifact-backed and read-only until a real case justifies editing or parallel-region complexity.

Keep task/lane success, artifact generated, artifact validated, evaluation evidence, and repo integration separate.
