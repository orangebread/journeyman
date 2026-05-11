from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set

from .artifacts import (
    DECISIONS_FILE,
    FULL_STATECHART_FILE,
    HANDOFFS_FILE,
    NORMALIZATION_FILE,
    REFINED_FILE,
    REVIEW_FILE,
    SCENARIOS_FILE,
    STATECHART_FILE,
    ArtifactError,
    alternative_artifacts,
    expected_parent_version,
    is_present,
    load_yaml,
    missing_required_files,
    source_hash,
    yaml_artifact_paths,
)

EVIDENCE_LABELS = {"explicit", "inferred", "assumed", "unknown", "contradicted"}
SENSITIVE_AUTO_CATEGORIES = {
    "security",
    "authorization",
    "privacy",
    "billing",
    "payment",
    "entitlement",
    "destructive_action",
    "data_retention",
    "data_deletion",
    "external_system_ownership",
    "user_visible_commitment",
    "sla",
    "legal",
    "compliance",
    "regulatory",
}
SCOPE_FENCE_FIELDS = [
    "primary_actor",
    "start_trigger",
    "terminal_outcome",
    "non_goals",
    "external_systems",
    "success_criteria",
    "failure_definition",
]
DECISION_FIELDS = [
    "id",
    "stage",
    "mode",
    "prompt",
    "proposal",
    "outcome",
    "rationale",
    "source_refs",
    "reversible",
    "auto_allowed",
    "blocked_auto_reason",
    "created_at",
]
COMMON_METADATA_FIELDS = [
    "schema_version",
    "artifact_version",
    "created_at",
    "updated_at",
    "source_hash",
    "parent_artifact_versions",
]


