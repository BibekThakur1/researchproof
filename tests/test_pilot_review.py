import copy

import pytest

from researchproof.pilot_review import compare_packets

SOURCES = {"case-1": "x = 1\n", "case-2": "y = 2\n"}


def packet(reviewer="A", verdicts=("leakage", "no_observed_leakage")):
    """Artificial unit-test records, not scientific annotations."""
    return {
        "source_sha256": "fixture",
        "cases": [
            {
                "case_id": key,
                "source": source,
                "verdict": verdict,
                "fault_lines": [1] if verdict == "leakage" else [],
                "reason": "Synthetic test reason",
                "missing_context": "Synthetic context",
                "reviewer": reviewer,
                "reviewed_at": "2026-10-03T12:00:00+05:45",
            }
            for (key, source), verdict in zip(SOURCES.items(), verdicts, strict=True)
        ],
    }


def compare(a, b):
    return compare_packets(a, b, SOURCES, "fixture")


def test_incomplete_has_no_agreement_and_preserves_packets():
    a, b = packet(verdicts=(None, None)), packet("B")
    before = copy.deepcopy(a)
    report = compare(a, b)
    assert report["agreement"] is None
    assert report["completed_first"] == 0
    assert a == before


def test_three_way_agreement_keeps_uncertain_cases():
    report = compare(packet(), packet("B", ("leakage", "insufficient_context")))
    assert report["agreement"]["raw"] == 0.5
    assert report["agreement"]["cohen_kappa"] == pytest.approx(1 / 3)
    assert report["agreement"]["insufficient_context_second"] == 1
    assert report["agreement"]["disagreements"] == ["case-2"]
    assert not report["independent_human_authorship_verified"]


def test_degenerate_kappa_is_undefined_not_perfect():
    report = compare(packet(verdicts=("leakage", "leakage")), packet("B", ("leakage", "leakage")))
    assert report["agreement"]["raw"] == 1
    assert report["agreement"]["cohen_kappa"] is None


@pytest.mark.parametrize(
    "failure",
    [
        "same_person",
        "duplicate",
        "source",
        "fingerprint",
        "verdict",
        "reason",
        "time",
        "lines",
        "missing_context",
        "missing_case",
    ],
)
def test_malformed_or_nonindependent_packets_rejected(failure):
    a, b = packet(), packet("B")
    row = b["cases"][0]
    if failure == "same_person":
        b = packet("a")
    elif failure == "duplicate":
        b["cases"][1] = dict(row)
    elif failure == "source":
        row["source"] = "modified"
    elif failure == "fingerprint":
        b["source_sha256"] = "changed"
    elif failure == "verdict":
        row["verdict"] = "guess"
    elif failure == "reason":
        row["reason"] = ""
    elif failure == "time":
        row["reviewed_at"] = "2026-10-03T12:00:00"
    elif failure == "lines":
        row["fault_lines"] = [2]
    elif failure == "missing_context":
        row["verdict"], row["missing_context"] = "insufficient_context", None
    else:
        b["cases"].pop()
    with pytest.raises(ValueError):
        compare(a, b)
