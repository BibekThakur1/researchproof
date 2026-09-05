from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

from researchproof.audit import classification_metrics

FeatureMode = Literal["static", "runtime", "hybrid"]


def extract_features(run: dict[str, Any], mode: FeatureMode) -> dict[str, float]:
    features: dict[str, float] = {}
    if mode in {"static", "hybrid"}:
        for index, operation in enumerate(run.get("operation_trace", [])):
            features[f"operation={operation}"] = 1.0
            if index:
                previous = run["operation_trace"][index - 1]
                features[f"transition={previous}->{operation}"] = 1.0
    if mode in {"runtime", "hybrid"}:
        evidence = run.get("evidence", {})
        for name, value in evidence.items():
            features[f"evidence={name}"] = float(bool(value))
    return features


def expected_calibration_error(
    labels: np.ndarray, probabilities: np.ndarray, bins: int = 10
) -> float:
    boundaries = np.linspace(0.0, 1.0, bins + 1)
    total = len(labels)
    error = 0.0
    for lower, upper in zip(boundaries[:-1], boundaries[1:], strict=True):
        if upper == 1.0:
            selected = (probabilities >= lower) & (probabilities <= upper)
        else:
            selected = (probabilities >= lower) & (probabilities < upper)
        if not np.any(selected):
            continue
        confidence = float(np.mean(probabilities[selected]))
        frequency = float(np.mean(labels[selected]))
        error += float(np.sum(selected)) / total * abs(confidence - frequency)
    return error


def _leave_one_group_out(
    runs: list[dict[str, Any]], mode: FeatureMode, group_field: str
) -> dict[str, Any]:
    groups = sorted({run[group_field] for run in runs})
    folds: list[dict[str, Any]] = []
    all_labels: list[bool] = []
    all_predictions: list[bool] = []
    all_probabilities: list[float] = []
    for held_out in groups:
        train = [run for run in runs if run[group_field] != held_out]
        test = [run for run in runs if run[group_field] == held_out]
        vectorizer = DictVectorizer(sparse=True)
        x_train = vectorizer.fit_transform([extract_features(run, mode) for run in train])
        x_test = vectorizer.transform([extract_features(run, mode) for run in test])
        y_train = np.asarray([run["variant"] == "faulty" for run in train], dtype=int)
        y_test = np.asarray([run["variant"] == "faulty" for run in test], dtype=int)
        model = LogisticRegression(max_iter=1000, random_state=0)
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        predictions = probabilities >= 0.5
        metrics = classification_metrics(y_test.astype(bool), predictions)
        folds.append(
            {
                "held_out_group": held_out,
                "metrics": asdict(metrics),
                "brier_score": float(np.mean((probabilities - y_test) ** 2)),
                "expected_calibration_error": expected_calibration_error(y_test, probabilities),
            }
        )
        all_labels.extend(y_test.astype(bool).tolist())
        all_predictions.extend(predictions.tolist())
        all_probabilities.extend(probabilities.tolist())
    labels_array = np.asarray(all_labels, dtype=int)
    probabilities_array = np.asarray(all_probabilities)
    return {
        "feature_mode": mode,
        "group_field": group_field,
        "protocol": f"leave_one_complete_{group_field}_out",
        "aggregate_metrics": asdict(classification_metrics(all_labels, all_predictions)),
        "aggregate_brier_score": float(np.mean((probabilities_array - labels_array) ** 2)),
        "aggregate_expected_calibration_error": expected_calibration_error(
            labels_array, probabilities_array
        ),
        "folds": folds,
    }


def leave_one_dataset_out(runs: list[dict[str, Any]], mode: FeatureMode) -> dict[str, Any]:
    return _leave_one_group_out(runs, mode, "dataset_id")


def leave_one_fault_family_out(
    runs: list[dict[str, Any]], mode: FeatureMode
) -> dict[str, Any]:
    return _leave_one_group_out(runs, mode, "fault_family")


def evaluate_learned_baselines(index: Path, destination: Path) -> Path:
    runs = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
    payload = {
        "status": "engineering_baseline_not_a_research_finding",
        "warning": (
            "Current operation names expose the injected mechanism. These results validate the "
            "evaluation pipeline but must not be reported as evidence of real-world detection."
        ),
        "source": str(index),
        "evaluations": [
            leave_one_dataset_out(runs, mode) for mode in ("static", "runtime", "hybrid")
        ],
        "fault_family_holdout_evaluations": [
            leave_one_fault_family_out(runs, mode)
            for mode in ("static", "runtime", "hybrid")
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
