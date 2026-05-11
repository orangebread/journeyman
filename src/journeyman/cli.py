from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .artifacts import (
    CONTEXT_FILE,
    DECISIONS_FILE,
    NORMALIZATION_FILE,
    RAW_FILE,
    REFINED_FILE,
    REVIEW_FILE,
    dump_yaml,
)
from .dashboard import run_dashboard
from .validator import validate_design, validate_hashes


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser(
        prog="journeyman",
        description="Deterministic support tools for the skill-owned Journeyman workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a design folder with starter templates.")
    init_parser.add_argument("design_dir", type=Path)

    hash_parser = subparsers.add_parser("hash", help="Verify raw source hashes and parent artifact versions.")
    hash_parser.add_argument("design_dir", type=Path)

    validate_parser = subparsers.add_parser("validate", help="Validate a design artifact folder.")
    validate_parser.add_argument("design_dir", type=Path)

    dashboard_parser = subparsers.add_parser("dashboard", help="Launch the read-only local dashboard viewer.")
    dashboard_parser.add_argument("design_dir", type=Path)
    dashboard_parser.add_argument("--host", default="127.0.0.1")
    dashboard_parser.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    if args.command == "init":
        init_design(args.design_dir)
        print(f"Initialized Journeyman design folder: {args.design_dir}")
        return 0
    if args.command == "hash":
        return _print_result(validate_hashes(args.design_dir))
    if args.command == "validate":
        return _print_result(validate_design(args.design_dir))
    if args.command == "dashboard":
        run_dashboard(args.design_dir, args.host, args.port)
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


def init_design(design_dir: Path) -> None:
    design_dir.mkdir(parents=True, exist_ok=True)
    _write_if_missing(design_dir / RAW_FILE, "")
    _write_yaml_if_missing(design_dir / CONTEXT_FILE, _context_template())
    _write_yaml_if_missing(design_dir / REFINED_FILE, _refined_template())
    _write_yaml_if_missing(design_dir / NORMALIZATION_FILE, _normalization_template())
    _write_yaml_if_missing(design_dir / DECISIONS_FILE, _decisions_template())
    _write_yaml_if_missing(design_dir / REVIEW_FILE, _review_template())


def _print_result(result: Any) -> int:
    if result.ok:
        print("OK")
        for warning in result.warnings:
            print(f"WARN: {warning}")
        return 0
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for warning in result.warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    return 1


def _write_if_missing(path: Path, text: str) -> None:
    if path.exists():
        return
    path.write_text(text, encoding="utf-8")


def _write_yaml_if_missing(path: Path, data: Dict[str, Any]) -> None:
    _write_if_missing(path, dump_yaml(data))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _base_template() -> Dict[str, Any]:
    now = _now()
    return {
        "schema_version": 1,
        "artifact_version": 1,
        "created_at": now,
        "updated_at": now,
        "source_hash": "",
        "parent_artifact_versions": {},
    }


def _context_template() -> Dict[str, Any]:
    data = _base_template()
    data.update(
        {
            "project_summary": "",
            "codebase_pointers": [],
            "related_artifacts": [],
            "known_systems": [],
            "known_actors": [],
            "glossary": [],
            "constraints": [],
            "out_of_scope": [],
        }
    )
    return data


def _refined_template() -> Dict[str, Any]:
    data = _base_template()
    data.update(
        {
            "source_summary": "",
            "request_type": "",
            "recommended_artifact": "",
            "recommendation_confidence": "",
            "clarification_budget": 3,
            "scope_fence": {
                "partial": True,
                "primary_actor": "",
                "start_trigger": "",
                "terminal_outcome": "",
                "non_goals": [],
                "external_systems": [],
                "success_criteria": [],
                "failure_definition": "",
            },
            "requirements": [],
            "negative_acceptance_criteria": [],
            "unknowns": {
                "blocking_now": [],
                "safe_to_assume": [],
                "design_risk": [],
                "implementation_risk": [],
                "defer_until_code": [],
            },
            "normalization_summary": "",
            "dependencies_seed": [],
            "handoffs_seed": [],
            "glossary_updates": [],
            "decisions": [],
        }
    )
    return data


def _normalization_template() -> Dict[str, Any]:
    data = _base_template()
    data.update(
        {
            "raw_source_hash": "",
            "added_inferences": [],
            "renamed_terms": [],
            "grouped_requirements": [],
            "omitted_items": [],
            "contradictions": [],
            "assumptions_introduced": [],
            "requires_user_review": True,
        }
    )
    return data


def _decisions_template() -> Dict[str, Any]:
    data = _base_template()
    data.update({"decisions": []})
    return data


def _review_template() -> Dict[str, Any]:
    data = _base_template()
    data.update(
        {
            "status": "partial",
            "accepted_at": None,
            "reviewer": None,
            "notes": [],
        }
    )
    return data
