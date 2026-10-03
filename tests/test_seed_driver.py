import json
import runpy
from pathlib import Path

import pytest

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/run_codebert_seeds.py"))


def test_seed_driver_rejects_preflight_directory(tmp_path):
    (tmp_path / "run.json").write_text(
        json.dumps({"seed": 0, "status": "preflight_two_training_rows_not_research"})
    )
    (tmp_path / "predictions.json").write_text("[]")
    with pytest.raises(ValueError, match="completed full"):
        MODULE["validate_directory"](tmp_path, 0)


def test_seed_driver_rejects_wrong_seed(tmp_path):
    (tmp_path / "run.json").write_text(json.dumps({"seed": 1}))
    with pytest.raises(ValueError, match="seed"):
        MODULE["validate_directory"](tmp_path, 0)


def test_seed_driver_rejects_missing_metadata(tmp_path):
    with pytest.raises(FileNotFoundError):
        MODULE["validate_directory"](tmp_path, 0)
