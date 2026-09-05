import json

import pytest

from researchproof.reproduce import compare_benchmark_indices


def write_index(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_runtime_difference_is_ignored(tmp_path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    write_index(first, [{"case_id": "a", "score": 0.8, "runtime_seconds": 1.0}])
    write_index(second, [{"case_id": "a", "score": 0.8, "runtime_seconds": 9.0}])
    assert compare_benchmark_indices(first, second)["reproduced"] is True


def test_scientific_field_difference_is_reported(tmp_path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    write_index(first, [{"case_id": "a", "score": 0.8}])
    write_index(second, [{"case_id": "a", "score": 0.9}])
    report = compare_benchmark_indices(first, second)
    assert report["reproduced"] is False
    assert report["changed_case_ids"] == ["a"]


def test_duplicate_case_id_is_rejected(tmp_path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    write_index(first, [{"case_id": "a"}, {"case_id": "a"}])
    write_index(second, [{"case_id": "a"}])
    with pytest.raises(ValueError, match="duplicate"):
        compare_benchmark_indices(first, second)