@dataclass
class ValidationResult:
    errors: List[str]
    warnings: List[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_design(design_dir: Path) -> ValidationResult:
    design_dir = design_dir.resolve()
    errors: List[str] = []
    warnings: List[str] = []

    if not design_dir.exists():
        return ValidationResult([f"missing design directory: {design_dir}"], warnings)

    missing = missing_required_files(design_dir)
    errors.extend(f"missing required artifact: {name}" for name in missing)
    if missing:
        return ValidationResult(errors, warnings)

    try:
        raw_hash = source_hash(design_dir)
    except ArtifactError as exc:
        return ValidationResult([str(exc)], warnings)

    yaml_docs: Dict[str, Dict[str, Any]] = {}
    for path in yaml_artifact_paths(design_dir):
        try:
            data = load_yaml(path)
        except ArtifactError as exc:
            errors.append(str(exc))
            continue
        yaml_docs[path.name] = data
        _validate_common_metadata(path.name, data, raw_hash, errors)

    if errors:
        return ValidationResult(errors, warnings)

    refined = yaml_docs.get(REFINED_FILE, {})
    normalization = yaml_docs.get(NORMALIZATION_FILE, {})
    decisions = yaml_docs.get(DECISIONS_FILE, {})
    review = yaml_docs.get(REVIEW_FILE, {})

    _validate_normalization(normalization, raw_hash, errors)
    _validate_requirements(refined, review, errors)
    _validate_decisions(decisions, errors)
    _validate_parent_versions(design_dir, yaml_docs, raw_hash, errors)
    _validate_selected_artifact(design_dir, refined, yaml_docs, errors)

    statechart_path = design_dir / STATECHART_FILE
    if statechart_path.exists():
        _validate_statechart(yaml_docs.get(STATECHART_FILE, {}), errors, STATECHART_FILE)
    full_statechart_path = design_dir / FULL_STATECHART_FILE
    if full_statechart_path.exists():
        _validate_statechart(yaml_docs.get(FULL_STATECHART_FILE, {}), errors, FULL_STATECHART_FILE)
    if SCENARIOS_FILE in yaml_docs:
        chart = yaml_docs.get(FULL_STATECHART_FILE) or yaml_docs.get(STATECHART_FILE) or {}
        _validate_scenarios(yaml_docs.get(SCENARIOS_FILE, {}), chart, errors)
    if HANDOFFS_FILE in yaml_docs:
        _validate_handoffs(yaml_docs.get(HANDOFFS_FILE, {}), errors)

    return ValidationResult(errors, warnings)


def validate_hashes(design_dir: Path) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    try:
        raw_hash = source_hash(design_dir)
    except ArtifactError as exc:
        return ValidationResult([str(exc)], warnings)

    for path in yaml_artifact_paths(design_dir):
        try:
            data = load_yaml(path)
        except ArtifactError as exc:
            errors.append(str(exc))
            continue
        actual = data.get("source_hash")
        if not is_present(actual):
            errors.append(f"{path.name}: source_hash is required")
        elif actual != raw_hash:
            errors.append(f"{path.name}: source_hash {actual!r} does not match requirements.raw.md")
        parents = data.get("parent_artifact_versions") or {}
        if not isinstance(parents, Mapping):
            errors.append(f"{path.name}: parent_artifact_versions must be a mapping")
            continue
        for parent, declared in parents.items():
            expected = expected_parent_version(design_dir, str(parent), raw_hash)
            if expected is None:
                errors.append(f"{path.name}: parent artifact {parent!r} is missing")
            elif str(declared) != expected:
                errors.append(
                    f"{path.name}: parent {parent!r} declares {declared!r}, expected {expected!r}"
                )
    return ValidationResult(errors, warnings)


def _validate_common_metadata(name: str, data: Mapping[str, Any], raw_hash: str, errors: List[str]) -> None:
    for field in COMMON_METADATA_FIELDS:
        if field not in data:
            errors.append(f"{name}: missing metadata field {field}")
    if data.get("source_hash") != raw_hash:
        errors.append(f"{name}: source_hash does not match requirements.raw.md")
    if "parent_artifact_versions" in data and not isinstance(data.get("parent_artifact_versions"), Mapping):
        errors.append(f"{name}: parent_artifact_versions must be a mapping")


def _validate_normalization(data: Mapping[str, Any], raw_hash: str, errors: List[str]) -> None:
    if data.get("raw_source_hash") != raw_hash:
        errors.append(f"{NORMALIZATION_FILE}: raw_source_hash does not match requirements.raw.md")
    for field in [
        "added_inferences",
        "renamed_terms",
        "grouped_requirements",
        "omitted_items",
        "contradictions",
        "assumptions_introduced",
        "requires_user_review",
    ]:
        if field not in data:
            errors.append(f"{NORMALIZATION_FILE}: missing {field}")


def _validate_requirements(refined: Mapping[str, Any], review: Mapping[str, Any], errors: List[str]) -> None:
    requirements = refined.get("requirements")
    if not isinstance(requirements, Sequence) or isinstance(requirements, (str, bytes)):
        errors.append(f"{REFINED_FILE}: requirements must be a list")
        return
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, Mapping):
            errors.append(f"{REFINED_FILE}: requirement {index} must be a mapping")
            continue
        evidence = requirement.get("evidence")
        if evidence not in EVIDENCE_LABELS:
            errors.append(f"{REFINED_FILE}: requirement {requirement.get('id', index)!r} has invalid evidence")
        if not is_present(requirement.get("source_ref")):
            errors.append(f"{REFINED_FILE}: requirement {requirement.get('id', index)!r} missing source_ref")

    scope = refined.get("scope_fence") or {}
    if not isinstance(scope, Mapping):
        errors.append(f"{REFINED_FILE}: scope_fence must be a mapping")
        return
    missing_scope = [field for field in SCOPE_FENCE_FIELDS if not is_present(scope.get(field))]
    partial = bool(scope.get("partial")) or review.get("status") == "partial"
    if missing_scope and not partial:
        errors.append(f"{REFINED_FILE}: incomplete scope_fence without partial status: {', '.join(missing_scope)}")

    unknowns = refined.get("unknowns") or {}
    blocking = unknowns.get("blocking_now") if isinstance(unknowns, Mapping) else None
    if review.get("status") == "accepted" and is_present(blocking):
        errors.append(f"{REFINED_FILE}: accepted design has unresolved blocking_now unknowns")


def _validate_decisions(decisions: Mapping[str, Any], errors: List[str]) -> None:
    entries = decisions.get("decisions", [])
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        errors.append(f"{DECISIONS_FILE}: decisions must be a list")
        return
    for index, decision in enumerate(entries):
        if not isinstance(decision, Mapping):
            errors.append(f"{DECISIONS_FILE}: decision {index} must be a mapping")
            continue
        decision_id = decision.get("id", index)
        for field in DECISION_FIELDS:
            if field not in decision:
                errors.append(f"{DECISIONS_FILE}: decision {decision_id!r} missing {field}")
        if "source_refs" in decision and not is_present(decision.get("source_refs")):
            errors.append(f"{DECISIONS_FILE}: decision {decision_id!r} must include source_refs")
        if decision.get("mode") != "auto":
            continue
        category = str(decision.get("category") or decision.get("sensitive_category") or "").strip()
        if category in SENSITIVE_AUTO_CATEGORIES:
            errors.append(f"{DECISIONS_FILE}: auto decision {decision_id!r} uses banned category {category!r}")
        if decision.get("auto_allowed") is not True:
            errors.append(f"{DECISIONS_FILE}: auto decision {decision_id!r} is not explicitly auto_allowed")
        if decision.get("reversible") is not True:
            errors.append(f"{DECISIONS_FILE}: auto decision {decision_id!r} is not reversible")


