# Design-First Statechart Workbench Plan

Status: planning baseline
Date: 2026-05-11
Current repo role: skill-owned Phase 1 implementation baseline

## Executive Summary

The project should reset from "Behavior-First Skill Packaging" to a smaller product: an AI-assisted design workbench that turns rough requirements into reviewable behavior artifacts.

The target workflow is:

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

The assessment is mostly right: the current repo is solving maturity governance for portable skill packages, while the desired product is requirements-to-statechart design support. Those are different products. The planning baseline should preserve the useful discipline around artifacts and proof, but cut package lifecycle machinery, cross-agent packaging, invariant metadata, and runtime enforcement until the core workflow proves useful.

## Decision

Build a product track around "requirements -> statechart -> viewer" as a structured Codex skill workflow supported by deterministic CLI tools and a read-only dashboard viewer.

Implementation path: skill-owned workflow in this repo. The repo-local Journeyman skill owns intake, routing, behavioral/domain modeling, refinement, statechart or alternative artifact generation, and acceptance checkpoints.

Executable code is limited to CLI support tools and the dashboard viewer. There is no formal intake application. The CLI may scaffold, hash, validate, inspect artifacts, and launch the read-only dashboard; it must not independently generate core interpretations.

## Assessment Review

### Adopt

- The product should be scoped as an AI-assisted design tool, not a skill-package maturity system.
- `yes | no | auto` is the right decision primitive.
- The workflow should move through explicit checkpoints: requirements, happy path, scenario completion, dashboard review.
- Statecharts should be a primary deliverable because they are visual, reviewable, and close to executable behavior.
- The dashboard should close the loop by letting users inspect the system through states, transitions, scenarios, dependencies, and handoffs.
- The MVP should be skill-owned, file-based, and git-friendly.
- The first dashboard should be read-only.
- Raw user input must be preserved verbatim and never overwritten by AI refinement.
- Requirement evidence labels, unknown classification, and `auto` safety rules should be first-class.

### Revise

- Do not make statecharts universal. The tool should recommend a statechart by default for stateful workflows, but allow `N/A` with a rationale and alternative artifact.
- Do not allow `auto` to run end-to-end without checkpoints. `auto` should operate inside one stage at a time and produce a decision summary before advancing.
- Do not model dependencies and handoffs as arbitrary nested statechart complexity in the MVP. Model them as transition annotations plus a handoff index.
- Do not wait until Phase 3 to validate the output visually. Phase 1 can use export-to-Stately or a simple static render before the dashboard exists.
- Treat request-type routing as the first gate inside intake, not a late field in the refined requirements artifact.
- Use a configurable clarification budget with a default of three blocking questions, not a hard global cap.
- Evaluate both sides of the product promise: producing useful statecharts and correctly declining low-value statecharts.

### Reject

- "Cut everything else" is directionally right for implementation scope, but the useful validation lessons should carry forward. The new product still needs deterministic checks for artifact integrity, traceability, and unresolved high-priority ambiguity.
- "One weekend" is plausible for a spike, not for a durable product baseline. Treat Phase 1 as a narrow proof slice, not a finished MVP.

## Product Thesis

Teams lose behavior truth between vague requirements and implementation. The workbench should help an AI ask better questions, turn answers into explicit stateful behavior, and make missing scenarios visible before code is written.

The product is successful if it catches design ambiguity, missing transitions, ownerless handoffs, and unhandled high-priority scenarios earlier than a normal prose spec or chat-only design pass.

## Primary Users

- Product-minded engineers designing features before implementation.
- Solo builders using AI as a requirements and design partner.
- Reviewers validating whether a proposed feature flow has complete states, transitions, dependencies, and handoffs.
- Agents or AI workflows that need a structured design contract before writing code.

## Non-Goals

- No cross-agent package portability in the MVP.
- No Claude or Codex plugin packaging in the MVP. A focused repo-local Codex skill is allowed as the operator workflow.
- No runtime tool-call enforcement hooks in the MVP.
- No formal intake application in the MVP.
- No generic workflow engine in the MVP.
- No fully automated design approval.
- No visual editor in the first dashboard.
- No attempt to force every task into a statechart.

