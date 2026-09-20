"""Check committed pilot arithmetic without network access or model training."""

import json
from pathlib import Path

import pytest

RESULT = Path(__file__).resolve().parents[1] / "results/2026-09-20/robustness_pilot.json"


@pytest.fixture
def evidence():
    return json.loads(RESULT.read_text())


def test_record_counts_and_no_exported_raw_source(evidence):
    records = evidence["records"]
    assert len(records) == evidence["test_rows"]
    assert len({r["id"] for r in records}) == len(records)
    assert sum(r["label"] for r in records) == evidence["test_positives"]
    assert sum(r["parseable"] for r in records) == evidence["parseable_test"]
    assert all("code_block" not in r for r in records)


def test_flip_accounting_and_denominators(evidence):
    for name, subsets in evidence["summary"].items():
        for subset, summary in subsets.items():
            records = [
                r
                for r in evidence["records"]
                if subset == "published_test"
                or not (r["exact_train_match"] or r["ast_train_match"])
            ]
            assert summary["n"] == len(records)
            for variant, counts in summary["edits"].items():
                eligible = [r for r in records if variant in r["predictions"][name]]
                assert counts["eligible"] == len(eligible)
                assert counts["flips"] == sum(
                    r["predictions"][name][variant] != r["predictions"][name]["original"]
                    for r in eligible
                )
                assert counts["flips"] == counts["correct_to_wrong"] + counts["wrong_to_correct"]


def test_semantic_pair_success_is_both_correct(evidence):
    for summary in evidence["constructed_semantic_pairs"].values():
        assert summary["both_correct"] == sum(
            p["clean_prediction"] == 0 and p["faulty_prediction"] == 1 for p in summary["pairs"]
        )