def _validate_parent_versions(
    design_dir: Path,
    yaml_docs: Mapping[str, Mapping[str, Any]],
    raw_hash: str,
    errors: List[str],
) -> None:
    for name, data in yaml_docs.items():
        parents = data.get("parent_artifact_versions") or {}
        if not isinstance(parents, Mapping):
            continue
        for parent, declared in parents.items():
            expected = expected_parent_version(design_dir, str(parent), raw_hash)
            if expected is None:
                errors.append(f"{name}: parent artifact {parent!r} is missing")
            elif str(declared) != expected:
                errors.append(f"{name}: parent {parent!r} declares {declared!r}, expected {expected!r}")


def _validate_selected_artifact(
    design_dir: Path,
    refined: Mapping[str, Any],
    yaml_docs: Mapping[str, Mapping[str, Any]],
    errors: List[str],
) -> None:
    recommended = str(refined.get("recommended_artifact") or "").strip()
    has_statechart = (design_dir / STATECHART_FILE).exists()
    alternatives = alternative_artifacts(design_dir)

    if has_statechart and alternatives:
        errors.append("design has both statechart.happy.yaml and artifact.*.yaml outputs")

    if recommended == "statechart":
        if not has_statechart:
            errors.append(f"{REFINED_FILE}: recommended statechart but {STATECHART_FILE} is missing")
        return

    if not recommended:
        errors.append(f"{REFINED_FILE}: recommended_artifact is required")
        return

    if not has_statechart and not alternatives:
        errors.append("non-statechart request lacks an alternative artifact")
        return
    if alternatives:
        artifact = yaml_docs.get(alternatives[0].name, {})
        if not is_present(artifact.get("rationale")):
            errors.append(f"{alternatives[0].name}: missing rationale for non-statechart recommendation")
        if not is_present(artifact.get("artifact_type")):
            errors.append(f"{alternatives[0].name}: missing artifact_type")


def _validate_statechart(statechart: Mapping[str, Any], errors: List[str], artifact_name: str) -> None:
    for field in ["id", "title", "actors", "states", "initial", "transitions", "terminal_states", "metadata"]:
        if field not in statechart:
            errors.append(f"{artifact_name}: missing {field}")
    states = _state_ids(statechart.get("states"))
    initial = statechart.get("initial")
    terminal_states = set(_as_list(statechart.get("terminal_states")))
    transitions = statechart.get("transitions")

    if not states:
        errors.append(f"{artifact_name}: no states defined")
        return
    if initial not in states:
        errors.append(f"{artifact_name}: initial state {initial!r} is not defined")
        return
    if not isinstance(transitions, Sequence) or isinstance(transitions, (str, bytes)):
        errors.append(f"{artifact_name}: transitions must be a list")
        return

    outgoing: Dict[str, List[str]] = defaultdict(list)
    for index, transition in enumerate(transitions):
        if not isinstance(transition, Mapping):
            errors.append(f"{artifact_name}: transition {index} must be a mapping")
            continue
        source = transition.get("from")
        target = transition.get("to")
        if source not in states:
            errors.append(f"{artifact_name}: transition {index} has unknown from state {source!r}")
        if target not in states:
            errors.append(f"{artifact_name}: transition {index} has unknown to state {target!r}")
        if source in states and target in states:
            outgoing[str(source)].append(str(target))
        if not is_present(transition.get("trigger")):
            errors.append(f"{artifact_name}: transition {index} missing trigger")
        if not is_present(transition.get("expected_result")):
            errors.append(f"{artifact_name}: transition {index} missing expected_result")

    reachable = _reachable(str(initial), outgoing)
    for state in sorted(states - reachable):
        errors.append(f"{artifact_name}: unreachable state {state!r}")
    for state in sorted(states - terminal_states):
        if not outgoing.get(state):
            errors.append(f"{artifact_name}: non-terminal state {state!r} has no outgoing transition")


