import json

import numpy as np
import pytest

from researchproof.manifest import BenchmarkManifest, ManifestError, dataset_checksum


def make_manifest(**overrides: object) -> BenchmarkManifest:
    values = {
        "dataset_id": "sklearn_breast_cancer",
        "dataset_checksum": "a" * 64,
        "template_id": "logistic_regression_standardized",
        "template_version": "0.1.0",
        "fault_family": "preprocessing_before_split",
        "injector_version": "0.1.0",
        "seed": 7,
        "split_policy": "stratified_random_75_25",
        "model_name": "logistic_regression",
        "model_parameters": {"max_iter": 2000},
        "expected_fault": True,
        "expected_evidence": ("scaler_fit_scope_includes_test_rows",),
        "expected_repair": "fit preprocessing on training rows only",
        "environment_lock": "pyproject.toml@0.1.0",
    }
    values.update(overrides)
    return BenchmarkManifest(**values)


def test_case_id_is_deterministic_and_content_addressed() -> None:
    first = make_manifest()
    second = make_manifest()
    changed = make_manifest(seed=19)

    assert first.case_id == second.case_id
    assert first.case_id != changed.case_id


def test_manifest_round_trip_checks_case_id(tmp_path) -> None:
    source = make_manifest()
    path = tmp_path / "manifest.json"
    source.write(path)

    restored = BenchmarkManifest.read(path)
    assert restored == source
    assert json.loads(path.read_text())["case_id"] == source.case_id


def test_tampered_manifest_is_rejected(tmp_path) -> None:
    manifest = make_manifest()
    payload = manifest.to_dict(include_case_id=True)
    payload["seed"] = 43
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ManifestError, match="case_id"):
        BenchmarkManifest.read(path)


def test_invalid_checksum_is_rejected() -> None:
    with pytest.raises(ManifestError, match="SHA-256"):
        make_manifest(dataset_checksum="not-a-checksum")


def test_dataset_checksum_changes_with_content_and_shape() -> None:
    features = np.array([[1.0, 2.0], [3.0, 4.0]])
    target = np.array([0, 1])

    original = dataset_checksum(features, target)
    assert original == dataset_checksum(features.copy(), target.copy())
    assert original != dataset_checksum(features + 1.0, target)
    assert original != dataset_checksum(features.reshape(1, 4), target)

