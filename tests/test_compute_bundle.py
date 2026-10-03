import hashlib
import json
import runpy
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "scripts/package_neural_job.py"))


def test_bundle_is_allowlisted_and_hashes_match(tmp_path):
    output = tmp_path / "compute.zip"
    manifest = MODULE["build_bundle"](ROOT, output)
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == set(MODULE["FILES"]) | {"MANIFEST.json"}
        assert json.loads(archive.read("MANIFEST.json")) == manifest
        for name, expected in manifest["files_sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
    with pytest.raises(FileExistsError):
        MODULE["build_bundle"](ROOT, output)


def test_missing_source_does_not_create_bundle(tmp_path):
    output = tmp_path / "compute.zip"
    with pytest.raises(FileNotFoundError):
        MODULE["build_bundle"](tmp_path, output)
    assert not output.exists()