def _validate_scenarios(scenarios: Mapping[str, Any], chart: Mapping[str, Any], errors: List[str]) -> None:
    for field in ["happy_path", "high_priority", "deferred", "rejected"]:
        if field not in scenarios:
            errors.append(f"{SCENARIOS_FILE}: missing {field}")
    states = _state_ids(chart.get("states"))
    transitions = _transition_refs(chart.get("transitions"))
    high_priority = scenarios.get("high_priority", [])
    if not isinstance(high_priority, Sequence) or isinstance(high_priority, (str, bytes)):
        errors.append(f"{SCENARIOS_FILE}: high_priority must be a list")
        return
    for index, scenario in enumerate(high_priority):
        if not isinstance(scenario, Mapping):
            errors.append(f"{SCENARIOS_FILE}: high_priority scenario {index} must be a mapping")
            continue
        scenario_id = scenario.get("id", index)
        affected_states = set(_as_list(scenario.get("affected_states")))
        affected_transitions = set(_as_list(scenario.get("affected_transitions")))
        if not affected_states and not affected_transitions:
            errors.append(f"{SCENARIOS_FILE}: high_priority scenario {scenario_id!r} must map to a state or transition")
        for state in affected_states:
            if state not in states:
                errors.append(f"{SCENARIOS_FILE}: scenario {scenario_id!r} references unknown state {state!r}")
        for transition in affected_transitions:
            if transition not in transitions:
                errors.append(f"{SCENARIOS_FILE}: scenario {scenario_id!r} references unknown transition {transition!r}")
    deferred = scenarios.get("deferred", [])
    if isinstance(deferred, Sequence) and not isinstance(deferred, (str, bytes)):
        for index, scenario in enumerate(deferred):
            if isinstance(scenario, Mapping) and not is_present(scenario.get("rationale")):
                errors.append(f"{SCENARIOS_FILE}: deferred scenario {scenario.get('id', index)!r} missing rationale")


def _validate_handoffs(handoffs: Mapping[str, Any], errors: List[str]) -> None:
    for field in ["actors", "systems", "dependencies", "handoffs", "accepted_risks"]:
        if field not in handoffs:
            errors.append(f"{HANDOFFS_FILE}: missing {field}")
    dependencies = handoffs.get("dependencies", [])
    if isinstance(dependencies, Sequence) and not isinstance(dependencies, (str, bytes)):
        for index, dependency in enumerate(dependencies):
            if not isinstance(dependency, Mapping):
                errors.append(f"{HANDOFFS_FILE}: dependency {index} must be a mapping")
                continue
            dependency_id = dependency.get("id", index)
            if not is_present(dependency.get("failure_path")) and not is_present(dependency.get("accepted_risk")):
                errors.append(f"{HANDOFFS_FILE}: dependency {dependency_id!r} missing failure_path or accepted_risk")
    entries = handoffs.get("handoffs", [])
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        errors.append(f"{HANDOFFS_FILE}: handoffs must be a list")
        return
    for index, handoff in enumerate(entries):
        if not isinstance(handoff, Mapping):
            errors.append(f"{HANDOFFS_FILE}: handoff {index} must be a mapping")
            continue
        handoff_id = handoff.get("id", index)
        for field in ["owner", "input_artifact", "output_artifact"]:
            if not is_present(handoff.get(field)):
                errors.append(f"{HANDOFFS_FILE}: handoff {handoff_id!r} missing {field}")
        if not is_present(handoff.get("failure_transition")) and not is_present(handoff.get("accepted_risk")):
            errors.append(f"{HANDOFFS_FILE}: handoff {handoff_id!r} missing failure_transition or accepted_risk")


def _state_ids(states_value: Any) -> Set[str]:
    if isinstance(states_value, Mapping):
        return {str(key) for key in states_value.keys()}
    if isinstance(states_value, Sequence) and not isinstance(states_value, (str, bytes)):
        ids: Set[str] = set()
        for state in states_value:
            if isinstance(state, Mapping) and "id" in state:
                ids.add(str(state["id"]))
            elif isinstance(state, str):
                ids.add(state)
        return ids
    return set()


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value]
    return [str(value)]


def _transition_refs(transitions_value: Any) -> Set[str]:
    refs: Set[str] = set()
    if not isinstance(transitions_value, Sequence) or isinstance(transitions_value, (str, bytes)):
        return refs
    for transition in transitions_value:
        if not isinstance(transition, Mapping):
            continue
        if "id" in transition:
            refs.add(str(transition["id"]))
        source = transition.get("from")
        target = transition.get("to")
        if source is not None and target is not None:
            refs.add(f"{source}->{target}")
    return refs


def _reachable(initial: str, outgoing: Mapping[str, Iterable[str]]) -> Set[str]:
    seen: Set[str] = set()
    queue: deque[str] = deque([initial])
    while queue:
        state = queue.popleft()
        if state in seen:
            continue
        seen.add(state)
        for target in outgoing.get(state, []):
            if target not in seen:
                queue.append(target)
    return seen
