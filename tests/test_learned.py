import json

import numpy as np

from researchproof.benchmark import generate_benchmark
from researchproof.learned import (
    evaluate_learned_baselines,
    expected_calibration_error,
    extract_features,
)


def test_feature_extraction_never_uses_variant_or_score() -> None:
    run = {
        "variant": "faulty",
        "accuracy": 1.0,
        "operation_trace": ["train_test_split", "model_fit_mixed_rows"],
        "evidence": {"training_observed_test_rows": 2},
    }
    features = extract_features(run, "hybrid")
    assert not any("variant" in name or "accuracy" in name for name in features)
    assert features["operation=model_fit_mixed_rows"] == 1.0
    assert features["evidence=training_observed_test_rows"] == 1.0


def test_calibration_error_is_zero_for_perfect_confidence() -> None:
    labels = np.array([0, 0, 1, 1])
    probabilities = np.array([0.0, 0.0, 1.0, 1.0])
    assert expected_calibration_error(labels, probabilities) == 0.0


def test_learned_report_contains_three_held_out_folds(tmp_path) -> None:
    index = generate_benchmark(
        [7],
        tmp_path / "benchmark",
        dataset_ids=["sklearn_breast_cancer", "sklearn_wine", "sklearn_digits"],
    )
    destination = evaluate_learned_baselines(index, tmp_path / "learned.json")
    report = json.loads(destination.read_text(encoding="utf-8"))
    assert len(report["evaluations"]) == 3
    assert all(len(evaluation["folds"]) == 3 for evaluation in report["evaluations"])
    assert len(report["fault_family_holdout_evaluations"]) == 3
    assert all(
        len(evaluation["folds"]) == 3
        for evaluation in report["fault_family_holdout_evaluations"]
    )
    assert report["status"] == "engineering_baseline_not_a_research_finding"
