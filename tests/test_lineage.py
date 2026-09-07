import numpy as np
import pytest

from researchproof.lineage import LineageMonitor


def test_lineage_summary_counts_unique_observed_test_rows() -> None:
    monitor = LineageMonitor(np.array([0, 1, 2]), np.array([3, 4]))
    monitor.record_fit(
        "scaler.fit", "preprocessing", np.array([0, 1, 3, 3]), uses_target=False
    )
    monitor.record_fit("model.fit", "model", np.array([0, 1, 4]), uses_target=True)
    evidence = monitor.summarize()
    assert evidence.preprocessing_observed_test_rows == 1
    assert evidence.training_observed_test_rows == 1
    assert evidence.target_observed_test_rows == 0
    assert evidence.test_evaluation_count == 0


def test_supervised_selection_records_test_target_access() -> None:
    monitor = LineageMonitor(np.array([0, 1]), np.array([2, 3]))
    monitor.record_fit("selector.fit", "selection", np.array([0, 1, 2]), uses_target=True)
    evidence = monitor.summarize()
    assert evidence.target_observed_test_rows == 1
    assert evidence.target_observed_before_split is True


def test_overlapping_base_split_is_rejected() -> None:
    with pytest.raises(ValueError, match="disjoint"):
        LineageMonitor(np.array([0, 1]), np.array([1, 2]))


def test_lineage_counts_test_evaluation_events_not_unique_rows() -> None:
    monitor = LineageMonitor(np.array([0, 1]), np.array([2, 3]))
    monitor.record_evaluation("candidate.score", np.array([2, 3]))
    monitor.record_evaluation("final.score", np.array([2, 3]))
    evidence = monitor.summarize()
    assert evidence.test_evaluation_count == 2
