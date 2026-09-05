from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class ReviewError(ValueError):
    """Raised when blinded review files cannot be compared safely."""


def _read_review(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "blind_id" not in rows[0]:
        raise ReviewError(f"{path} is not a ResearchProof review form")
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        blind_id = row["blind_id"].strip()
        answer = row["valid_experiment"].strip().lower()
        if answer not in {"yes", "no"}:
            raise ReviewError(f"{blind_id} in {path} must use yes or no for valid_experiment")
        if blind_id in indexed:
            raise ReviewError(f"duplicate blind_id {blind_id} in {path}")
        indexed[blind_id] = row
    return indexed


def _cohen_kappa(first: list[bool], second: list[bool]) -> float:
    if len(first) != len(second) or not first:
        raise ReviewError("paired non-empty labels are required")
    observed = sum(left == right for left, right in zip(first, second, strict=True)) / len(first)
    first_yes = sum(first) / len(first)
    second_yes = sum(second) / len(second)
    expected = first_yes * second_yes + (1 - first_yes) * (1 - second_yes)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def compare_reviews(first_path: Path, second_path: Path) -> dict[str, Any]:
    first = _read_review(first_path)
    second = _read_review(second_path)
    if set(first) != set(second):
        missing_first = sorted(set(second) - set(first))
        missing_second = sorted(set(first) - set(second))
        raise ReviewError(
            "review IDs differ; "
            f"missing from first={missing_first}, missing from second={missing_second}"
        )
    ids = sorted(first)
    first_labels = [first[item]["valid_experiment"].strip().lower() == "yes" for item in ids]
    second_labels = [second[item]["valid_experiment"].strip().lower() == "yes" for item in ids]
    disagreements = []
    for item, left, right in zip(ids, first_labels, second_labels, strict=True):
        if left != right:
            disagreements.append(
                {
                    "blind_id": item,
                    "first_valid": left,
                    "second_valid": right,
                    "first_evidence": first[item].get("evidence", ""),
                    "second_evidence": second[item].get("evidence", ""),
                }
            )
    agreement = sum(left == right for left, right in zip(first_labels, second_labels, strict=True))
    return {
        "cases": len(ids),
        "agreements": agreement,
        "raw_agreement": agreement / len(ids),
        "cohen_kappa": _cohen_kappa(first_labels, second_labels),
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
    }


def write_comparison(first: Path, second: Path, destination: Path) -> Path:
    report = compare_reviews(first, second)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
