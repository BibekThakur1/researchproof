"""Explicit score-to-selection provenance for an instrumented, finite workflow.

This API checks observed selection reuse, not general experiment validity. Callers
must propagate every selection decision. It does not instrument arbitrary Python.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

Rows = frozenset[tuple[str, int]]


def row_keys(dataset: str, ids: list[int]) -> Rows:
    if not dataset or not ids:
        raise ValueError("dataset namespace and non-empty row IDs are required")
    return frozenset((dataset, int(row)) for row in ids)


@dataclass(frozen=True)
class ModelState:
    model_id: str
    selection_rows: Rows = frozenset()
    complete: bool = True


@dataclass(frozen=True)
class Score:
    value: float
    observed_rows: Rows
    complete: bool = True

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise ValueError("score must be finite")


@dataclass(frozen=True)
class Verdict:
    status: Literal["selection_reuse", "no_observed_selection_reuse", "insufficient_evidence"]
    reused_rows: int


def combine_scores(scores: list[Score]) -> Score:
    """Mean used by a decision; retain every contributing score's row provenance."""
    if not scores:
        raise ValueError("at least one score is required")
    return Score(
        sum(score.value for score in scores) / len(scores),
        frozenset().union(*(score.observed_rows for score in scores)),
        all(score.complete for score in scores),
    )


def choose_model(candidates: list[ModelState], scores: list[Score]) -> ModelState:
    """Argmax with stable first-candidate ties; all comparisons influence selection."""
    if not candidates or len(candidates) != len(scores):
        raise ValueError("one score per candidate is required")
    winner = max(range(len(scores)), key=lambda index: scores[index].value)
    return decision(candidates[winner], candidates, scores)


def decision(chosen: ModelState, candidates: list[ModelState], evidence: list[Score]) -> ModelState:
    """Record an explicit branch, threshold, or selection decision."""
    if chosen not in candidates or not evidence:
        raise ValueError("chosen model and decision evidence are required")
    rows = frozenset().union(
        *(model.selection_rows for model in candidates),
        *(score.observed_rows for score in evidence),
    )
    return ModelState(
        chosen.model_id,
        rows,
        all(model.complete for model in candidates) and all(s.complete for s in evidence),
    )


def audit_report(model: ModelState, score: Score) -> Verdict:
    overlap = model.selection_rows & score.observed_rows
    if overlap:
        return Verdict("selection_reuse", len(overlap))
    if not model.complete or not score.complete:
        return Verdict("insufficient_evidence", 0)
    return Verdict("no_observed_selection_reuse", 0)
