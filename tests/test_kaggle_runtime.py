"""Simulate startup failures without Kaggle access, package installation or model training."""

import json
import runpy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


def runtime(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/kaggle_runtime.py"
    namespace = runpy.run_path(str(path))
    context = namespace["main"].__globals__
    monkeypatch.setitem(context, "require_kaggle", lambda: None)
    monkeypatch.setitem(context, "STATE", tmp_path / "state.json")
    monkeypatch.setitem(context, "DIAGNOSTICS", tmp_path / "startup.json")
    monkeypatch.setattr(context["platform"], "platform", lambda: "test fixture")
    monkeypatch.setattr(
        context["shutil"], "disk_usage", lambda path: SimpleNamespace(free=20 * 1024**3)
    )
    return context


def test_gpu_failure_stops_before_any_download(tmp_path, monkeypatch):
    context = runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=2, stdout='{"cuda":false}', stderr=""),
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Network must not run after a CUDA failure")

    monkeypatch.setattr(context["urllib"].request, "urlopen", forbidden)
    with pytest.raises(RuntimeError, match="CUDA check failed"):
        context["preflight"]()
    status = json.loads((tmp_path / "state.json").read_text())
    assert status["status"] == "failed"
    assert status["reason"] == "host_pytorch_cuda_unavailable"
    assert json.loads((tmp_path / "startup.json").read_text())["cuda_check"]["exit_code"] == 2


def test_internet_failure_preserves_diagnostic(tmp_path, monkeypatch):
    context = runtime(tmp_path, monkeypatch)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(
            returncode=0, stdout='{"cuda":true,"devices":["fixture"]}', stderr=""
        ),
    )

    def offline(*args, **kwargs):
        raise OSError("simulated offline runtime")

    monkeypatch.setattr(context["urllib"].request, "urlopen", offline)
    with pytest.raises(RuntimeError, match="enable notebook Internet"):
        context["preflight"]()
    diagnostic = json.loads((tmp_path / "startup.json").read_text())
    assert diagnostic["figshare"]["reachable"] is False
    assert json.loads((tmp_path / "state.json").read_text())["status"] == "failed"


def test_missing_setup_cannot_start_training(tmp_path, monkeypatch):
    context = runtime(tmp_path, monkeypatch)
    (tmp_path / "state.json").write_text('{"stage":"preflight","status":"passed"}')

    def forbidden(*args, **kwargs):
        pytest.fail("Training command must not execute without successful setup")

    monkeypatch.setitem(context, "run", forbidden)
    with pytest.raises(RuntimeError, match="Successful setup"):
        context["train"]()
