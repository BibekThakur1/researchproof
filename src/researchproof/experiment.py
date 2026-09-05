from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class RunResult:
    variant: str
    seed: int
    train_rows: int
    test_rows: int
    train_index_hash: str
    test_index_hash: str
    accuracy: float
    balanced_accuracy: float
    roc_auc: float
    runtime_seconds: float


def _index_hash(values: np.ndarray) -> str:
    normalized = ",".join(str(int(value)) for value in np.sort(values))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_pilot_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dataset = load_breast_cancer()
    rows = np.arange(dataset.data.shape[0])
    return dataset.data, dataset.target, rows


def run_variant(variant: str, seed: int, test_size: float, max_iter: int) -> RunResult:
    if variant not in {"clean", "faulty"}:
        raise ValueError("variant must be 'clean' or 'faulty'")

    features, target, row_ids = load_pilot_data()
    started = time.perf_counter()

    if variant == "faulty":
        # Intentionally invalid for benchmark construction: the scaler observes test rows.
        features = StandardScaler().fit_transform(features)

    x_train, x_test, y_train, y_test, id_train, id_test = train_test_split(
        features,
        target,
        row_ids,
        test_size=test_size,
        random_state=seed,
        stratify=target,
    )

    if variant == "clean":
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=max_iter, random_state=seed),
        )
    else:
        model = LogisticRegression(max_iter=max_iter, random_state=seed)

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]

    return RunResult(
        variant=variant,
        seed=seed,
        train_rows=len(id_train),
        test_rows=len(id_test),
        train_index_hash=_index_hash(id_train),
        test_index_hash=_index_hash(id_test),
        accuracy=float(accuracy_score(y_test, predictions)),
        balanced_accuracy=float(balanced_accuracy_score(y_test, predictions)),
        roc_auc=float(roc_auc_score(y_test, probabilities)),
        runtime_seconds=time.perf_counter() - started,
    )


def run_pilot(config: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[RunResult] = []
    for seed in config["seeds"]:
        for variant in ("clean", "faulty"):
            results.append(
                run_variant(
                    variant=variant,
                    seed=int(seed),
                    test_size=float(config["test_size"]),
                    max_iter=int(config["model"]["max_iter"]),
                )
            )

    payload = {
        "status": "pilot_data_not_a_research_finding",
        "config": config,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "runs": [asdict(result) for result in results],
    }
    destination = output_dir / "results.json"
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination

