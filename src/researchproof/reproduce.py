from __future__ import annotations

import json
from pathlib import Path
from typing import Any

IGNORED_RUN_FIELDS = {"runtime_seconds"}


def _load_index(path: Path) -> dict[str, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = row.get("case_id")
        if not case_id or case_id in indexed:
            raise ValueError(f"missing or duplicate case_id in {path}: {case_id}")
        indexed[case_id] = row
    return indexed


def _stable_payload(run: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in run.items() if key not in IGNORED_RUN_FIELDS}


def compare_benchmark_indices(reference: Path, candidate: Path) -> dict[str, Any]:
    expected = _load_index(reference)
    actual = _load_index(candidate)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    changed = sorted(
        case_id
        for case_id in set(expected) & set(actual)
        if _stable_payload(expected[case_id]) != _stable_payload(actual[case_id])
    )
    return {
        "reference": str(reference),
        "candidate": str(candidate),
        "ignored_fields": sorted(IGNORED_RUN_FIELDS),
        "reference_cases": len(expected),
        "candidate_cases": len(actual),
        "missing_case_ids": missing,
        "unexpected_case_ids": unexpected,
        "changed_case_ids": changed,
        "reproduced": not missing and not unexpected and not changed,
    }


def write_comparison(reference: Path, candidate: Path, destination: Path) -> Path:
    report = compare_benchmark_indices(reference, candidate)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination

