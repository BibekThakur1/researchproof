import json
from pathlib import Path

import pytest

RESULT = Path(__file__).resolve().parents[1] / "results/2026-09-26/mlscent.json"


@pytest.fixture
def evidence():
    return json.loads(RESULT.read_text())


def test_all_corpus_denominators_account_for_unknown(evidence):
    for corpus, summary in evidence["summary"].items():
        rows = [
            r
            for r in evidence["records"]
            if r["corpus"] == corpus and (corpus != "peerj_test" or r["variant"] == "original")
        ]
        assert len(rows) == summary["inputs"]
        assert sum(r["label"] is not None for r in rows) == summary["labeled_inputs"]
        answered = [r for r in rows if r["prediction"] is not None and r["label"] is not None]
        assert len(answered) == summary["answered"]
        assert sum(summary[k] for k in ("tp", "fp", "tn", "fn")) == len(answered)
        assert summary["tp"] + summary["fn"] == sum(r["label"] for r in answered)


def test_skips_do_not_become_clean(evidence):
    for row in evidence["records"]:
        assert "source" not in row
        if all(
            c["status"] != "checked" and c["prediction"] is not True
            for c in row["components"].values()
        ):
            assert row["prediction"] is None


def test_executable_positive_control_warns_then_loses_warning(evidence):
    controls = {r["variant"]: r for r in evidence["records"] if r["corpus"] == "executable_control"}
    assert controls["prefix"]["prediction"] is True
    assert controls["full"]["prediction"] is False


def test_surface_metrics_use_only_answered_pairs(evidence):
    originals = {
        r["group"]: r
        for r in evidence["records"]
        if r["corpus"] == "peerj_test" and r["variant"] == "original"
    }
    for edit, summary in evidence["edits"].items():
        pairs = [
            (originals[r["group"]], r)
            for r in evidence["records"]
            if r["corpus"] == "peerj_test" and r["variant"] == edit
        ]
        answered = [
            (a, b) for a, b in pairs if a["prediction"] is not None and b["prediction"] is not None
        ]
        assert summary["paired"] == len(pairs)
        assert summary["both_answered"] == len(answered)
        assert summary["flips"] == sum(a["prediction"] != b["prediction"] for a, b in answered)
