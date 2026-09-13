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


def selective_risk_curve(
    labels: np.ndarray,
    probabilities: np.ndarray,
    coverage_levels: tuple[float, ...] = (1.0, 0.8, 0.5, 0.25),
    *,
    confidence: np.ndarray | None = None,
) -> list[dict[str, float | int]]:
    if len(labels) != len(probabilities) or not len(labels):
        raise ValueError("paired non-empty labels and probabilities are required")
    confidence_values = (
        np.abs(probabilities - 0.5) * 2.0
        if confidence is None
        else np.asarray(confidence, dtype=float)
    )
    if len(confidence_values) != len(labels):
        raise ValueError("confidence must align with labels")
    predictions = probabilities >= 0.5
    order = np.argsort(-confidence_values, kind="stable")
    curve: list[dict[str, float | int]] = []
    for requested in coverage_levels:
        if not 0.0 < requested <= 1.0:
            raise ValueError("coverage levels must be in (0, 1]")
        selected_count = max(1, int(np.ceil(len(labels) * requested)))
        selected = order[:selected_count]
        mistakes = int(np.sum(predictions[selected] != labels[selected]))
        curve.append(
            {
                "requested_coverage": requested,
                "selected_cases": selected_count,
                "actual_coverage": selected_count / len(labels),
                "selective_risk": mistakes / selected_count,
                "mean_confidence": float(np.mean(confidence_values[selected])),
            }
        )
    return curve


def extract_features(
    run: dict[str, Any], mode: FeatureMode, *, runtime_encoding: str = "presence"
) -> dict[str, float]:
    if runtime_encoding not in {"presence", "log_count"}:
        raise ValueError("unknown runtime encoding")
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
            features[f"evidence={name}"] = (
                float(bool(value))
                if runtime_encoding == "presence"
                else float(np.log1p(float(value)))
            )
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
    runs: list[dict[str, Any]],
    mode: FeatureMode,
    group_field: str,
    *,
    runtime_encoding: str = "presence",
) -> dict[str, Any]:
    groups = sorted({run[group_field] for run in runs})
    folds: list[dict[str, Any]] = []
    all_labels: list[bool] = []
    all_predictions: list[bool] = []
    all_probabilities: list[float] = []
    all_support_confidences: list[float] = []
    for held_out in groups:
        train = [run for run in runs if run[group_field] != held_out]
        test = [run for run in runs if run[group_field] == held_out]
        train_features = [
            extract_features(run, mode, runtime_encoding=runtime_encoding) for run in train
        ]
        test_features = [
            extract_features(run, mode, runtime_encoding=runtime_encoding) for run in test
        ]
        vectorizer = DictVectorizer(sparse=True)
        x_train = vectorizer.fit_transform(train_features)
        x_test = vectorizer.transform(test_features)
        y_train = np.asarray([run["variant"] == "faulty" for run in train], dtype=int)
        y_test = np.asarray([run["variant"] == "faulty" for run in test], dtype=int)
        model = LogisticRegression(max_iter=1000, random_state=0)
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        predictions = probabilities >= 0.5
        known = set(vectorizer.feature_names_)
        support = np.asarray(
            [
                sum(abs(value) for key, value in features.items() if key in known)
                / max(sum(abs(value) for value in features.values()), 1e-12)
                for features in test_features
            ]
        )
        model_confidence = np.abs(probabilities - 0.5) * 2.0
        support_confidence = model_confidence * support
        metrics = classification_metrics(y_test.astype(bool), predictions)
        folds.append(
            {
                "held_out_group": held_out,
                "metrics": asdict(metrics),
                "brier_score": float(np.mean((probabilities - y_test) ** 2)),
                "expected_calibration_error": expected_calibration_error(y_test, probabilities),
                "selective_risk": selective_risk_curve(y_test, probabilities),
                "support_adjusted_selective_risk": selective_risk_curve(
                    y_test, probabilities, confidence=support_confidence
                ),
                "mean_feature_support": float(np.mean(support)),
            }
        )
        all_labels.extend(y_test.astype(bool).tolist())
        all_predictions.extend(predictions.tolist())
        all_probabilities.extend(probabilities.tolist())
        all_support_confidences.extend(support_confidence.tolist())
    labels_array = np.asarray(all_labels, dtype=int)
    probabilities_array = np.asarray(all_probabilities)
    support_confidence_array = np.asarray(all_support_confidences)
    return {
        "feature_mode": mode,
        "runtime_encoding": runtime_encoding,
        "group_field": group_field,
        "protocol": f"leave_one_complete_{group_field}_out",
        "aggregate_metrics": asdict(classification_metrics(all_labels, all_predictions)),
        "aggregate_brier_score": float(np.mean((probabilities_array - labels_array) ** 2)),
        "aggregate_expected_calibration_error": expected_calibration_error(
            labels_array, probabilities_array
        ),
        "aggregate_selective_risk": selective_risk_curve(labels_array, probabilities_array),
        "aggregate_support_adjusted_selective_risk": selective_risk_curve(
            labels_array,
            probabilities_array,
            confidence=support_confidence_array,
        ),
        "folds": folds,
    }


def leave_one_dataset_out(runs: list[dict[str, Any]], mode: FeatureMode) -> dict[str, Any]:
    return _leave_one_group_out(runs, mode, "dataset_id")


def leave_one_fault_family_out(runs: list[dict[str, Any]], mode: FeatureMode) -> dict[str, Any]:
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
        "count_encoding_ablations": [
            _leave_one_group_out(runs, mode, group, runtime_encoding="log_count")
            for mode in ("runtime", "hybrid")
            for group in ("dataset_id", "fault_family")
        ],
        "evaluations": [
            leave_one_dataset_out(runs, mode) for mode in ("static", "runtime", "hybrid")
        ],
        "fault_family_holdout_evaluations": [
            leave_one_fault_family_out(runs, mode) for mode in ("static", "runtime", "hybrid")
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
