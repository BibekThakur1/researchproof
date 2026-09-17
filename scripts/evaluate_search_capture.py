"""Development comparison; shared authored workflow is not an external benchmark."""

import argparse
import json
import platform

import sklearn
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from researchproof.datasets import available_datasets, load_dataset
from researchproof.manifest import dataset_checksum
from researchproof.search_capture import capture_grid_search
from researchproof.selection_provenance import ModelState, Score, audit_report, row_keys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    records = []
    for name in available_datasets():
        data = load_dataset(name)
        namespace = dataset_checksum(data.features, data.target)
        for seed in (0, 1, 2):
            splits = list(
                StratifiedKFold(3, shuffle=True, random_state=seed).split(
                    data.features, data.target
                )
            )
            # Independent baseline: validation roles taken straight from split inputs.
            validation_rows = {int(i) for _, validation in splits for i in validation}
            for known in (True, False):
                result = capture_grid_search(
                    DecisionTreeClassifier(random_state=seed),
                    {"max_depth": [1, 3, None]},
                    data.features,
                    data.target,
                    dataset=namespace,
                    row_ids=data.row_ids,
                    splits=splits,
                    prior=ModelState("predeclared") if known else None,
                )
                # Probe reporting origins only; these are not measured model accuracies.
                for report_ids in ([0], [len(data.target)], [0, len(data.target)]):
                    overlap = bool(validation_rows.intersection(report_ids))
                    baseline = (
                        "selection_reuse"
                        if overlap
                        else "no_observed_selection_reuse"
                        if known
                        else "insufficient_evidence"
                    )
                    verdict = audit_report(
                        result.selected, Score(0.0, row_keys(namespace, report_ids))
                    )
                    records.append(
                        {
                            "dataset": name,
                            "sha256": namespace,
                            "seed": seed,
                            "known_prior": known,
                            "report_ids": report_ids,
                            "provenance": verdict.status,
                            "split_role_baseline": baseline,
                            "library_winner": int(result.search.best_index_),
                            "captured_winner": int(result.selected.model_id),
                        }
                    )
    summary = {
        "status": "constructed_origin_probes_not_external_accuracy",
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "searches": 18,
        "candidate_fold_fits": 162,
        "records": records,
        "baseline_disagreements": sum(
            row["provenance"] != row["split_role_baseline"] for row in records
        ),
        "winner_disagreements": sum(
            row["library_winner"] != row["captured_winner"] for row in records
        ),
        "limitations": "One workflow family; artificial report-origin probes; no external labels.",
    }
    from pathlib import Path

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}))


if __name__ == "__main__":
    main()
