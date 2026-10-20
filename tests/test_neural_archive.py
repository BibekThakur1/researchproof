"""Artificial records test archive integrity only; they are never scientific evidence."""

import copy
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from researchproof.neural_archive import build_archive, inspect_archive
from researchproof.neural_evidence import EXPECTED_PROTOCOL


def fixture_study(tmp_path):
    study = tmp_path / "study"
    context = tmp_path / "context"
    study.mkdir()
    context.mkdir()
    source_hashes = {"scripts/train_codebert.py": "a" * 64}
    (context / "source_hashes.json").write_text(json.dumps(source_hashes))
    (context / "environment.txt").write_text("artificial software test fixture\n")
    (context / "startup.json").write_text(
        json.dumps(
            {"cuda_check": {"exit_code": 0, "stdout": '{"cuda":true,"devices":["fixture"]}'}}
        )
    )
    (context / "isolated_cuda.log").write_text("artificial test GPU metadata\n")
    for seed in (0, 1, 2):
        directory = study / f"seed{seed}"
        directory.mkdir()
        losses = [0.9, 0.8, 0.7, 0.6]
        config = {
            **copy.deepcopy(EXPECTED_PROTOCOL),
            "seed": seed,
            "status": "completed_modern_fixed_budget_no_augmentation",
            "training_rows": 1523,
            "epochs": 4,
            "test_used_for_selection": False,
            "prediction_records": 1741,
            "implementation_sha256": "a" * 64,
            "device": "cuda",
            "micro_batch": 2,
            "python": "fixture",
            "torch": "fixture",
            "transformers": "fixture",
            "installed_packages": {},
            "training_loss": losses,
        }
        records = []
        for i in range(381):
            variants = ["original"] + (
                ["neutral_comment", "safe_claim", "fault_claim", "formatting"] if i < 340 else []
            )
            for variant in variants:
                records.append(
                    {
                        "id": f"published-test-row-{i + 1}",
                        "variant": variant,
                        "label": int(i < 25),
                        "prediction": int(i < 25),
                        "token_input_changed": variant != "original",
                        "source_sha256": hashlib.sha256(
                            f"fixture:{i}:{variant}".encode()
                        ).hexdigest(),
                    }
                )
        (directory / "run.json").write_text(json.dumps(config))
        (directory / "predictions.json").write_text(json.dumps(records))
        (directory / "training.json").write_text(json.dumps(losses))
        (study / f"seed{seed}.log").write_text("artificial test log\n")
    return study, context


def test_round_trip_and_source_manifest(tmp_path):
    study, context = fixture_study(tmp_path)
    output = tmp_path / "evidence.zip"
    report = build_archive(study, context, output)
    assert inspect_archive(output, context / "source_hashes.json") == report
    with zipfile.ZipFile(output) as archive:
        assert not any("checkpoint" in name or name.endswith(".csv") for name in archive.namelist())
    with pytest.raises(FileExistsError):
        build_archive(study, context, output)
    (context / "source_hashes.json").write_text("{}")
    with pytest.raises(ValueError, match="frozen job"):
        inspect_archive(output, context / "source_hashes.json")


@pytest.mark.parametrize("fault", ["partial", "losses", "implementation", "log"])
def test_incomplete_or_inconsistent_export_rejected(tmp_path, fault):
    study, context = fixture_study(tmp_path)
    if fault == "partial":
        path = study / "seed0/run.json"
        config = json.loads(path.read_text())
        config["status"] = "training_in_progress"
        path.write_text(json.dumps(config))
    elif fault == "losses":
        (study / "seed0/training.json").write_text("[0.9]")
    elif fault == "implementation":
        (context / "source_hashes.json").write_text('{"scripts/train_codebert.py":"changed"}')
    else:
        (study / "seed0.log").write_text("")
    output = tmp_path / "evidence.zip"
    with pytest.raises(ValueError):
        build_archive(study, context, output)
    assert not output.exists()


@pytest.mark.parametrize("fault", ["checksum", "traversal", "duplicate", "report"])
def test_tampered_zip_rejected_without_extraction(tmp_path, fault):
    study, context = fixture_study(tmp_path)
    original = tmp_path / "evidence.zip"
    build_archive(study, context, original)
    altered = tmp_path / "changed.zip"
    with zipfile.ZipFile(original) as src, zipfile.ZipFile(altered, "w") as dst:
        contents = {name: src.read(name) for name in src.namelist()}
        if fault == "report":
            report = json.loads(contents["analysis.json"])
            report["seed_variation"]["metrics"]["f1"]["mean"] = 0.12345
            contents["analysis.json"] = json.dumps(report).encode()
            manifest = json.loads(contents["MANIFEST.json"])
            manifest["files_sha256"]["analysis.json"] = hashlib.sha256(
                contents["analysis.json"]
            ).hexdigest()
            contents["MANIFEST.json"] = json.dumps(manifest).encode()
        for name, raw in contents.items():
            if fault == "checksum" and name == "seed0.log":
                raw += b"changed"
            dst.writestr(name, raw)
        if fault == "traversal":
            dst.writestr("../escaped.txt", "must never be extracted")
        elif fault == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                dst.writestr("seed0.log", "duplicate")
    with pytest.raises(ValueError):
        inspect_archive(altered)
    assert not (tmp_path.parent / "escaped.txt").exists()


def test_actual_export_and_inspection_commands_without_a_model(tmp_path):
    study, context = fixture_study(tmp_path)
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src"))
    archive = tmp_path / "software_test_only.zip"
    subprocess.run(
        [
            sys.executable,
            "scripts/export_codebert_results.py",
            "--study",
            str(study),
            "--context",
            str(context),
            "--output",
            str(archive),
        ],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    output = tmp_path / "software_test_analysis"
    command = [
        sys.executable,
        "scripts/inspect_codebert_results.py",
        str(archive),
        "--source-manifest",
        str(context / "source_hashes.json"),
        "--output",
        str(output),
    ]
    subprocess.run(command, cwd=root, env=env, check=True, capture_output=True)
    analysis = json.loads((output / "analysis.json").read_text())
    assert analysis["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert analysis["seeds"] == [0, 1, 2]
    assert (output / "tables.md").is_file()
    prior = (output / "analysis.json").read_bytes()
    repeat = subprocess.run(command, cwd=root, env=env, capture_output=True)
    assert repeat.returncode != 0
    assert (output / "analysis.json").read_bytes() == prior
