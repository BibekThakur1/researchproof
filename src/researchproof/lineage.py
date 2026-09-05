from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LineageEvent:
    operation: str
    stage: str
    observed_row_ids: tuple[int, ...]
    uses_target: bool


@dataclass(frozen=True)
class RuntimeEvidence:
    preprocessing_observed_test_rows: int
    training_observed_test_rows: int
    target_observed_test_rows: int
    target_observed_before_split: bool


class LineageMonitor:
    def __init__(self, train_ids: np.ndarray, test_ids: np.ndarray) -> None:
        self.train_ids = frozenset(int(value) for value in train_ids)
        self.test_ids = frozenset(int(value) for value in test_ids)
        if self.train_ids & self.test_ids:
            raise ValueError("base train and test row IDs must be disjoint")
        self._events: list[LineageEvent] = []

    @property
    def events(self) -> tuple[LineageEvent, ...]:
        return tuple(self._events)

    def record_fit(
        self,
        operation: str,
        stage: str,
        observed_row_ids: np.ndarray,
        *,
        uses_target: bool,
    ) -> None:
        if stage not in {"preprocessing", "selection", "model"}:
            raise ValueError(f"unsupported lineage stage: {stage}")
        observed = tuple(int(value) for value in np.asarray(observed_row_ids).reshape(-1))
        self._events.append(
            LineageEvent(
                operation=operation,
                stage=stage,
                observed_row_ids=observed,
                uses_target=uses_target,
            )
        )

    def summarize(self) -> RuntimeEvidence:
        preprocessing_test: set[int] = set()
        training_test: set[int] = set()
        target_test: set[int] = set()
        for event in self._events:
            observed_test = set(event.observed_row_ids) & self.test_ids
            if event.stage == "preprocessing":
                preprocessing_test.update(observed_test)
            if event.stage == "model":
                training_test.update(observed_test)
            if event.uses_target and event.stage != "model":
                target_test.update(observed_test)
        return RuntimeEvidence(
            preprocessing_observed_test_rows=len(preprocessing_test),
            training_observed_test_rows=len(training_test),
            target_observed_test_rows=len(target_test),
            target_observed_before_split=bool(target_test),
        )

