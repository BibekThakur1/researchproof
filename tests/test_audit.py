from dataclasses import asdict

from researchproof.audit import (
    always_clean,
    classification_metrics,
    runtime_lineage_rules,
    static_sequence_rules,
)
from researchproof.benchmark import FaultFamily, run_benchmark_case


def run_dict(family: FaultFamily, variant: str) -> dict:
    _, run = run_benchmark_case(family, variant, seed=7)
    return asdict(run)


def test_always_clean_is_an_explicit_weak_baseline() -> None:
    decision = always_clean(run_dict(FaultFamily.TRAIN_TEST_OVERLAP, "faulty"))
    assert decision.predicted_fault is False
    assert decision.evidence == ()


def test_static_rules_detect_engineered_faults_without_false_alarm() -> None:
    for family in FaultFamily:
        assert static_sequence_rules(run_dict(family, "clean")).predicted_fault is False
        assert static_sequence_rules(run_dict(family, "faulty")).predicted_fault is True


def test_runtime_rules_detect_engineered_faults_without_false_alarm() -> None:
    for family in FaultFamily:
        assert runtime_lineage_rules(run_dict(family, "clean")).predicted_fault is False
        assert runtime_lineage_rules(run_dict(family, "faulty")).predicted_fault is True


def test_classification_metrics_include_false_alarm_rate() -> None:
    result = classification_metrics(
        labels=[True, True, False, False],
        predictions=[True, False, True, False],
    )
    assert result.true_positive == 1
    assert result.true_negative == 1
    assert result.false_positive == 1
    assert result.false_negative == 1
    assert result.accuracy == 0.5
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.f1 == 0.5
    assert result.false_positive_rate == 0.5

