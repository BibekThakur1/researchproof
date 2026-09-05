import pytest

from researchproof.artifacts import build_artifact_manifest, verify_artifact_manifest


def test_artifact_manifest_round_trip(tmp_path) -> None:
    (tmp_path / "a.json").write_text("{}\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("evidence\n", encoding="utf-8")
    build_artifact_manifest(tmp_path)
    assert verify_artifact_manifest(tmp_path) == []


def test_artifact_tampering_is_detected(tmp_path) -> None:
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("original", encoding="utf-8")
    build_artifact_manifest(tmp_path)
    evidence.write_text("changed", encoding="utf-8")
    assert verify_artifact_manifest(tmp_path) == ["checksum mismatch: evidence.txt"]


def test_empty_artifact_directory_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="no files"):
        build_artifact_manifest(tmp_path)

