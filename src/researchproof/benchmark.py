from __future__ import annotations

import json
import time
import warnings
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from researchproof.datasets import load_dataset
from researchproof.experiment import _index_hash
from researchproof.manifest import BenchmarkManifest, dataset_checksum


class FaultFamily(str, Enum):
    PREPROCESSING_BEFORE_SPLIT = "preprocessing_before_split"
    TRAIN_TEST_OVERLAP = "train_test_overlap"
    TARGET_INFORMED_FEATURE_SELECTION = "target_informed_feature_selection"


def _stable_f_classif(features: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Run ANOVA scoring while assigning zero importance to constant features."""

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Features .* are constant")
        warnings.filterwarnings("ignore", message="invalid value encountered in divide")
        scores, p_values = f_classif(features, target)
    return np.nan_to_num(scores, nan=0.0), np.nan_to_num(p_values, nan=1.0)


@dataclass(frozen=True)
class RuntimeEvidence:
    preprocessing_observed_test_rows: int
    training_observed_test_rows: int
    target_observed_before_split: bool


@dataclass(frozen=True)
class BenchmarkRun:
    case_id: str
    pair_id: str
    dataset_id: str
    fault_family: str
    variant: str
    seed: int
    base_train_hash: str
    base_test_hash: str
    model_fit_rows: int
    operation_trace: tuple[str, ...]
    evidence: RuntimeEvidence
    accuracy: float
    balanced_accuracy: float
    roc_auc: float
    runtime_seconds: float

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def _manifest(
    fault_family: FaultFamily,
    variant: str,
    seed: int,
    checksum: str,
    dataset_id: str,
) -> BenchmarkManifest:
    faulty = variant == "faulty"
    expected_evidence = {
        FaultFamily.PREPROCESSING_BEFORE_SPLIT: "preprocessing_observed_test_rows",
        FaultFamily.TRAIN_TEST_OVERLAP: "training_observed_test_rows",
        FaultFamily.TARGET_INFORMED_FEATURE_SELECTION: "target_observed_before_split",
    }[fault_family]
    repairs = {
        FaultFamily.PREPROCESSING_BEFORE_SPLIT: "fit preprocessing on training rows only",
        FaultFamily.TRAIN_TEST_OVERLAP: "remove evaluation rows from model fitting",
        FaultFamily.TARGET_INFORMED_FEATURE_SELECTION: (
            "fit supervised feature selection on training labels only"
        ),
    }
    return BenchmarkManifest(
        dataset_id=dataset_id,
        dataset_checksum=checksum,
        template_id="logistic_regression_tabular",
        template_version="0.2.0",
        fault_family=fault_family.value,
        injector_version="0.1.0",
        seed=seed,
        split_policy="stratified_random_75_25",
        model_name="logistic_regression",
        model_parameters={"max_iter": 2000, "feature_count": 10},
        expected_fault=faulty,
        expected_evidence=(expected_evidence if faulty else "no_methodological_fault",),
        expected_repair=repairs[fault_family] if faulty else "no repair required",
        environment_lock="pyproject.toml@0.1.0",
    )


def _score(model: Any, x_test: np.ndarray, y_test: np.ndarray) -> tuple[float, float, float]:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)
    if probabilities.shape[1] == 2:
        auc = roc_auc_score(y_test, probabilities[:, 1])
    else:
        auc = roc_auc_score(y_test, probabilities, multi_class="ovr", average="macro")
    return (
        float(accuracy_score(y_test, predictions)),
        float(balanced_accuracy_score(y_test, predictions)),
        float(auc),
    )


def run_benchmark_case(
    fault_family: FaultFamily | str,
    variant: str,
    seed: int,
    *,
    dataset_id: str = "sklearn_breast_cancer",
    test_size: float = 0.25,
    overlap_fraction: float = 0.10,
) -> tuple[BenchmarkManifest, BenchmarkRun]:
    family = FaultFamily(fault_family)
    if variant not in {"clean", "faulty"}:
        raise ValueError("variant must be 'clean' or 'faulty'")
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between zero and one")
    if not 0.0 < overlap_fraction < 1.0:
        raise ValueError("overlap_fraction must be between zero and one")

    dataset = load_dataset(dataset_id)
    features, target, row_ids = dataset.features, dataset.target, dataset.row_ids
    checksum = dataset_checksum(features, target)
    x_train, x_test, y_train, y_test, id_train, id_test = train_test_split(
        features,
        target,
        row_ids,
        test_size=test_size,
        random_state=seed,
        stratify=target,
    )
    started = time.perf_counter()
    preprocessing_test_rows = 0
    training_test_rows = 0
    target_before_split = False
    operation_trace: tuple[str, ...]

    if family is FaultFamily.PREPROCESSING_BEFORE_SPLIT:
        if variant == "faulty":
            scaler = StandardScaler().fit(features)
            x_train_model = scaler.transform(x_train)
            x_test_model = scaler.transform(x_test)
            model = LogisticRegression(max_iter=2000, random_state=seed)
            preprocessing_test_rows = len(id_test)
            operation_trace = (
                "preprocessing_fit_all_rows",
                "train_test_split",
                "model_fit_train_rows",
                "evaluate_test_rows",
            )
        else:
            x_train_model, x_test_model = x_train, x_test
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=2000, random_state=seed),
            )
            operation_trace = (
                "train_test_split",
                "preprocessing_fit_train_rows",
                "model_fit_train_rows",
                "evaluate_test_rows",
            )
        model.fit(x_train_model, y_train)
        model_fit_rows = len(id_train)

    elif family is FaultFamily.TRAIN_TEST_OVERLAP:
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, random_state=seed),
        )
        x_train_model, y_train_model = x_train, y_train
        if variant == "faulty":
            overlap_count = max(1, round(len(id_test) * overlap_fraction))
            x_train_model = np.concatenate((x_train, x_test[:overlap_count]), axis=0)
            y_train_model = np.concatenate((y_train, y_test[:overlap_count]), axis=0)
            training_test_rows = overlap_count
            operation_trace = (
                "train_test_split",
                "append_test_rows_to_training",
                "model_fit_mixed_rows",
                "evaluate_test_rows",
            )
        else:
            operation_trace = (
                "train_test_split",
                "model_fit_train_rows",
                "evaluate_test_rows",
            )
        model.fit(x_train_model, y_train_model)
        x_test_model = x_test
        model_fit_rows = len(x_train_model)

    else:
        if variant == "faulty":
            selector = SelectKBest(score_func=_stable_f_classif, k=10).fit(features, target)
            x_train_model = selector.transform(x_train)
            x_test_model = selector.transform(x_test)
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=2000, random_state=seed),
            )
            target_before_split = True
            operation_trace = (
                "feature_selection_fit_all_labels",
                "train_test_split",
                "model_fit_train_rows",
                "evaluate_test_rows",
            )
        else:
            x_train_model, x_test_model = x_train, x_test
            model = make_pipeline(
                SelectKBest(score_func=_stable_f_classif, k=10),
                StandardScaler(),
                LogisticRegression(max_iter=2000, random_state=seed),
            )
            operation_trace = (
                "train_test_split",
                "feature_selection_fit_train_labels",
                "model_fit_train_rows",
                "evaluate_test_rows",
            )
        model.fit(x_train_model, y_train)
        model_fit_rows = len(id_train)

    accuracy, balanced_accuracy, roc_auc = _score(model, x_test_model, y_test)
    manifest = _manifest(family, variant, seed, checksum, dataset_id)
    pair_material = f"{checksum}:{family.value}:{seed}:logistic_regression_tabular"
    pair_id = f"pair-{__import__('hashlib').sha256(pair_material.encode()).hexdigest()[:16]}"
    run = BenchmarkRun(
        case_id=manifest.case_id,
        pair_id=pair_id,
        dataset_id=dataset_id,
        fault_family=family.value,
        variant=variant,
        seed=seed,
        base_train_hash=_index_hash(id_train),
        base_test_hash=_index_hash(id_test),
        model_fit_rows=model_fit_rows,
        operation_trace=operation_trace,
        evidence=RuntimeEvidence(
            preprocessing_observed_test_rows=preprocessing_test_rows,
            training_observed_test_rows=training_test_rows,
            target_observed_before_split=target_before_split,
        ),
        accuracy=accuracy,
        balanced_accuracy=balanced_accuracy,
        roc_auc=roc_auc,
        runtime_seconds=time.perf_counter() - started,
    )
    return manifest, run


def generate_benchmark(
    seeds: list[int],
    output_dir: Path,
    *,
    dataset_ids: list[str] | None = None,
    test_size: float = 0.25,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir = output_dir / "manifests"
    runs: list[BenchmarkRun] = []
    selected_datasets = dataset_ids or ["sklearn_breast_cancer"]
    for dataset_id in selected_datasets:
        for seed in seeds:
            for family in FaultFamily:
                for variant in ("clean", "faulty"):
                    manifest, run = run_benchmark_case(
                        family,
                        variant,
                        seed,
                        dataset_id=dataset_id,
                        test_size=test_size,
                    )
                    manifest.write(manifests_dir / f"{manifest.case_id}.json")
                    runs.append(run)

    destination = output_dir / "runs.jsonl"
    destination.write_text(
        "".join(json.dumps(run.to_dict(), sort_keys=True) + "\n" for run in runs),
        encoding="utf-8",
    )
    return destination