## Core Modes

Each stage supports:

- `yes`: ask the user to approve or revise the proposed artifact before continuing.
- `no`: skip the stage and record why it was skipped.
- `auto`: let AI proceed within the stage, but log decisions and stop at the stage boundary with a summary.

Default mode by stage:

| Stage | Default | Reason |
| --- | --- | --- |
| Raw intake and requirement interpretation | `yes` | This is where vague terms, contradictions, and missing constraints matter most. |
| Happy statechart | `yes` | This is the primary product artifact and should be reviewed. |
| Scenario completion | `auto` with summary | AI can draft likely edge cases, but user should approve the resulting priority list. |
| Dependency and handoff mapping | `yes` | Owner, system boundary, and failure responsibility are easy to hallucinate. |
| Dashboard review | `yes` | The dashboard exists to support explicit acceptance. |

`auto` must never silently advance across all stages. It can batch decisions inside a stage, then produce a checkpoint summary.

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

## Product Workflow

### Stage 1: Raw Intake, Routing, And Requirement Interpretation

Input:

- `requirements.raw.md`
- optional stdin or chat-export import
- `context.yaml`

Output:

- `requirements.refined.yaml`
- `normalization.diff.yaml`
- `decisions.log.yaml`

Responsibilities:

- Capture raw input verbatim. `requirements.raw.md` is immutable after capture unless the user explicitly replaces the source and increments the intake version.
- Classify the request type before refinement:
  - stateful workflow
  - simple content or task transform
  - CRUD or data model
  - integration or handoff flow
  - debugging or regression
  - planning or spec request
- Recommend the primary artifact before shaping the request: statechart, sequence diagram, dependency DAG, checklist, data contract, or acceptance matrix.
- Record what the AI normalized, renamed, grouped, inferred, omitted, or contradicted in `normalization.diff.yaml`.
- Extract goals, actors, user jobs, constraints, acceptance criteria, assumptions, open questions, contradictions, and non-goals.
- Tag every extracted requirement as `explicit`, `inferred`, `assumed`, `unknown`, or `contradicted`.
- Maintain a scope fence with primary actor, start trigger, terminal outcome, non-goals, external systems, success criteria, and failure definition.
- Classify terms that need precision, such as "fast," "secure," "simple," "done," "approved," or "failed."
- Maintain a glossary of domain terms and ambiguous terms introduced during intake.
- Classify unknowns as `blocking_now`, `safe_to_assume`, `design_risk`, `implementation_risk`, or `defer_until_code`.
- Seed likely dependencies and handoffs early, with confidence labels, without treating them as verified truth.
- Produce blocking clarification questions only when the missing answer would change the happy path, ownership, acceptance criteria, or external dependency behavior.

Success criteria:

- Every major requirement has a source reference and evidence label.
- Open questions are classified by urgency and impact.
- The tool states whether a statechart is recommended or whether another artifact is more appropriate before generating downstream artifacts.
- No happy-path statechart can be accepted unless the scope fence is complete or explicitly marked partial.
- Every `auto` intake decision is reversible, logged, and outside the banned categories.

### Stage 2: Happy Path Statechart

Input:

- `requirements.refined.yaml`

Output:

- `statechart.happy.yaml`
- optional rendered preview

Responsibilities:

- Model the intended successful path first.
- Keep the happy path small and legible.
- Identify actors and systems involved in each transition.
- Avoid edge-case explosion at this stage.

Success criteria:

- The happy path can be read without implementation context.
- Every state has an entry condition.
- Every transition has a trigger and expected result.
- The chart has a clear terminal or handoff state.

### Stage 3: High-Priority Scenario Completion

Input:

- `requirements.refined.yaml`
- `statechart.happy.yaml`

Output:

- `scenarios.yaml`
- `statechart.full.yaml`
- updated `decisions.log.yaml`

Responsibilities:

- Add only high-priority scenarios:
  - invalid input
  - permission denied
  - timeout
  - cancellation
  - retry
  - dependency unavailable
  - stale state
  - duplicate submission
  - handoff failure
  - partial completion
