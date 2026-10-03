"""Descriptive analysis of all prespecified seeds, not independent-corpus inference."""

import re
from statistics import mean, stdev

from researchproof.neural_evidence import summarize

MATCHED_FIELDS = (
    "implementation_sha256",
    "device",
    "micro_batch",
    "python",
    "torch",
    "transformers",
    "installed_packages",
)


def _spread(values):
    return {
        "mean": mean(values),
        "sample_std": stdev(values),
        "min": min(values),
        "max": max(values),
    }


def analyze_runs(runs):
    """Each item is (run metadata, predictions). No seed selection or pooling."""
    if len(runs) != 3 or sorted(run.get("seed", -1) for run, _ in runs) != [0, 1, 2]:
        raise ValueError("exactly the prespecified seeds 0, 1 and 2 are required")
    runs = sorted(runs, key=lambda pair: pair[0]["seed"])
    reference = runs[0][0]
    identities = None
    summaries = []
    for run, records in runs:
        summary = summarize(run, records)
        if any(field not in run or run[field] != reference.get(field) for field in MATCHED_FIELDS):
            raise ValueError("implementation or execution environment differs across seeds")
        if not re.fullmatch(r"[0-9a-f]{64}", run["implementation_sha256"]):
            raise ValueError("invalid implementation fingerprint")
        current = {}
        for row in records:
            source_hash = row.get("source_sha256", "")
            if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
                raise ValueError("source fingerprints are required")
            current[(row["id"], row["variant"])] = (
                row["label"],
                source_hash,
                row["token_input_changed"],
            )
        if identities is not None and current != identities:
            raise ValueError("evaluation identities, labels or visible tokens differ across seeds")
        identities = current
        for edit in summary["edits"].values():
            edit["flip_rate_all_pairs"] = edit["flips"] / edit["paired"]
            edit["flip_rate_visible_pairs"] = (
                edit["flips"] / edit["token_changed"] if edit["token_changed"] else None
            )
            # Denominator is every eligible pair, not only initially correct examples.
            edit["harmful_rate_all_pairs"] = edit["correct_to_wrong"] / edit["paired"]
            edit["corrective_rate_all_pairs"] = edit["wrong_to_correct"] / edit["paired"]
        summaries.append({"seed": run["seed"], **summary})
    metrics = {
        metric: _spread([item["metrics"][metric] for item in summaries])
        for metric in ("precision", "recall", "f1", "false_positive_rate")
    }
    edits = {}
    for variant in summaries[0]["edits"]:
        edits[variant] = {}
        for metric in (
            "flip_rate_all_pairs",
            "flip_rate_visible_pairs",
            "harmful_rate_all_pairs",
            "corrective_rate_all_pairs",
        ):
            values = [item["edits"][variant][metric] for item in summaries]
            edits[variant][metric] = (
                None if any(value is None for value in values) else _spread(values)
            )
    return {
        "status": "three_seed_descriptive_analysis",
        "seeds": [0, 1, 2],
        "distinct_original_test_cases": 381,
        "per_seed": summaries,
        "seed_variation": {"metrics": metrics, "edits": edits},
        "limitations": [
            "Sample standard deviations describe three optimization seeds, "
            "not population confidence intervals.",
            "Seeds share one test set; do not treat them as 1,143 independent test cases.",
            "The test split is previously explored, not an unseen confirmation corpus.",
            "Matching hashes across runs does not verify source labels or human review.",
            "No statistical superiority or publication-readiness conclusion is produced.",
        ],
    }
