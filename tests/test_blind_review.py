import csv
import hashlib
import json

import pytest

from researchproof.blind_review import FIELDS, compare_blind_reviews, readable_packet


def _compare(packet, first, second):
    return compare_blind_reviews(
        packet, first, second, hashlib.sha256(packet.read_bytes()).hexdigest()
    )


def _fixtures(tmp_path):
    packet = tmp_path / "packet.jsonl"
    packet.write_text(
        "".join(json.dumps({"review_id": f"R-{i}", "code_block": "x = 1"}) + "\n" for i in range(8))
    )
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    for path in (first, second):
        _write(path, [{"review_id": f"R-{i}"} for i in range(8)])
    return packet, first, second


def _write(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _completed(verdict):
    return [
        {
            "review_id": f"R-{i}",
            "judgment": verdict,
            "leakage_mechanism": "holdout reuse" if verdict == "confirmed_leakage" else "",
            "evidence_cells": "cell 2" if i % 2 else "snippet line 1",
            "confidence": "medium",
            "rationale": "Reviewed the visible data flow.",
        }
        for i in range(8)
    ]


def test_blank_forms_report_coverage_only(tmp_path):
    packet, first, second = _fixtures(tmp_path)
    report = _compare(packet, first, second)
    assert report["completed_first"] == report["completed_second"] == 0
    assert report["agreement"] is None
    assert report["human_independence_verified"] is False
    assert "code_block" not in json.dumps(report)


def test_agreement_and_disagreement_after_completion(tmp_path):
    packet, first, second = _fixtures(tmp_path)
    a = _completed("confirmed_leakage")
    b = _completed("confirmed_leakage")
    b[2]["judgment"] = "insufficient_context"
    b[2]["leakage_mechanism"] = ""
    _write(first, a)
    _write(second, b)
    report = _compare(packet, first, second)
    assert report["status"] == "complete_pending_adjudication"
    assert report["agreement"]["raw"] == 7 / 8
    assert report["agreement"]["disagreements"] == ["R-2"]
    assert report["agreement"]["cohen_kappa"] == pytest.approx(0)


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "no_rationale", "partial"])
def test_bad_forms_rejected(tmp_path, mutation):
    packet, first, second = _fixtures(tmp_path)
    rows = _completed("confirmed_leakage")
    if mutation == "duplicate":
        rows[1]["review_id"] = "R-0"
    elif mutation == "unknown":
        rows[1]["review_id"] = "R-99"
    elif mutation == "no_rationale":
        rows[1]["rationale"] = ""
    else:
        rows[1]["judgment"] = ""
    _write(first, rows)
    with pytest.raises(ValueError):
        _compare(packet, first, second)


def test_changed_packet_rejected(tmp_path):
    packet, first, second = _fixtures(tmp_path)
    with pytest.raises(ValueError, match="fingerprint"):
        compare_blind_reviews(packet, first, second, "0" * 64)


def test_readable_packet_keeps_code_but_not_review_key(tmp_path):
    packet, _, _ = _fixtures(tmp_path)
    digest = hashlib.sha256(packet.read_bytes()).hexdigest()
    readable = readable_packet(packet, digest)
    assert readable.count("## Case ") == 8
    assert "x = 1" in readable
    assert "published-test-row-" not in readable
    assert "model predictions" in readable