- Link each scenario to affected states and transitions.
- Mark deferred scenarios explicitly rather than hiding them.

Success criteria:

- Every high-priority scenario maps to at least one state or transition.
- Every deferred scenario has a rationale.
- The full chart remains reviewable and does not become a generic exception catalog.

### Stage 4: Dependencies And Handoffs

Input:

- `statechart.full.yaml`
- `scenarios.yaml`

Output:

- `handoffs.yaml`
- annotated `statechart.full.yaml`

Responsibilities:

- Identify actor-to-actor, service-to-service, and system-to-human handoffs.
- Attach handoff metadata to transitions.
- Capture dependency failure paths without overloading the statechart.

Transition metadata should support:

- `actor`
- `owner`
- `dependency`
- `input_artifact`
- `output_artifact`
- `precondition`
- `postcondition`
- `timeout`
- `failure_transition`
- `scenario_refs`

Success criteria:

- No handoff is ownerless.
- Every external dependency has an unavailable or failed path, or an explicit `accepted_risk` entry.
- Every handoff has an input and output artifact, even if the artifact is a user action or event.

### Stage 5: Dashboard Review

Input:

- all generated artifacts

Output:

- local review UI
- accepted or revision-required decision

Responsibilities:

- Render the happy and full statecharts.
- Show requirements-to-state traceability.
- Show scenario coverage.
- Show handoffs and owner boundaries.
- Show unresolved questions and accepted risks.
- Show diff between happy and full charts.

Initial dashboard should be read-only. Editing can come later after the artifact model stabilizes.

## Statechart Suitability Rules

Statechart recommended when the request includes:

- lifecycle states
- modes
- UI screens with behavior changes
- async jobs
- approvals
- retries
- cancellations
- multi-actor flows
- external dependencies
- agent loops
- stateful user journeys

Statechart not recommended when the request is mostly:

- pure CRUD with no meaningful lifecycle
- stateless data transformation
- one-shot content generation
- simple compute
- static document formatting
- linear checklist with no branching

When statechart is not recommended, the tool should produce one of:

- sequence diagram
- dependency DAG
- checklist
- data contract
- acceptance matrix

The user can still force a statechart, but the tool should label it as likely low-value.

## Artifact Contract

Recommended file layout:

```text
design/
  requirements.raw.md
  context.yaml
  requirements.refined.yaml
  normalization.diff.yaml
  statechart.happy.yaml
  scenarios.yaml
  handoffs.yaml
  statechart.full.yaml
  decisions.log.yaml
  review.status.yaml
```

All artifacts should include:

- `schema_version`
- `artifact_version`
- `created_at`
- `updated_at`
- `source_hash`
- `parent_artifact_versions`

When requirements change mid-design, downstream artifacts become stale unless their `parent_artifact_versions` match the current upstream artifact versions.

`review.status.yaml` also records `phase`. Accepted designs must declare the phase being accepted. Phase 2+ statechart reviews require `scenarios.yaml`, `statechart.full.yaml`, and `handoffs.yaml` plus matching parent artifact references.

### `context.yaml`

Required sections:

- `project_summary`
- `codebase_pointers`
- `related_artifacts`
- `known_systems`
- `known_actors`
- `glossary`
- `constraints`
- `out_of_scope`

`context.yaml` exists to prevent the intake step from treating a chat prompt as the only source of truth when a codebase, prior spec, glossary, or related feature already exists.

### `requirements.refined.yaml`

Required sections:

- `source_summary`
- `request_type`
- `recommended_artifact`
- `recommendation_confidence`
- `clarification_budget`
- `scope_fence`
- `requirements`
- `negative_acceptance_criteria`
- `unknowns`
- `normalization_summary`
- `dependencies_seed`
- `handoffs_seed`
- `glossary_updates`
- `decisions`

Each requirement should include:

- `id`
- `text`
- `evidence`: `explicit`, `inferred`, `assumed`, `unknown`, or `contradicted`
- `source_ref`
- `confidence`
- `decision_ref`

`scope_fence` should include:

