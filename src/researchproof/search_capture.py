"""Explicit GridSearchCV boundary; no claim of whole-program completeness.

Supports dense arrays, explicit disjoint positional splits, accuracy scoring and
no refit. Captures validation-score origins, not training/preprocessing leakage.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.model_selection import GridSearchCV

from researchproof.selection_provenance import ModelState, Score, choose_model, row_keys


@dataclass
class CapturedSearch:
    search: GridSearchCV
    candidates: list[ModelState]
    scores: list[Score]
    selected: ModelState


def capture_grid_search(
    estimator, param_grid, X, y, *, dataset, row_ids, splits, prior: ModelState | None = None
) -> CapturedSearch:
    """Capture score dependencies automatically inside this declared boundary.

    Unknown pre-boundary history defaults to incomplete. A supplied prior applies
    to every candidate; callers must include earlier data-dependent choices there.
    """
    X, y, ids = np.asarray(X), np.asarray(y), np.asarray(row_ids)
    if X.ndim != 2 or y.ndim != 1 or len(X) != len(y):
        raise ValueError("aligned dense feature matrix and target vector required")
    if ids.ndim != 1 or len(ids) != len(X) or ids.dtype.kind not in "iu":
        raise ValueError("one integer row identity per input row required")
    if len(set(ids.tolist())) != len(ids):
        raise ValueError("row identities must be unique")
    if not isinstance(dataset, str) or not dataset:
        raise ValueError("dataset namespace required")
    checked = []
    origins = set()
    for train, test in splits:
        train, test = np.asarray(train), np.asarray(test)
        for positions in (train, test):
            if (
                positions.ndim != 1
                or not len(positions)
                or positions.dtype.kind not in "iu"
                or np.any(positions < 0)
                or np.any(positions >= len(X))
                or len(set(positions.tolist())) != len(positions)
            ):
                raise ValueError("split positions must be nonempty unique in-range integers")
        if set(train.tolist()) & set(test.tolist()):
            raise ValueError("overlapping train/validation split unsupported")
        checked.append((train, test))
        origins.update(ids[test].tolist())
    if not checked:
        raise ValueError("at least one split required")
    search = GridSearchCV(
        estimator,
        param_grid,
        cv=checked,
        scoring="accuracy",
        refit=False,
        n_jobs=1,
        error_score="raise",
    ).fit(X, y)
    history = prior if prior is not None else ModelState("unknown", complete=False)
    candidates = [
        ModelState(str(i), history.selection_rows, history.complete)
        for i in range(len(search.cv_results_["params"]))
    ]
    scores = [
        Score(float(value), row_keys(dataset, sorted(origins)))
        for value in search.cv_results_["mean_test_score"]
    ]
    selected = choose_model(candidates, scores)
    if int(selected.model_id) != int(search.best_index_):
        raise RuntimeError("captured selection disagrees with GridSearchCV")
    return CapturedSearch(search, candidates, scores, selected)
