import csv
import json

import pytest

from researchproof.annotation import export_blind_review
from researchproof.source_benchmark import build_source_cases


def test_blind_export_hides_labels_from_review_form_and_filenames(tmp_path) -> None:
    cases = build_source_cases()
    form = export_blind_review(cases, tmp_path, salt="fixed-test-salt")
    with form.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    filenames = [path.name for path in (tmp_path / "sources").glob("*.py")]
    assert len(rows) == len(cases)
    assert all(row["valid_experiment"] == "" for row in rows)
    assert all("clean" not in name and "faulty" not in name for name in filenames)


def test_adjudication_key_is_separate_and_complete(tmp_path) -> None:
    cases = build_source_cases()
    export_blind_review(cases, tmp_path, salt="fixed-test-salt")
    key = json.loads((tmp_path / "adjudication_key.json").read_text(encoding="utf-8"))
    assert len(key) == len(cases)
    assert {item["variant"] for item in key} == {"clean", "faulty"}
    assert all(item["source"] == "stored_separately" for item in key)


def test_short_salt_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="12 characters"):
        export_blind_review(build_source_cases(), tmp_path, salt="short")
