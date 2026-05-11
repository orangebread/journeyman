from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import yaml

RAW_FILE = "requirements.raw.md"
CONTEXT_FILE = "context.yaml"
REFINED_FILE = "requirements.refined.yaml"
NORMALIZATION_FILE = "normalization.diff.yaml"
DECISIONS_FILE = "decisions.log.yaml"
STATECHART_FILE = "statechart.happy.yaml"
SCENARIOS_FILE = "scenarios.yaml"
HANDOFFS_FILE = "handoffs.yaml"
FULL_STATECHART_FILE = "statechart.full.yaml"
REVIEW_FILE = "review.status.yaml"

REQUIRED_PHASE1_FILES = [
    RAW_FILE,
    CONTEXT_FILE,
    REFINED_FILE,
    NORMALIZATION_FILE,
    DECISIONS_FILE,
    REVIEW_FILE,
]

YAML_ARTIFACTS = [
    CONTEXT_FILE,
    REFINED_FILE,
    NORMALIZATION_FILE,
    DECISIONS_FILE,
    STATECHART_FILE,
    SCENARIOS_FILE,
    HANDOFFS_FILE,
    FULL_STATECHART_FILE,
    REVIEW_FILE,
]


class ArtifactError(Exception):
    """Raised when an artifact cannot be read or interpreted."""


@dataclass(frozen=True)
class LoadedYaml:
    path: Path
    data: Dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_hash(design_dir: Path) -> str:
    raw_path = design_dir / RAW_FILE
    if not raw_path.exists():
        raise ArtifactError(f"missing {RAW_FILE}")
    return sha256_file(raw_path)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ArtifactError(f"missing {path.name}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ArtifactError(f"{path.name}: invalid YAML: {exc}") from exc
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ArtifactError(f"{path.name}: expected top-level mapping")
    return value


def dump_yaml(data: Mapping[str, Any]) -> str:
    return yaml.safe_dump(dict(data), sort_keys=False, allow_unicode=False)


def alternative_artifacts(design_dir: Path) -> List[Path]:
    return sorted(design_dir.glob("artifact.*.yaml"))


def selected_output_artifacts(design_dir: Path) -> List[Path]:
    paths: List[Path] = []
    statechart = design_dir / STATECHART_FILE
    if statechart.exists():
        paths.append(statechart)
    paths.extend(alternative_artifacts(design_dir))
    return paths


def yaml_artifact_paths(design_dir: Path) -> Iterable[Path]:
    seen = set()
    for name in YAML_ARTIFACTS:
        path = design_dir / name
        if path.exists():
            seen.add(path)
            yield path
    for path in alternative_artifacts(design_dir):
        if path not in seen:
            yield path


def artifact_version(path: Path) -> Optional[str]:
    data = load_yaml(path)
    version = data.get("artifact_version")
    if version is None:
        return None
    return str(version)


def expected_parent_version(design_dir: Path, parent: str, raw_hash: str) -> Optional[str]:
    if parent == RAW_FILE:
        return f"sha256:{raw_hash}"
    parent_path = design_dir / parent
    if not parent_path.exists():
        return None
    return artifact_version(parent_path)


def missing_required_files(design_dir: Path) -> List[str]:
    missing = [name for name in REQUIRED_PHASE1_FILES if not (design_dir / name).exists()]
    if not selected_output_artifacts(design_dir):
        missing.append(f"{STATECHART_FILE} or artifact.*.yaml")
    return missing


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True
