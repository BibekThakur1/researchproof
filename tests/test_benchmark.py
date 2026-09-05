import pytest

from researchproof.benchmark import (
    FaultFamily,
    FaultSeverity,
    generate_benchmark,
    run_benchmark_case,
)
from researchproof.manifest import BenchmarkManifest


@pytest.mark.parametrize("family", list(FaultFamily))
def test_paired_cases_share_dataset_split_and_pair_id(family: FaultFamily) -> None:
    clean_manifest, clean = run_benchmark_case(family, "clean", seed=7)
    faulty_manifest, faulty = run_benchmark_case(family, "faulty", seed=7)

    assert clean.base_train_hash == faulty.base_train_hash
    assert clean.base_test_hash == faulty.base_test_hash
    assert clean.pair_id == faulty.pair_id
    assert clean_manifest.dataset_checksum == faulty_manifest.dataset_checksum
    assert clean_manifest.expected_fault is False
    assert faulty_manifest.expected_fault is True


def test_preprocessing_fault_exposes_only_faulty_test_rows() -> None:
    _, clean = run_benchmark_case(FaultFamily.PREPROCESSING_BEFORE_SPLIT, "clean", 7)
    _, faulty = run_benchmark_case(FaultFamily.PREPROCESSING_BEFORE_SPLIT, "faulty", 7)
    assert clean.evidence.preprocessing_observed_test_rows == 0
    assert 0 < faulty.evidence.preprocessing_observed_test_rows < faulty.model_fit_rows


def test_overlap_fault_adds_evaluation_rows_to_model_fit() -> None:
    _, clean = run_benchmark_case(FaultFamily.TRAIN_TEST_OVERLAP, "clean", 7)
    _, faulty = run_benchmark_case(FaultFamily.TRAIN_TEST_OVERLAP, "faulty", 7)
    assert clean.evidence.training_observed_test_rows == 0
    assert faulty.evidence.training_observed_test_rows > 0
    assert faulty.model_fit_rows > clean.model_fit_rows


def test_target_informed_selection_observes_labels_before_split() -> None:
    _, clean = run_benchmark_case(FaultFamily.TARGET_INFORMED_FEATURE_SELECTION, "clean", 7)
    _, faulty = run_benchmark_case(FaultFamily.TARGET_INFORMED_FEATURE_SELECTION, "faulty", 7)
    assert clean.evidence.target_observed_before_split is False
    assert faulty.evidence.target_observed_before_split is True


@pytest.mark.parametrize("family", list(FaultFamily))
@pytest.mark.parametrize("variant", ["clean", "faulty"])
def test_all_metrics_are_bounded(family: FaultFamily, variant: str) -> None:
    _, run = run_benchmark_case(family, variant, seed=19)
    assert 0.0 <= run.accuracy <= 1.0
    assert 0.0 <= run.balanced_accuracy <= 1.0
    assert 0.0 <= run.roc_auc <= 1.0


def test_generator_writes_six_cases_per_seed(tmp_path) -> None:
    index = generate_benchmark([7, 19], tmp_path)
    lines = index.read_text(encoding="utf-8").splitlines()
    manifests = sorted((tmp_path / "manifests").glob("*.json"))

    assert len(lines) == 12
    assert len(manifests) == 12
    assert all(BenchmarkManifest.read(path).case_id == path.stem for path in manifests)


def test_generator_supports_multiple_datasets(tmp_path) -> None:
    index = generate_benchmark(
        [7],
        tmp_path,
        dataset_ids=["sklearn_breast_cancer", "sklearn_wine"],
    )
    lines = index.read_text(encoding="utf-8").splitlines()
    manifests = [BenchmarkManifest.read(path) for path in (tmp_path / "manifests").glob("*.json")]
    assert len(lines) == 12
    assert {manifest.dataset_id for manifest in manifests} == {
        "sklearn_breast_cancer",
        "sklearn_wine",
    }


@pytest.mark.parametrize("family", list(FaultFamily))
def test_fault_severity_increases_observed_contamination(family: FaultFamily) -> None:
    counts = []
    for severity in FaultSeverity:
        _, run = run_benchmark_case(family, "faulty", seed=7, severity=severity)
        evidence = run.evidence
        counts.append(
            evidence.preprocessing_observed_test_rows
            or evidence.training_observed_test_rows
            or evidence.target_observed_test_rows
        )
    assert counts[0] < counts[1] < counts[2]


def test_generator_crosses_cases_with_severity_levels(tmp_path) -> None:
    index = generate_benchmark(
        [7],
        tmp_path,
        severities=["low", "medium", "high"],
    )
    assert len(index.read_text(encoding="utf-8").splitlines()) == 18
