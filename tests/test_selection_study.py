from researchproof.selection_study import run_study


def test_study_preserves_disjoint_data_and_unknown_cases():
    records, summary = run_study([7])
    assert len(records) == 162
    assert summary["labelled"] == 144
    for row in records:
        groups = [set(ids) for ids in row["partitions"].values()]
        assert sum(map(len, groups)) == len(set().union(*groups))
        if row["scenario"] == "missing_history":
            assert row["expected_selection_reuse"] is None
            assert row["predictions"]["selection_provenance"] is None
        assert 0 <= row["reported_accuracy"] <= 1


def test_same_score_and_row_ids_different_decision_change_verdict():
    from researchproof.selection_provenance import ModelState, Score, audit_report, choose_model

    fixed = ModelState("a")
    score = Score(0.8, frozenset({("d", 1)}))
    assert audit_report(fixed, score).status == "no_observed_selection_reuse"
    chosen = choose_model([fixed, ModelState("b")], [score, Score(0.7, score.observed_rows)])
    assert audit_report(chosen, score).status == "selection_reuse"
