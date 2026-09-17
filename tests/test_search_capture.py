import numpy as np
import pytest
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from researchproof.datasets import load_dataset
from researchproof.score_store import load_scores, save_scores
from researchproof.search_capture import capture_grid_search
from researchproof.selection_provenance import ModelState, Score, audit_report, row_keys


def run(prior=None, **overrides):
    data = load_dataset("sklearn_wine")
    arguments = dict(
        dataset="wine",
        row_ids=data.row_ids + 1000,
        splits=list(StratifiedKFold(3).split(data.features, data.target)),
        prior=prior,
    )
    arguments.update(overrides)
    return capture_grid_search(
        DecisionTreeClassifier(random_state=0),
        {"max_depth": [1, 3]},
        data.features,
        data.target,
        **arguments,
    )


def test_library_winner_and_all_validation_origins():
    result = run(ModelState("predeclared"))
    assert int(result.selected.model_id) == result.search.best_index_
    assert result.selected.selection_rows == row_keys("wine", list(range(1000, 1178)))
    assert audit_report(result.selected, Score(0.5, row_keys("wine", [1000]))).status == (
        "selection_reuse"
    )
    assert audit_report(result.selected, Score(0.5, row_keys("wine", [999]))).status == (
        "no_observed_selection_reuse"
    )


def test_unknown_history_cannot_certify_fresh_report():
    result = run()
    assert audit_report(result.selected, Score(0.5, row_keys("wine", [999]))).status == (
        "insufficient_evidence"
    )


def test_prior_history_and_persistence(tmp_path):
    result = run(ModelState("prior", row_keys("older", [7])))
    path = tmp_path / "selected.json"
    save_scores(path, [result.selected], [result.scores[int(result.selected.model_id)]])
    models, _ = load_scores(path)
    assert audit_report(models[0], Score(0.5, row_keys("older", [7]))).status == "selection_reuse"


@pytest.mark.parametrize(
    "splits", [[], [([0, 1], [1, 2])], [([0], [178])], [([0], [1.5])], [([0, 0], [1])]]
)
def test_bad_splits_rejected(splits):
    with pytest.raises(ValueError):
        run(splits=splits)


@pytest.mark.parametrize("ids", [np.zeros(178, dtype=int), np.arange(178) + 0.5])
def test_bad_identity_rejected(ids):
    with pytest.raises(ValueError):
        run(row_ids=ids)
