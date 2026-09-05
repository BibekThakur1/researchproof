from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_breast_cancer, load_digits, load_wine
from sklearn.utils import Bunch


@dataclass(frozen=True)
class LoadedDataset:
    dataset_id: str
    features: np.ndarray
    target: np.ndarray
    row_ids: np.ndarray


_LOADERS: dict[str, Callable[[], Bunch]] = {
    "sklearn_breast_cancer": load_breast_cancer,
    "sklearn_wine": load_wine,
    "sklearn_digits": load_digits,
}


def available_datasets() -> tuple[str, ...]:
    return tuple(sorted(_LOADERS))


def load_dataset(dataset_id: str) -> LoadedDataset:
    try:
        loader = _LOADERS[dataset_id]
    except KeyError as error:
        available = ", ".join(available_datasets())
        raise ValueError(f"unknown dataset {dataset_id!r}; choose one of: {available}") from error
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Setting the shape on a NumPy array has been deprecated",
            category=DeprecationWarning,
        )
        dataset = loader()
    features = np.asarray(dataset.data)
    target = np.asarray(dataset.target)
    return LoadedDataset(
        dataset_id=dataset_id,
        features=features,
        target=target,
        row_ids=np.arange(features.shape[0]),
    )
