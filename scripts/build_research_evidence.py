"""Build small, reviewable evidence files from reproducible experiment artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from researchproof.learned import extract_features


def main() -> None:
    paths = {
        "selection": Path("artifacts/selection_study_v1/summary.json"),
        "encoding": Path("artifacts/selection_study_v1/encoding_ablation.json"),
        "external": Path("artifacts/external_ase22/evaluation_summary.json"),
        "benchmark": Path("artifacts/benchmark_v0_4/runs.jsonl"),
    }
    loaded = {
        key: json.loads(path.read_text()) for key, path in paths.items() if key != "benchmark"
    }
    runs = [json.loads(line) for line in paths["benchmark"].read_text().splitlines()]
    collisions = {}
    for encoding in ("presence", "log_count"):
        groups = defaultdict(lambda: {"clean": 0, "faulty": 0})
        for run in runs:
            signature = json.dumps(
                extract_features(
                    run,
                    "runtime",
                    runtime_encoding=encoding,
                ),
                sort_keys=True,
            )
            groups[signature][run["variant"]] += 1
        collisions[encoding] = {
            "cases": len(runs),
            "distinct_vectors": len(groups),
            "conflicting_vectors": sum(v["clean"] > 0 and v["faulty"] > 0 for v in groups.values()),
            "empirical_accuracy_ceiling": sum(max(v.values()) for v in groups.values()) / len(runs),
            "meaning": "Upper bound for any deterministic classifier of this feature vector only.",
        }
    rows = []
    for group in ("evaluations", "fault_family_holdout_evaluations", "count_encoding_ablations"):
        for evaluation in loaded["encoding"][group]:
            rows.append(
                {
                    key: evaluation[key]
                    for key in (
                        "feature_mode",
                        "runtime_encoding",
                        "group_field",
                        "aggregate_metrics",
                    )
                }
            )
    bundle = {
        "status": "exploratory_research_evidence_not_submission_ready",
        "selection_study": loaded["selection"],
        "external_audit": loaded["external"],
        "feature_collision_diagnostic": collisions,
        "encoding_comparisons": rows,
        "inputs_sha256": {
            key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()
        },
        "implementation_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for directory in ("src/researchproof", "scripts")
            for path in sorted(Path(directory).glob("*.py"))
        },
    }
    destination = Path("results/2026-09-13")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "evidence.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Generated pilot results",
        "",
        "These are measured exploratory results.",
        "",
        "## Constructed selection-provenance experiment",
        "",
        "| Method | Known cases | F1 | False positives | False negatives | Decisions on unknown |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, value in loaded["selection"]["overall"].items():
        lines.append(
            f"| {name} | {value['cases']} | {value['f1']:.4f} | "
            f"{value['false_positive']} | {value['false_negative']} | "
            f"{value['decisions_on_unknown']} |"
        )
    lines.extend(
        [
            "",
            "810 constructed cases share model fits; 90 have unknown labels. "
            "Perfect explicit-API behavior is a mechanism check, not external detection accuracy.",
            "",
            "## External corpus, unchanged symbolic analyzer",
            "",
            "| Category | Eligible | Answered | Precision | Recall | F1 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, value in loaded["external"]["local"].items():
        lines.append(
            f"| {name} | {value['eligible']} | {value['cases']} | "
            f"{value['precision']:.4f} | {value['recall']:.4f} | {value['f1']:.4f} |"
        )
    lines.extend(
        [
            "",
            "The corpus contains 100 ground-truth rows, 66 with explicit category labels; "
            "86 notebooks parse and 58 have both labels and parsable source.",
            "",
            "## Learned feature representation",
            "",
            "| Mode | Encoding | Holdout | Accuracy | F1 |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in rows:
        m = row["aggregate_metrics"]
        lines.append(
            f"| {row['feature_mode']} | {row['runtime_encoding']} | {row['group_field']} "
            f"| {m['accuracy']:.4f} | {m['f1']:.4f} |"
        )
    lines.extend(["", "## Feature collision bound", ""])
    for name, value in collisions.items():
        lines.append(
            f"- {name}: empirical deterministic accuracy ceiling "
            f"{value['empirical_accuracy_ceiling']:.4f}."
        )
    lines.extend(
        [
            "",
            "Reproduce with the commands in docs/research_report_2026-09-13.md. "
            "Full metrics, provenance and hashes are in evidence.json.",
            "",
        ]
    )
    (destination / "tables.md").write_text("\n".join(lines))
    print(json.dumps(collisions, indent=2))


if __name__ == "__main__":
    main()
