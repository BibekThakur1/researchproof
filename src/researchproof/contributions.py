from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from researchproof.benchmark import FaultFamily
from researchproof.source_benchmark import SourceCase, build_source_cases


class ContributionError(ValueError):
    """Raised when an external source-template contribution is unsafe or incomplete."""


def _text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContributionError(f"{field} must be a non-empty string")
    return value.strip()


def load_contribution(metadata_path: Path) -> SourceCase:
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContributionError(f"cannot read {metadata_path}: {error}") from error
    if not isinstance(payload, dict):
        raise ContributionError("contribution metadata must be a JSON object")
    author_id = _text(payload, "author_id")
    style_id = _text(payload, "style_id")
    template_family = _text(payload, "template_family")
    fault_family = _text(payload, "fault_family")
    variant = _text(payload, "variant")
    license_statement = _text(payload, "license_statement")
    if variant not in {"clean", "faulty"}:
        raise ContributionError("variant must be clean or faulty")
    known_faults = {family.value for family in FaultFamily}
    if variant == "faulty" and fault_family not in known_faults:
        raise ContributionError("faulty contributions must use a registered fault family")
    if len(license_statement) < 20:
        raise ContributionError("license_statement must explain authorship and research reuse")
    source_name = _text(payload, "source_file")
    source_path = Path(source_name)
    if source_path.name != source_name or source_path.suffix != ".py":
        raise ContributionError("source_file must be a local .py filename without directories")
    source = (metadata_path.parent / source_path).read_text(encoding="utf-8")
    try:
        ast.parse(source)
    except SyntaxError as error:
        raise ContributionError(f"source does not parse as Python: {error}") from error
    material = json.dumps(
        {
            "author_id": author_id,
            "style_id": style_id,
            "template_family": template_family,
            "fault_family": fault_family,
            "variant": variant,
            "source": source,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return SourceCase(
        source_case_id=f"source-{hashlib.sha256(material.encode()).hexdigest()[:16]}",
        author_id=author_id,
        style_id=style_id,
        template_family=template_family,
        fault_family=fault_family,
        variant=variant,
        source=source,
    )


def build_combined_source_index(contributions_dir: Path, destination: Path) -> Path:
    cases = build_source_cases()
    if contributions_dir.is_dir():
        cases.extend(load_contribution(path) for path in sorted(contributions_dir.glob("*.json")))
    ids = [case.source_case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ContributionError("duplicate source case IDs were generated")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(asdict(case), sort_keys=True) + "\n" for case in cases),
        encoding="utf-8",
    )
    return destination

