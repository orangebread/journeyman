from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from journeyman.cli import init_design, main
from journeyman.dashboard import render_dashboard_html
from journeyman.validator import validate_design, validate_hashes


ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(tmp_path: Path, name: str) -> Path:
    destination = tmp_path / name
    shutil.copytree(ROOT / "examples" / "expected" / name, destination)
    return destination


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_password_reset_fixture_validates_and_renders_dashboard(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")

    assert validate_design(design_dir).ok
    assert validate_hashes(design_dir).ok

    html = render_dashboard_html(design_dir)
    assert "Password Reset Happy Path" in html
    assert "No validation errors" in html
    assert "ready_to_sign_in" in html
    assert "SCN-003" in html
    assert "HND-001" in html
    assert "review-filter" in html
    assert "EVT-001" in html
    assert "statechart-diagram" in html
    assert "<svg" in html
    assert "pollDesignChanges" in html


def test_background_export_fixture_validates_async_dependency_expansion(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "background-export")

    assert validate_design(design_dir).ok
    assert validate_hashes(design_dir).ok

    html = render_dashboard_html(design_dir)
    assert "Background Export Full Review Chart" in html
    assert "HND-STORAGE" in html
    assert "SCN-004" in html
    assert "EVT-003" in html
    assert "statechart-diagram" in html


def test_commit_message_fixture_validates_escape_hatch(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "commit-message")

    assert validate_design(design_dir).ok
    html = render_dashboard_html(design_dir)

    assert "artifact.checklist.yaml" in html
    assert "one-shot content transform" in html
    assert "No validation errors" in html


def test_validator_rejects_missing_normalization_diff(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    (design_dir / "normalization.diff.yaml").unlink()

    result = validate_design(design_dir)

    assert not result.ok
    assert any("normalization.diff.yaml" in error for error in result.errors)


def test_validator_rejects_requirement_without_evidence(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    refined_path = design_dir / "requirements.refined.yaml"
    refined = load_yaml(refined_path)
    del refined["requirements"][0]["evidence"]
    write_yaml(refined_path, refined)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("invalid evidence" in error for error in result.errors)


def test_validator_rejects_requirement_without_required_fields(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    refined_path = design_dir / "requirements.refined.yaml"
    refined = load_yaml(refined_path)
    del refined["requirements"][0]["id"]
    del refined["requirements"][0]["text"]
    del refined["requirements"][0]["confidence"]
    del refined["requirements"][0]["decision_ref"]
    write_yaml(refined_path, refined)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("missing id" in error for error in result.errors)
    assert any("missing text" in error for error in result.errors)
    assert any("missing confidence" in error for error in result.errors)
    assert any("missing decision_ref" in error for error in result.errors)


def test_validator_rejects_incomplete_scope_fence_without_partial_status(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    refined_path = design_dir / "requirements.refined.yaml"
    refined = load_yaml(refined_path)
    refined["scope_fence"]["terminal_outcome"] = ""
    write_yaml(refined_path, refined)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("incomplete scope_fence" in error for error in result.errors)


def test_validator_rejects_accepted_design_with_blocking_unknowns(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    refined_path = design_dir / "requirements.refined.yaml"
    refined = load_yaml(refined_path)
    refined["unknowns"]["blocking_now"] = ["Need to know who owns the email provider."]
    write_yaml(refined_path, refined)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("blocking_now" in error for error in result.errors)


def test_validator_rejects_banned_auto_decision(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    decisions_path = design_dir / "decisions.log.yaml"
    decisions = load_yaml(decisions_path)
    decisions["decisions"].append(
        {
            "id": "DEC-BAD",
            "stage": "security-policy",
            "mode": "auto",
            "category": "security",
            "prompt": "Can auto decide account enumeration copy?",
            "proposal": "Pick a response.",
            "outcome": "accepted",
            "rationale": "Bad test fixture.",
            "source_refs": ["requirements.raw.md:L3"],
            "reversible": True,
            "auto_allowed": True,
            "blocked_auto_reason": "",
            "created_at": "2026-05-11T00:00:00+00:00",
        }
    )
    write_yaml(decisions_path, decisions)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("banned category" in error for error in result.errors)


def test_validator_rejects_unreachable_state(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    chart_path = design_dir / "statechart.happy.yaml"
    chart = load_yaml(chart_path)
    chart["states"].append({"id": "unreachable", "entry_condition": "No incoming transition."})
    chart["terminal_states"].append("unreachable")
    write_yaml(chart_path, chart)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("unreachable state" in error for error in result.errors)


def test_validator_rejects_stale_parent_artifact_version(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    chart_path = design_dir / "statechart.happy.yaml"
    chart = load_yaml(chart_path)
    chart["parent_artifact_versions"]["requirements.refined.yaml"] = "0"
    write_yaml(chart_path, chart)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("declares '0', expected '1'" in error for error in result.errors)


def test_validator_rejects_missing_required_parent_artifact_version(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    chart_path = design_dir / "statechart.happy.yaml"
    chart = load_yaml(chart_path)
    chart["parent_artifact_versions"] = {}
    write_yaml(chart_path, chart)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("missing required parent artifact 'requirements.refined.yaml'" in error for error in result.errors)


def test_validator_requires_phase_two_expansion_artifacts(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    (design_dir / "scenarios.yaml").unlink()
    (design_dir / "statechart.full.yaml").unlink()
    (design_dir / "handoffs.yaml").unlink()
    review_path = design_dir / "review.status.yaml"
    review = load_yaml(review_path)
    review["parent_artifact_versions"] = {"statechart.happy.yaml": "1"}
    write_yaml(review_path, review)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("phase 2 statechart review requires scenarios.yaml" in error for error in result.errors)


def test_hash_check_rejects_changed_raw_source(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "commit-message")
    raw_path = design_dir / "requirements.raw.md"
    raw_path.write_text(raw_path.read_text(encoding="utf-8") + "\nextra\n", encoding="utf-8")

    result = validate_hashes(design_dir)

    assert not result.ok
    assert any("source_hash" in error for error in result.errors)


def test_hash_check_rejects_empty_source_hashes_from_init(tmp_path: Path) -> None:
    design_dir = tmp_path / "new-design"
    init_design(design_dir)

    result = validate_hashes(design_dir)

    assert not result.ok
    assert any("source_hash is required" in error for error in result.errors)


def test_validator_rejects_incomplete_decision_entries(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    decisions_path = design_dir / "decisions.log.yaml"
    decisions = load_yaml(decisions_path)
    decisions["decisions"] = [{"id": "DEC-INCOMPLETE", "mode": "yes"}]
    write_yaml(decisions_path, decisions)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("DEC-INCOMPLETE" in error and "missing prompt" in error for error in result.errors)


def test_validator_rejects_multiple_selected_outputs(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    extra_artifact = {
        "schema_version": 1,
        "artifact_version": 1,
        "created_at": "2026-05-11T00:00:00+00:00",
        "updated_at": "2026-05-11T00:00:00+00:00",
        "source_hash": load_yaml(design_dir / "requirements.refined.yaml")["source_hash"],
        "parent_artifact_versions": {"requirements.refined.yaml": "1"},
        "artifact_type": "checklist",
        "rationale": "This should not coexist with a statechart output.",
        "items": [],
    }
    write_yaml(design_dir / "artifact.checklist.yaml", extra_artifact)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("both statechart.happy.yaml and artifact.*.yaml" in error for error in result.errors)


def test_validator_rejects_high_priority_scenario_without_mapping(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    scenarios_path = design_dir / "scenarios.yaml"
    scenarios = load_yaml(scenarios_path)
    scenarios["high_priority"][0]["affected_states"] = []
    scenarios["high_priority"][0]["affected_transitions"] = []
    write_yaml(scenarios_path, scenarios)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("must map to a state or transition" in error for error in result.errors)


def test_validator_rejects_dependency_without_failure_path_or_risk(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    handoffs_path = design_dir / "handoffs.yaml"
    handoffs = load_yaml(handoffs_path)
    handoffs["dependencies"][0]["failure_path"] = ""
    handoffs["dependencies"][0]["accepted_risk"] = ""
    write_yaml(handoffs_path, handoffs)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("missing failure_path or accepted_risk" in error for error in result.errors)


def test_validator_rejects_handoff_not_linked_from_full_chart(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    chart_path = design_dir / "statechart.full.yaml"
    chart = load_yaml(chart_path)
    for transition in chart["transitions"]:
        transition.pop("handoff_ref", None)
    write_yaml(chart_path, chart)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("is not attached to any statechart transition" in error for error in result.errors)


def test_validator_rejects_unknown_handoff_failure_transition(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    handoffs_path = design_dir / "handoffs.yaml"
    handoffs = load_yaml(handoffs_path)
    handoffs["handoffs"][0]["failure_transition"] = "T-MISSING"
    write_yaml(handoffs_path, handoffs)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("references unknown failure_transition" in error for error in result.errors)


def test_validator_rejects_ownerless_handoff(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    handoffs_path = design_dir / "handoffs.yaml"
    handoffs = load_yaml(handoffs_path)
    handoffs["handoffs"][0]["owner"] = ""
    write_yaml(handoffs_path, handoffs)

    result = validate_design(design_dir)

    assert not result.ok
    assert any("missing owner" in error for error in result.errors)


def test_init_creates_templates_without_selected_output(tmp_path: Path) -> None:
    design_dir = tmp_path / "new-design"
    init_design(design_dir)

    assert (design_dir / "requirements.raw.md").exists()
    assert (design_dir / "requirements.refined.yaml").exists()
    assert not validate_design(design_dir).ok


def test_cli_validate_returns_zero_for_fixture(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "commit-message")

    assert main(["validate", str(design_dir)]) == 0


def test_cli_dashboard_exports_static_review_bundle(tmp_path: Path) -> None:
    design_dir = copy_fixture(tmp_path, "password-reset")
    output = tmp_path / "review" / "index.html"

    assert main(["dashboard", str(design_dir), "--export", str(output)]) == 0
    html = output.read_text(encoding="utf-8")
    assert "Journeyman Review" in html
    assert "statechart-diagram" in html


def test_evaluation_artifacts_cover_fixture_metrics() -> None:
    for name in ["password-reset", "background-export", "commit-message"]:
        evaluation = load_yaml(ROOT / "examples" / "evaluations" / f"{name}.yaml")

        assert evaluation["result"] == "passes"
        assert evaluation["metrics"]["raw_source_preserved"] is True
        assert evaluation["metrics"]["requirement_evidence_coverage"]
