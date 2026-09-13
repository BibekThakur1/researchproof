"""Reproduce the explicit-selection API pilot without running external source code."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import asdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from researchproof.audit import classification_metrics
from researchproof.datasets import available_datasets, load_dataset
from researchproof.manifest import dataset_checksum
from researchproof.selection_provenance import (
    ModelState,
    Score,
    audit_report,
    choose_model,
    combine_scores,
    decision,
    row_keys,
)


def run_study(seeds: list[int]) -> tuple[list[dict], dict]:
    records = []
    fingerprints = {}
    for dataset_id in available_datasets():
        data = load_dataset(dataset_id)
        checksum = dataset_checksum(data.features, data.target)
        fingerprints[dataset_id] = checksum
        for seed in seeds:
            train, remaining = train_test_split(
                data.row_ids,
                test_size=0.4,
                random_state=seed,
                stratify=data.target,
            )
            validation, heldout = train_test_split(
                remaining,
                test_size=0.5,
                random_state=seed + 1,
                stratify=data.target[remaining],
            )
            test, fresh = train_test_split(
                heldout,
                test_size=0.5,
                random_state=seed + 2,
                stratify=data.target[heldout],
            )
            partitions = {"train": train, "validation": validation, "test": test, "fresh": fresh}
            for family in ("logistic", "tree"):
                for budget in (2, 3, 5):
                    estimators = []
                    for index in range(budget):
                        if family == "logistic":
                            estimator = make_pipeline(
                                StandardScaler(),
                                LogisticRegression(
                                    C=(0.01, 0.1, 1, 10, 100)[index],
                                    max_iter=2000,
                                    random_state=seed,
                                ),
                            )
                        else:
                            estimator = DecisionTreeClassifier(
                                max_depth=(1, 2, 4, 8, None)[index],
                                random_state=seed,
                            )
                        estimator.fit(data.features[train], data.target[train])
                        estimators.append(estimator)
                    models = [ModelState(str(index)) for index in range(budget)]

                    def scenario(kind: str) -> dict:
                        accesses: list[frozenset] = []

                        def evaluate(model: ModelState, partition: str) -> Score:
                            ids = partitions[partition]
                            rows = row_keys(checksum, ids.tolist())
                            value = estimators[int(model.model_id)].score(
                                data.features[ids],
                                data.target[ids],
                            )
                            accesses.append(rows)
                            return Score(float(value), rows)

                        chosen = models[0]
                        expected: bool | None = False
                        if kind == "single_report":
                            reported = evaluate(chosen, "test")
                        elif kind == "repeat_report":
                            for _ in range(budget):
                                reported = evaluate(chosen, "test")
                        elif kind == "predeclared_comparison":
                            # Every fixed candidate is reported; no winner is selected.
                            reports = [evaluate(model, "test") for model in models]
                            reported = reports[0]
                        elif kind == "validation_selection":
                            scores = [evaluate(model, "validation") for model in models]
                            chosen = choose_model(models, scores)
                            reported = evaluate(chosen, "test")
                        elif kind in {"test_selection_cached", "test_selection_fresh"}:
                            scores = [evaluate(model, "test") for model in models]
                            chosen = choose_model(models, scores)
                            if kind == "test_selection_cached":
                                reported = scores[int(chosen.model_id)]
                                expected = True
                            else:
                                reported = evaluate(chosen, "fresh")
                        elif kind == "single_score_threshold":
                            initial = evaluate(models[0], "test")
                            winner = models[0] if initial.value >= 0.5 else models[1]
                            chosen = decision(winner, models[:2], [initial])
                            reported = initial if winner == models[0] else evaluate(winner, "test")
                            expected = True
                        elif kind == "pooled_score_selection":
                            test_scores = [evaluate(model, "test") for model in models]
                            validation_scores = [evaluate(model, "validation") for model in models]
                            scores = [
                                combine_scores([a, b])
                                for a, b in zip(test_scores, validation_scores, strict=True)
                            ]
                            chosen = choose_model(models, scores)
                            reported = test_scores[int(chosen.model_id)]
                            expected = True
                        elif kind == "missing_history":
                            chosen = ModelState("0", complete=False)
                            reported = evaluate(chosen, "test")
                            expected = None
                        else:
                            raise ValueError(kind)
                        verdict = audit_report(chosen, reported)
                        test_accesses = sum(
                            bool(rows & row_keys(checksum, test.tolist())) for rows in accesses
                        )
                        predictions = {
                            "count_rule": test_accesses > 1,
                            "selection_provenance": (
                                None
                                if verdict.status == "insufficient_evidence"
                                else verdict.status == "selection_reuse"
                            ),
                            "without_decision_edges": False if chosen.complete else None,
                            "without_row_identity": (
                                bool(chosen.selection_rows) if chosen.complete else None
                            ),
                        }
                        return {
                            "scenario": kind,
                            "dataset": dataset_id,
                            "seed": seed,
                            "model_family": family,
                            "budget": budget,
                            "expected_selection_reuse": expected,
                            "predictions": predictions,
                            "verdict": asdict(verdict),
                            "test_evaluations": test_accesses,
                            "reported_accuracy": reported.value,
                            "chosen_model": chosen.model_id,
                            "selection_rows": sorted(chosen.selection_rows),
                            "report_rows": sorted(reported.observed_rows),
                            "partitions": {name: ids.tolist() for name, ids in partitions.items()},
                        }

                    for kind in (
                        "single_report",
                        "repeat_report",
                        "predeclared_comparison",
                        "validation_selection",
                        "test_selection_cached",
                        "test_selection_fresh",
                        "single_score_threshold",
                        "pooled_score_selection",
                        "missing_history",
                    ):
                        records.append(scenario(kind))
    summary = {
        "status": "constructed_mechanism_study_not_external_validation",
        "seeds": seeds,
        "datasets": fingerprints,
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
        },
        "records": len(records),
        "labelled": sum(row["expected_selection_reuse"] is not None for row in records),
        "independent_source_authors": 1,
        "warning": "Scenarios share fitted models; case counts are not independent sample sizes.",
        "overall": {},
        "by_scenario": {},
    }

    def metrics(rows: list[dict], method: str) -> dict:
        eligible = [row for row in rows if row["expected_selection_reuse"] is not None]
        answered = [row for row in eligible if row["predictions"][method] is not None]
        result = asdict(
            classification_metrics(
                [row["expected_selection_reuse"] for row in answered],
                [row["predictions"][method] for row in answered],
            )
        )
        result.update(
            {
                "eligible": len(eligible),
                "abstentions_on_known": len(eligible) - len(answered),
                "unknown_label_cases": len(rows) - len(eligible),
                "decisions_on_unknown": sum(
                    row["expected_selection_reuse"] is None
                    and row["predictions"][method] is not None
                    for row in rows
                ),
            }
        )
        return result

    for method in records[0]["predictions"]:
        summary["overall"][method] = metrics(records, method)
    for kind in sorted({row["scenario"] for row in records}):
        rows = [row for row in records if row["scenario"] == kind]
        summary["by_scenario"][kind] = {
            method: metrics(rows, method) for method in records[0]["predictions"]
        }
    return records, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/selection_study_v1"))
    parser.add_argument("--seeds", nargs="+", type=int, default=[7, 19, 43, 71, 101])
    args = parser.parse_args()
    records, summary = run_study(args.seeds)
    args.output.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(row, sort_keys=True) + "\n" for row in records)
    summary["records_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    summary["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.output / "records.jsonl").write_text(body)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"records": len(records), "overall": summary["overall"]}, indent=2))


if __name__ == "__main__":
    main()