- `primary_actor`
- `start_trigger`
- `terminal_outcome`
- `non_goals`
- `external_systems`
- `success_criteria`
- `failure_definition`

`unknowns` should include:

- `blocking_now`
- `safe_to_assume`
- `design_risk`
- `implementation_risk`
- `defer_until_code`

`dependencies_seed` and `handoffs_seed` should include confidence labels and should be treated as prompts for later validation, not verified truth.

### `normalization.diff.yaml`

Required sections:

- `raw_source_hash`
- `added_inferences`
- `renamed_terms`
- `grouped_requirements`
- `omitted_items`
- `contradictions`
- `assumptions_introduced`
- `requires_user_review`

This artifact is the trust boundary between raw input and AI interpretation.

### `decisions.log.yaml`

Each decision should include:

- `id`
- `stage`
- `mode`
- `prompt`
- `proposal`
- `outcome`
- `rationale`
- `source_refs`
- `reversible`
- `auto_allowed`
- `blocked_auto_reason`
- `created_at`

### `statechart.happy.yaml` and `statechart.full.yaml`

Use an XState-compatible structure where practical, but keep a stable internal schema if exact XState serialization becomes awkward.

Required sections:

- `id`
- `title`
- `actors`
- `states`
- `initial`
- `transitions`
- `terminal_states`
- `metadata`

### `scenarios.yaml`

Required sections:

- `happy_path`
- `high_priority`
- `deferred`
- `rejected`

Each scenario should include priority, reason, affected states, affected transitions, and verification notes.

### `handoffs.yaml`

Required sections:

- `actors`
- `systems`
- `dependencies`
- `handoffs`
- `accepted_risks`

## Dashboard Requirements

Phase 3 dashboard capabilities:

- Local server.
- Reloads when artifact files change.
- Renders statechart diagrams.
- Shows happy vs full chart diff.
- Shows decisions beside generated artifacts.
- Shows unresolved questions and accepted risks.
- Shows scenario coverage by state and transition.
- Shows dependency and handoff lanes.
- Exports a static review bundle.

Candidate stack:

- Vite + React for the local viewer.
- XState v5-compatible model where it provides useful graph semantics.
- Stately tooling as a compatibility and visualization reference.
- Chokidar-style file watching for local artifact refresh.

Implementation-time verification required:

- Confirm current XState and Stately APIs against official docs before coding.
- Confirm whether Stately visualization can be embedded or whether the MVP should render its own graph.
- Keep the internal artifact schema independent enough that visualization library changes do not break the product model.

Reference docs checked for planning context:

- Stately/XState docs: https://stately.ai/docs
- Stately Studio docs: https://stately.ai/docs/studio
- Vite docs: https://vite.dev/guide/

## Validation Gates

Validation should prove artifact integrity, not package maturity.

Minimum deterministic checks:

- `requirements.raw.md` exists and has a stable source hash.
- `requirements.refined.yaml` has source-backed requirements, a request-type routing result, and a complete scope fence or explicit partial status.
- `normalization.diff.yaml` exists and references the current raw source hash.
- Every requirement has id, text, evidence label, source reference, confidence, and decision reference.
- No accepted design has unresolved `blocking_now` unknowns.
- `auto` is not used for security, privacy, billing, destructive action, data retention, external ownership, user-visible commitment, legal, compliance, or regulatory decisions.
- Every `auto` decision is reversible and logged.
- Every happy-path state is reachable from the initial state.
- Every non-terminal happy-path state has at least one outgoing transition.
- Every high-priority scenario maps to a state or transition.
- Every dependency has a failure path or accepted risk.
- Every handoff has owner, input artifact, output artifact, and failure transition or accepted risk.
- Every handoff dependency, failure path, and failure transition cross-references the full chart.
- Every full-chart `handoff_ref` points to a known handoff, and every handoff is attached to at least one transition.
- Every artifact version matches its declared parent artifact versions.
- Every artifact includes its required parent references.
- Non-statechart requests produce a recommended alternative artifact with a rationale.

## Evaluation Plan

The old `workflowProven` idea should be replaced with product-level proof:

