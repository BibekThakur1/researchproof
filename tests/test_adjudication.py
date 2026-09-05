import csv

import pytest

from researchproof.adjudication import ReviewError, compare_reviews

FIELDS = [
    "blind_id",
    "reviewer",
    "valid_experiment",
    "fault_category",
    "evidence",
    "minimal_repair",
    "confidence_1_to_5",
    "notes",
]


def write_review(path, labels):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for index, label in enumerate(labels):
            writer.writerow({"blind_id": f"review-{index}", "valid_experiment": label})


def test_review_comparison_reports_agreement_and_disagreements(tmp_path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    write_review(first, ["yes", "no", "yes", "no"])
    write_review(second, ["yes", "no", "no", "no"])
    report = compare_reviews(first, second)
    assert report["raw_agreement"] == 0.75
    assert report["disagreement_count"] == 1
    assert report["disagreements"][0]["blind_id"] == "review-2"


def test_incomplete_answers_are_rejected(tmp_path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    write_review(first, ["yes", ""])
    write_review(second, ["yes", "no"])
    with pytest.raises(ReviewError, match="yes or no"):
        compare_reviews(first, second)


def test_mismatched_review_ids_are_rejected(tmp_path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    write_review(first, ["yes", "no"])
    write_review(second, ["yes"])
    with pytest.raises(ReviewError, match="IDs differ"):
        compare_reviews(first, second)

