"""Development pilot with real fits; not external validation or a novelty claim."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import sklearn
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from researchproof.datasets import available_datasets, load_dataset
from researchproof.manifest import dataset_checksum
from researchproof.score_store import save_scores
from researchproof.selection_provenance import ModelState, Score, row_keys

READER = """
import json, sys
from pathlib import Path
from researchproof.score_store import load_scores
from researchproof.selection_provenance import choose_model, audit_report
models, scores = load_scores(Path(sys.argv[1]))
chosen = choose_model(models, scores)
_, reports = load_scores(Path(sys.argv[2]))
index = next(i for i, model in enumerate(models) if model.model_id == chosen.model_id)
print(json.dumps({'winner': chosen.model_id,
                  'status': audit_report(chosen, reports[index]).status}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, help="Optional version-controlled results path")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for dataset in available_datasets():
        data = load_dataset(dataset)
        namespace = dataset_checksum(data.features, data.target)
        for seed in (0, 1, 2):
            train, heldout = train_test_split(
                data.row_ids, test_size=0.4, stratify=data.target, random_state=seed
            )
            selection, fresh = train_test_split(
                heldout, test_size=0.5, stratify=data.target[heldout], random_state=seed + 1
            )
            models, selection_scores, fresh_scores = [], [], []
            started = time.perf_counter()
            for depth in (1, 3, None):
                estimator = DecisionTreeClassifier(max_depth=depth, random_state=seed)
                estimator.fit(data.features[train], data.target[train])
                models.append(ModelState(str(depth)))
                for ids, destination in ((selection, selection_scores), (fresh, fresh_scores)):
                    destination.append(
                        Score(
                            float(estimator.score(data.features[ids], data.target[ids])),
                            row_keys(namespace, ids.tolist()),
                        )
                    )
            fit_score_seconds = time.perf_counter() - started
            directory = args.output / f"{dataset}-{seed}"
            selection_path = directory / "selection.json"
            fresh_path = directory / "fresh.json"
            started = time.perf_counter()
            save_scores(selection_path, models, selection_scores)
            save_scores(fresh_path, models, fresh_scores)
            save_seconds = time.perf_counter() - started
            for export in ("complete", "scalar_only", "missing_history"):
                envelope = json.loads(selection_path.read_text())
                for record in envelope["payload"]["records"]:
                    if export == "scalar_only":
                        for field in (
                            "selection_rows",
                            "observed_rows",
                            "model_complete",
                            "score_complete",
                        ):
                            record.pop(field)
                    elif export == "missing_history":
                        record.pop("selection_rows")
                body = json.dumps(
                    envelope["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False
                )
                envelope["sha256"] = hashlib.sha256(body.encode()).hexdigest()
                export_path = directory / f"{export}.json"
                export_path.write_text(json.dumps(envelope) + "\n")
                for report_name, report_path in (("reused", selection_path), ("fresh", fresh_path)):
                    started = time.perf_counter()
                    result = subprocess.run(
                        [sys.executable, "-c", READER, str(export_path), str(report_path)],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    # Expected labels come from the declared supported API semantics.
                    expected = (
                        "insufficient_evidence"
                        if export == "scalar_only"
                        else "selection_reuse"
                        if report_name == "reused"
                        else "insufficient_evidence"
                        if export == "missing_history"
                        else "no_observed_selection_reuse"
                    )
                    records.append(
                        {
                            "dataset": dataset,
                            "dataset_sha256": namespace,
                            "seed": seed,
                            "export": export,
                            "report": report_name,
                            "expected": expected,
                            **json.loads(result.stdout),
                            "fit_score_seconds": fit_score_seconds,
                            "save_seconds": save_seconds,
                            "reader_wall_seconds": time.perf_counter() - started,
                            "export_bytes": export_path.stat().st_size,
                        }
                    )
    summary = {
        "status": "development_pilot_not_external_validation",
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "fits": len(available_datasets()) * 3 * 3,
        "records": records,
        "mismatches": sum(row["status"] != row["expected"] for row in records),
        "limitations": [
            "Single authored workflow; records share fitted models.",
            "Explicit capture, not automatic search-library instrumentation.",
            "Reader timings include interpreter startup, not isolated monitor overhead.",
            "Scalar-only is an evidence-loss condition, not a published detector baseline.",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"cases": len(records), "mismatches": summary["mismatches"]}))
    if summary["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