> Given the same messy real requirement, the workbench produces a more complete and reviewable behavior design than a baseline chat-only design pass.

Evaluation cases should be real and small:

1. Password reset or login recovery flow: primary proof that statechart output improves behavior design.
2. Background export or report generation flow: async/dependency proof case.
3. Rewrite commit message into conventional format: escape-hatch proof that the tool can decline a statechart and recommend a better artifact.

Metrics:

- missing state count
- missing transition count
- unresolved ambiguity surfaced
- high-priority scenario coverage
- ownerless handoff count
- dependency failure coverage
- correct artifact recommendation
- incorrect statechart recommendation count
- reviewer time to understand flow
- reviewer confidence rating

Phase 1 does not need automated judging. A structured before/after review is enough if the evidence is committed.

## Phased Plan

### Phase 0: Repo Decision And Product Naming

Goal: prevent wrong-shape carryover.

Tasks:

- Use this repo as the Phase 1 implementation baseline.
- Pick product name.
- Decide initial artifact folder convention.
- Preserve this plan as the planning baseline.

Exit criteria:

- There is one implementation repo.
- The implementation repo has no package-maturity lifecycle baggage.

### Phase 1: Requirements To Happy Statechart

Goal: prove the core AI design loop before building dashboard infrastructure.

Tasks:

- Use the Journeyman skill to accept raw prompt, file, stdin, or chat-export source and write immutable `requirements.raw.md`.
- Use the Journeyman skill to generate or update `context.yaml`.
- Use the Journeyman skill to generate `requirements.refined.yaml`.
- Use the Journeyman skill to generate `normalization.diff.yaml`.
- Ask or log `yes | no | auto` decisions for requirement interpretation.
- Use the Journeyman skill to generate `statechart.happy.yaml` when statechart is recommended.
- Use the Journeyman skill to generate an alternative artifact when statechart is not recommended.
- Use CLI support to validate, hash-check, and display the selected artifact in the dashboard.
- Commit one primary statechart before/after case and one escape-hatch case.

Exit criteria:

- A real messy request produces a reviewable happy-path chart.
- A non-statechart request is correctly declined and routed to a better artifact.
- User can inspect every AI decision.
- At least one reviewer can identify whether the happy path matches intent.

### Phase 2: Scenario Expansion And Handoff Mapping

Goal: add the behavior that makes the design useful for implementation readiness.

Implementation status: supported by `scenarios.yaml`, `statechart.full.yaml`, `handoffs.yaml`, deterministic validation, the password-reset proof fixture, the background-export async dependency fixture, and committed evaluation artifacts.

Tasks:

- Generate `scenarios.yaml`.
- Generate `handoffs.yaml`.
- Expand to `statechart.full.yaml`.
- Add deterministic validators.
- Add before/after evaluation on at least two real cases.

Exit criteria:

- High-priority scenarios are mapped to states or transitions.
- External dependencies and handoffs have owners and failure paths.
- Validation fails on ownerless handoffs and unmapped high-priority scenarios.

### Phase 3: Read-Only Dashboard

Goal: make the artifacts inspectable without reading YAML.

Implementation status: supported by the local read-only dashboard viewer for raw source, routing, requirements, SVG happy/full chart diagrams, happy-to-full diff, scenario coverage, handoffs, actor lanes, event passes, validation results, browser polling for changed artifacts, and static HTML export.

Tasks:

- Build local dashboard server.
- Watch artifact files.
- Render happy and full charts.
- Show decision log, questions, scenario coverage, handoffs, and accepted risks.
- Show happy-to-full diff.

Exit criteria:

- A user can review a design without opening raw YAML.
- Dashboard exposes missing owners, missing failure paths, and unresolved blocking questions.
- Dashboard is read-only and does not introduce a second source of truth.

### Phase 4: Multi-Actor And Advanced Handoffs

Goal: support more complex systems without breaking MVP simplicity.

Implementation status: bounded support exists for actor lanes, event-passing metadata, and read-only client-side filtering. Parallel-region support remains gated until a real case requires it.

Tasks:

