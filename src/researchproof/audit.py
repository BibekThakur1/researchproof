from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditDecision:
    predicted_fault: bool
    risk_score: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ClassificationMetrics:
    cases: int
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float


Auditor = Callable[[dict[str, Any]], AuditDecision]


def always_clean(_: dict[str, Any]) -> AuditDecision:
    return AuditDecision(predicted_fault=False, risk_score=0.0, evidence=())


def static_sequence_rules(run: dict[str, Any]) -> AuditDecision:
    trace = set(run.get("operation_trace", ()))
    suspicious = tuple(
        sorted(
            trace
            & {
                "preprocessing_fit_all_rows",
                "append_test_rows_to_training",
                "model_fit_mixed_rows",
                "feature_selection_fit_all_labels",
            }
        )
    )
    return AuditDecision(
        predicted_fault=bool(suspicious),
        risk_score=1.0 if suspicious else 0.0,
        evidence=suspicious,
    )


def runtime_lineage_rules(run: dict[str, Any]) -> AuditDecision:
    evidence = run.get("evidence", {})
    triggered: list[str] = []
    if int(evidence.get("preprocessing_observed_test_rows", 0)) > 0:
        triggered.append("preprocessing_observed_test_rows")
    if int(evidence.get("training_observed_test_rows", 0)) > 0:
        triggered.append("training_observed_test_rows")
    if bool(evidence.get("target_observed_before_split", False)):
        triggered.append("target_observed_before_split")
    return AuditDecision(
        predicted_fault=bool(triggered),
        risk_score=1.0 if triggered else 0.0,
        evidence=tuple(triggered),
    )


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def classification_metrics(
    labels: Iterable[bool], predictions: Iterable[bool]
) -> ClassificationMetrics:
    pairs = list(zip(labels, predictions, strict=True))
    true_positive = sum(label and prediction for label, prediction in pairs)
    true_negative = sum(not label and not prediction for label, prediction in pairs)
    false_positive = sum(not label and prediction for label, prediction in pairs)
    false_negative = sum(label and not prediction for label, prediction in pairs)
    precision = _safe_divide(true_positive, true_positive + false_positive)
    recall = _safe_divide(true_positive, true_positive + false_negative)
    return ClassificationMetrics(
        cases=len(pairs),
        true_positive=true_positive,
        true_negative=true_negative,
        false_positive=false_positive,
        false_negative=false_negative,
        accuracy=_safe_divide(true_positive + true_negative, len(pairs)),
        precision=precision,
        recall=recall,
        f1=_safe_divide(2 * precision * recall, precision + recall),
        false_positive_rate=_safe_divide(false_positive, false_positive + true_negative),
    )


def evaluate_auditor(runs: list[dict[str, Any]], auditor: Auditor) -> ClassificationMetrics:
    labels = [run["variant"] == "faulty" for run in runs]
    predictions = [auditor(run).predicted_fault for run in runs]
    return classification_metrics(labels, predictions)


def evaluate_baselines(index: Path, destination: Path) -> Path:
    runs = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
    auditors: dict[str, Auditor] = {
        "always_clean": always_clean,
        "static_sequence_rules": static_sequence_rules,
        "runtime_lineage_rules": runtime_lineage_rules,
    }
    report: dict[str, Any] = {
        "status": "engineering_sanity_check_not_a_research_finding",
        "source": str(index),
        "overall": {},
        "by_fault_family": {},
    }
    for name, auditor in auditors.items():
        report["overall"][name] = asdict(evaluate_auditor(runs, auditor))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[run["fault_family"]].append(run)
    for family, family_runs in sorted(grouped.items()):
        report["by_fault_family"][family] = {
            name: asdict(evaluate_auditor(family_runs, auditor))
            for name, auditor in auditors.items()
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
