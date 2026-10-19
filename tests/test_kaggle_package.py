"""Packaging checks only: these tests never train or contact Kaggle."""

import base64
import hashlib
import importlib.util
import json
import runpy
from pathlib import Path

import pytest


def load_builder(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / 'scripts'))
    spec = importlib.util.spec_from_file_location('kaggle_package', root / 'scripts/prepare_kaggle_kernel.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return root, module


def test_private_allowlisted_package(tmp_path, monkeypatch):
    root, builder = load_builder(monkeypatch)
    output = tmp_path / 'job'
    hashes = builder.prepare(root, output)
    meta = json.loads((output / 'kernel-metadata.json').read_text())
    assert meta['is_private'] is True
    assert meta['enable_gpu'] is True
    assert meta['kernel_type'] == 'notebook'
    assert meta['machine_shape'] == 'NvidiaTeslaT4'
    notebook = json.loads((output / meta['code_file']).read_text())
    assert notebook['cells'][0]['source'] == (output / 'job.py').read_text()
    assert notebook['cells'][0]['outputs'] == []
    module = runpy.run_path(str(output / 'job.py'))
    assert set(module['PAYLOAD']) == set(builder.FILES)
    for name, encoded in module['PAYLOAD'].items():
        assert base64.b64decode(encoded) == (root / name).read_bytes()
        assert hashlib.sha256(base64.b64decode(encoded)).hexdigest() == hashes[name]
    with pytest.raises(FileExistsError):
        builder.prepare(root, output)


def test_refuses_local_execution(tmp_path, monkeypatch):
    root, builder = load_builder(monkeypatch)
    output = tmp_path / 'job'
    builder.prepare(root, output)
    module = runpy.run_path(str(output / 'job.py'))
    monkeypatch.setattr(Path, 'is_dir', lambda self: False)
    with pytest.raises(RuntimeError, match='must run on Kaggle'):
        module['main']()
