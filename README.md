# Journeyman

Journeyman is a design-first statechart workbench. It helps turn rough user requirements into reviewable behavior artifacts before implementation.

The product is intentionally scoped to:

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

Start with the planning baseline:

- [Design-First Statechart Workbench Plan](docs/2026-05-11-design-first-statechart-workbench-plan.md)
- [Phase 1 Execution Brief](docs/phase-1-execution-brief.md)
- [Journeyman Skill](skills/journeyman/SKILL.md)

Agent and implementation rules live in:

- [AGENTS.md](AGENTS.md)

## Current Build Target

Build the skill-owned workflow with deterministic CLI support:

- skill-owned intake from raw prompt, file, stdin, or chat export
- immutable `requirements.raw.md`
- `context.yaml`
- `requirements.refined.yaml`
- `normalization.diff.yaml`
- `decisions.log.yaml`
- `statechart.happy.yaml` for statechart-worthy requests
- alternative artifact output for non-statechart requests
- `scenarios.yaml`, `statechart.full.yaml`, and `handoffs.yaml` for expanded statechart reviews
- CLI support for scaffolding, hashes, validation, artifact inspection, and the read-only local dashboard

Current proof fixtures cover:

- password reset or login recovery produces a useful happy-path statechart
- background export produces async dependency, failure-path, and handoff expansion
- commit-message rewrite is correctly declined as a statechart and routed to a better artifact

## Non-Goals

Do not build package maturity governance, Codex or Claude plugin packaging, runtime enforcement hooks, a formal intake application, dashboard editing, or broad dashboard scope before Phase 1 is proven.

## CLI Support

The CLI is deterministic support tooling, not the workflow owner:

```bash
./start.sh
journeyman init designs/password-reset
journeyman hash examples/expected/password-reset
journeyman validate examples/expected/password-reset
journeyman dashboard examples/expected/password-reset
journeyman dashboard examples/expected/password-reset --export tmp/review.html
```

`./start.sh` creates a repo-local `.venv` when needed, installs Journeyman in editable mode, validates the proof fixtures, chooses the next available port starting at `8765`, and launches the read-only dashboard. Use `./start.sh --check` to run setup and validation without starting the server.

The repo-local skill owns design interpretation and artifact authorship. The CLI must not infer requirements, choose state names, or generate design meaning in Phase 1.

The dashboard is read-only. It can display SVG statechart diagrams, happy and full charts, scenario coverage, handoffs, actor lanes, event passes, validation results, client-side filtering, browser polling for changed artifacts, and a static HTML review export.
