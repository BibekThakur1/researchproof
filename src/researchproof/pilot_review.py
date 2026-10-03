"""Validate the three-way JSON pilot review without inventing human judgments."""

from collections import Counter
from datetime import datetime

VERDICTS = ("leakage", "no_observed_leakage", "insufficient_context")


def _validate(packet, sources, dataset_sha256):
    if packet.get("source_sha256") != dataset_sha256:
        raise ValueError("review dataset fingerprint differs")
    cases = packet.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("nonempty case list required")
    indexed = {}
    reviewers = set()
    for row in cases:
        identifier = row.get("case_id")
        if identifier not in sources or identifier in indexed:
            raise ValueError("unknown or duplicate review case")
        if row.get("source") != sources[identifier]:
            raise ValueError("review source changed")
        verdict = row.get("verdict")
        if verdict is not None:
            if verdict not in VERDICTS:
                raise ValueError("invalid verdict")
            for field in ("reviewer", "reason", "reviewed_at"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise ValueError(f"completed verdict requires {field}")
            timestamp = datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00"))
            if timestamp.utcoffset() is None:
                raise ValueError("review timestamp needs a timezone")
            reviewers.add(row["reviewer"].strip().casefold())
            lines = row.get("fault_lines")
            if not isinstance(lines, list) or any(
                type(line) is not int or not 1 <= line <= len(row["source"].splitlines())
                for line in lines
            ):
                raise ValueError("invalid fault lines")
            if verdict == "leakage" and not lines:
                raise ValueError("leakage verdict needs evidence lines")
            if verdict == "insufficient_context":
                context = row.get("missing_context")
                if not isinstance(context, str) or not context.strip():
                    raise ValueError("insufficient context needs an explanation")
        indexed[identifier] = row
    if len(reviewers) > 1:
        raise ValueError("one reviewer per independent packet is required")
    return indexed, reviewers


def compare_packets(first, second, sources, dataset_sha256):
    """Return coverage for incomplete packets; agreement only after both finish.

    Metadata can detect contradictions, not prove independence or human authorship.
    ``sources`` must come from the checksum-verified canonical dataset.
    """
    left, left_reviewers = _validate(first, sources, dataset_sha256)
    right, right_reviewers = _validate(second, sources, dataset_sha256)
    if set(left) != set(right):
        raise ValueError("review case IDs differ")
    if left_reviewers & right_reviewers:
        raise ValueError("distinct reviewer identities required")
    counts = [
        sum(row["verdict"] is not None for row in packet.values()) for packet in (left, right)
    ]
    report = {
        "status": "incomplete",
        "cases_per_reviewer": len(left),
        "completed_first": counts[0],
        "completed_second": counts[1],
        "agreement": None,
        "independent_human_authorship_verified": False,
        "scope": "label-feasibility pilot, not confirmed ground truth",
    }
    if counts != [len(left), len(left)]:
        return report
    pairs = [(left[key]["verdict"], right[key]["verdict"]) for key in sorted(left)]
    matrix = {a: {b: 0 for b in VERDICTS} for a in VERDICTS}
    for a, b in pairs:
        matrix[a][b] += 1
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    marginal_a, marginal_b = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(marginal_a[v] * marginal_b[v] for v in VERDICTS) / n**2
    report.update(
        {
            "status": "complete_pending_adjudication",
            "agreement": {
                "raw": observed,
                "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
                "kappa_note": "undefined when expected agreement is one" if expected == 1 else None,
                "confusion_matrix": matrix,
                "disagreements": [
                    key for key in sorted(left) if left[key]["verdict"] != right[key]["verdict"]
                ],
                "insufficient_context_first": marginal_a["insufficient_context"],
                "insufficient_context_second": marginal_b["insufficient_context"],
            },
        }
    )
    return report