- Add swimlane-oriented views.
- Add parallel-region support only if real cases require it.
- Add event-passing representation between actors.
- Add dashboard filtering by actor, system, dependency, and scenario.

Exit criteria:

- Multi-actor flows stay legible.
- Parallel or actor-model complexity is justified by real examples.

## Implementation Guidance

Start with the skill-owned file workflow plus deterministic CLI support, not a formal intake application.

Preferred early command shape:

```bash
journeyman init ./design
# Use the Journeyman skill to populate and revise artifacts.
journeyman hash ./design
journeyman validate ./design
journeyman dashboard ./design
```

Early implementation modules:

- `skills/journeyman`
- `validate`
- `dashboard`

The skill workflow should remain readable and portable as instructions, but Phase 1 does not require a provider-integrated application runtime. Artifact schemas should not depend on one provider.

Iteration support should be built into the artifact model from the start:

- Skill-applied feedback records a delta decision instead of overwriting prior decisions.
- Changed upstream artifacts increment `artifact_version`.
- Downstream stale artifacts are marked `needs_regeneration` until regenerated or explicitly accepted as still valid.

## Risks And Failure Modes

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Statechart forced onto low-state work | Noisy artifacts, user distrust | Add suitability gate and alternative artifact path. |
| `auto` invents requirements | False design truth | Restrict `auto` to one stage and require decision log summary. |
| `auto` decides sensitive behavior | Security, privacy, billing, or ownership harm | Ban `auto` for sensitive categories and fail validation if violated. |
| Raw request gets normalized away | Loss of user intent and auditability | Keep raw source immutable and require normalization diff. |
| Requirements change but charts stay stale | Implementation starts from obsolete design | Version artifacts and invalidate downstream outputs on parent mismatch. |
| Domain terms drift across stages | Inconsistent state names and acceptance criteria | Maintain glossary in `context.yaml` and refined requirements. |
| Dashboard becomes editor too early | Source-of-truth drift | Keep dashboard read-only until schema stabilizes. |
| Handoffs make charts unreadable | Visual overload | Use transition annotations plus separate handoff index. |
| AI asks too many questions | Workflow fatigue | Ask only blocking or behavior-changing questions. |
| Evaluation becomes subjective theater | False proof | Commit before/after artifacts and score concrete omissions. |
| CLI starts generating design meaning | Drift between skill workflow and executable behavior | Keep interpretation, routing, and modeling owned by the skill in Phase 1. |

## What To Carry Forward From This Repo

- Artifact discipline.
- Separation between generated claims and proven workflow value.
- Deterministic validation mindset.
- Explicit handling of policy-only vs enforceable claims, translated here into "accepted risk" vs "validated artifact integrity."
- Evidence that fixture-only scoring is not product proof.

## What To Cut

- `.behavior` package maturity structure.
- Dual lifecycle state machines.
- `packageReady` and `workflowProven` as product states.
- Codex and Claude generated package surfaces.
- Plugin validation.
- Runtime enforcement claims.
- Video-export fixture as primary evidence.
- Acceptance files that only rerun validators without proving design value.

## Open Decisions

1. Whether the static review export should remain a single HTML file or become a multi-file bundle with extracted assets.
2. Whether `context.yaml` should be hand-authored, generated from repo inspection, or both.
3. How chat-export intake should preserve source references.
4. Whether glossary updates require explicit approval or can be `auto` when reversible.

## Recommended Next Step

Implement Phase 1 only with the Journeyman skill as workflow owner and CLI/dashboard as deterministic support:

- raw requirement intake
- request-type routing
- requirement interpretation with `yes | no | auto`
- immutable raw source and normalization diff
- evidence labels, unknown classification, scope fence, and negative acceptance criteria
- happy-path statechart generation
- alternative artifact generation for non-statechart requests
- decision log
- validation for reachability, unresolved blocking questions, sensitive `auto` misuse, and stale artifact versions
- one primary statechart before/after evaluation case
- one escape-hatch evaluation case

Do not build dashboard editing, broad scenario/handoff visualization, or a second source of truth until Phase 1 proves that statechart-as-output is valuable for real requests.
