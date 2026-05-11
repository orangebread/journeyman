# Journeyman Artifact Contract

Every YAML artifact includes:

- `schema_version`
- `artifact_version`
- `created_at`
- `updated_at`
- `source_hash`
- `parent_artifact_versions`

Use `source_hash` as the SHA-256 hash of `requirements.raw.md`. For `parent_artifact_versions`, reference `requirements.raw.md` as `sha256:<hash>` and YAML parents by their current `artifact_version`.

## Required Phase 1 Files

- `requirements.raw.md`
- `context.yaml`
- `requirements.refined.yaml`
- `normalization.diff.yaml`
- `decisions.log.yaml`
- `statechart.happy.yaml` or one `artifact.*.yaml`
- `scenarios.yaml` for expanded statechart designs
- `statechart.full.yaml` for expanded statechart designs
- `handoffs.yaml` for expanded statechart designs
- `review.status.yaml`

## `context.yaml`

Required sections: `project_summary`, `codebase_pointers`, `related_artifacts`, `known_systems`, `known_actors`, `glossary`, `constraints`, and `out_of_scope`.

## `requirements.refined.yaml`

Required sections: `source_summary`, `request_type`, `recommended_artifact`, `recommendation_confidence`, `clarification_budget`, `scope_fence`, `requirements`, `negative_acceptance_criteria`, `unknowns`, `normalization_summary`, `dependencies_seed`, `handoffs_seed`, `glossary_updates`, and `decisions`.

Each requirement includes `id`, `text`, `evidence`, `source_ref`, `confidence`, and `decision_ref`. Evidence must be one of `explicit`, `inferred`, `assumed`, `unknown`, or `contradicted`.

`scope_fence` includes `primary_actor`, `start_trigger`, `terminal_outcome`, `non_goals`, `external_systems`, `success_criteria`, and `failure_definition`.

`unknowns` includes `blocking_now`, `safe_to_assume`, `design_risk`, `implementation_risk`, and `defer_until_code`.

## `normalization.diff.yaml`

Required sections: `raw_source_hash`, `added_inferences`, `renamed_terms`, `grouped_requirements`, `omitted_items`, `contradictions`, `assumptions_introduced`, and `requires_user_review`.

## `decisions.log.yaml`

Each decision includes `id`, `stage`, `mode`, `prompt`, `proposal`, `outcome`, `rationale`, `source_refs`, `reversible`, `auto_allowed`, `blocked_auto_reason`, and `created_at`.

## `statechart.happy.yaml`

Required sections: `id`, `title`, `actors`, `states`, `initial`, `transitions`, `terminal_states`, and `metadata`.

Every state has an entry condition. Every transition has `from`, `to`, `trigger`, and `expected_result`.

## `scenarios.yaml`

Required sections: `happy_path`, `high_priority`, `deferred`, and `rejected`.

Every high-priority scenario maps to at least one affected state or transition. Every deferred scenario includes a rationale.

## `statechart.full.yaml`

Use the same structural contract as `statechart.happy.yaml`. Add high-priority scenario transitions only when they keep the chart reviewable.

For actor-lane and event-passing review, states may include `lane`, transitions may include `scenario_refs` and `handoff_ref`, and `metadata.event_passes` may list event handoffs between actors or systems.

## `handoffs.yaml`

Required sections: `actors`, `systems`, `dependencies`, `handoffs`, and `accepted_risks`.

Every dependency includes `failure_path` or `accepted_risk`. Every handoff includes `owner`, `input_artifact`, `output_artifact`, and either `failure_transition` or `accepted_risk`.

## Alternative Artifacts

When `recommended_artifact` is not `statechart`, write one `artifact.*.yaml` with at least:

- `artifact_type`
- `rationale`
- artifact-specific body

The rationale must explain why a statechart is low-value for the request.
