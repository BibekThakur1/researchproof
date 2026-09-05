from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def paired_differences(
    runs: list[dict[str, Any]], metric: str
) -> list[tuple[str, str, float]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for run in runs:
        grouped[run["pair_id"]][run["variant"]] = run
    differences: list[tuple[str, str, float]] = []
    for pair_id, variants in sorted(grouped.items()):
        if set(variants) != {"clean", "faulty"}:
            raise ValueError(f"pair {pair_id} must contain exactly one clean and one faulty run")
        clean = variants["clean"]
        faulty = variants["faulty"]
        if clean["base_train_hash"] != faulty["base_train_hash"]:
            raise ValueError(f"pair {pair_id} does not share its training split")
        if clean["base_test_hash"] != faulty["base_test_hash"]:
            raise ValueError(f"pair {pair_id} does not share its test split")
        differences.append(
            (pair_id, clean["fault_family"], float(faulty[metric]) - float(clean[metric]))
        )
    return differences


def bootstrap_mean_interval(
    values: list[float], *, samples: int = 10_000, seed: int = 20260905
) -> dict[str, float | int]:
    if not values:
        raise ValueError("at least one paired difference is required")
    array = np.asarray(values, dtype=float)
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, len(array), size=(samples, len(array)))
    means = array[indices].mean(axis=1)
    lower, upper = np.quantile(means, [0.025, 0.975])
    return {
        "pairs": len(values),
        "mean_faulty_minus_clean": float(array.mean()),
        "median_faulty_minus_clean": float(np.median(array)),
        "bootstrap_95_percent_lower": float(lower),
        "bootstrap_95_percent_upper": float(upper),
        "bootstrap_samples": samples,
        "bootstrap_seed": seed,
    }


def summarize_paired_effects(index: Path, destination: Path) -> Path:
    runs = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
    metrics = ("accuracy", "balanced_accuracy", "roc_auc")
    report: dict[str, Any] = {
        "status": "engineering_effect_summary_not_a_research_finding",
        "difference_direction": "faulty_minus_clean",
        "dependence_warning": (
            "Severity contrasts reuse the same clean run conditions. Treat severity-specific "
            "summaries as related contrasts, not independent samples."
        ),
        "metrics": {},
    }
    severity_by_pair = {
        run["pair_id"]: run.get("fault_severity", "unspecified") for run in runs
    }
    for metric in metrics:
        differences = paired_differences(runs, metric)
        by_family: dict[str, list[float]] = defaultdict(list)
        by_severity: dict[str, list[float]] = defaultdict(list)
        for _, family, value in differences:
            by_family[family].append(value)
        for pair_id, _, value in differences:
            by_severity[severity_by_pair[pair_id]].append(value)
        report["metrics"][metric] = {
            "overall": bootstrap_mean_interval([value for _, _, value in differences]),
            "by_fault_family": {
                family: bootstrap_mean_interval(values)
                for family, values in sorted(by_family.items())
            },
            "by_fault_severity": {
                severity: bootstrap_mean_interval(values)
                for severity, values in sorted(by_severity.items())
            },
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
