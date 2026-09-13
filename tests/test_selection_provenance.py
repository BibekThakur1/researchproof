import pytest

from researchproof.selection_provenance import (
    ModelState,
    Score,
    audit_report,
    choose_model,
    combine_scores,
    decision,
    row_keys,
)


def test_same_row_ids_in_different_datasets_are_disjoint():
    selected = choose_model([ModelState("a")], [Score(0.8, row_keys("a", [1, 2]))])
    assert audit_report(selected, Score(0.9, row_keys("b", [1, 2]))).reused_rows == 0


def test_losing_candidate_test_score_still_influences_choice():
    rows = row_keys("d", [1, 2])
    chosen = choose_model(
        [ModelState("a"), ModelState("b")],
        [Score(0.9, row_keys("d", [3])), Score(0.1, rows)],
    )
    assert audit_report(chosen, Score(0.5, rows)).status == "selection_reuse"


def test_repeated_scoring_without_selection_does_not_taint_model():
    model = ModelState("a")
    score = Score(0.8, row_keys("d", [1, 2]))
    for _ in range(10):
        assert audit_report(model, score).status == "no_observed_selection_reuse"


def test_single_threshold_and_fresh_holdout():
    a, b = ModelState("a"), ModelState("b")
    score = Score(0.8, row_keys("d", [1, 2]))
    chosen = decision(a if score.value > 0.7 else b, [a, b], [score])
    assert audit_report(chosen, score).status == "selection_reuse"
    fresh = Score(0.8, row_keys("d", [3, 4]))
    assert audit_report(chosen, fresh).status == "no_observed_selection_reuse"


def test_unknown_trace_abstains_and_score_composition_preserves_origin():
    rows = row_keys("d", [1])
    assert audit_report(ModelState("a", complete=False), Score(0.5, rows)).status == (
        "insufficient_evidence"
    )
    aggregate = combine_scores([Score(0.2, rows), Score(0.8, row_keys("d", [2]))])
    selected = choose_model([ModelState("a")], [aggregate])
    assert audit_report(selected, Score(0.7, rows)).reused_rows == 1


def test_invalid_decision_and_nonfinite_score_rejected():
    with pytest.raises(ValueError):
        choose_model([ModelState("a")], [])
    with pytest.raises(ValueError):
        Score(float("nan"), row_keys("d", [1]))
