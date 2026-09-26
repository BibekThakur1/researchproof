import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLASSIFY = runpy.run_path(str(ROOT / "scripts/run_mlscent_baseline.py"))["classify"]


def test_skip_is_unknown_not_negative():
    assert CLASSIFY([], "Skipping ML smell detection: No ML-related packages imported", "ml") == {
        "status": "skipped_no_import",
        "prediction": None,
    }


def test_caught_error_is_unknown_not_negative():
    assert CLASSIFY([], "Unexpected error while processing file", "ml")["prediction"] is None


def test_positive_evidence_survives_later_error():
    result = [{"smell": "Potential data leakage: Preprocessing applied before train-test split"}]
    verdict = CLASSIFY(result, "Unexpected error later", "ml")
    assert verdict == {"status": "error", "prediction": True}


@pytest.mark.parametrize(
    "component, result, expected",
    [
        ("ml", [{"smell": "Magic number detected"}], False),
        ("framework", [{"name": "Data Leakage Checker"}], True),
        ("framework", [{"name": "Missing Random Seed"}], False),
    ],
)
def test_category_mapping(component, result, expected):
    assert CLASSIFY(result, "", component)["prediction"] is expected


def test_downstream_fit_does_not_remove_leaked_scaler_state():
    path = ROOT / "examples/mlscent_preprocessing_control.py"
    text = path.read_text()
    prefix = {}
    exec(compile(text.split("# DOWNSTREAM")[0], str(path), "exec"), prefix)
    full = runpy.run_path(str(path))
    assert prefix["scaler"].n_samples_seen_ == full["scaler"].n_samples_seen_
    assert full["scaler"].n_samples_seen_ > len(full["x_train"])
