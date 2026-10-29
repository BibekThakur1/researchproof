"""Validate the eight-case notebook review without reading the private key."""

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

JUDGMENTS = (
    "confirmed_leakage",
    "no_leakage_in_recovered_workflow",
    "insufficient_context",
    "ambiguous_or_disputed",
)
FIELDS = (
    "review_id",
    "judgment",
    "leakage_mechanism",
    "evidence_cells",
    "confidence",
    "rationale",
)
CONFIDENCE = ("low", "medium", "high")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _packet(path: Path) -> dict[str, dict]:
    cases = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        identifier = item.get("review_id")
        if not isinstance(identifier, str) or not identifier or identifier in cases:
            raise ValueError("packet has a missing or duplicate review ID")
        if not isinstance(item.get("code_block"), str):
            raise ValueError("packet case lacks source code")
        cases[identifier] = item
    if len(cases) != 8:
        raise ValueError("expected exactly eight packet cases")
    return cases


def readable_packet(packet: Path, expected_packet_sha256: str) -> str:
    """Render the frozen packet for local reading without unblinding it."""
    if _sha256(packet) != expected_packet_sha256:
        raise ValueError("packet fingerprint differs from the frozen packet")
    cases = _packet(packet)
    lines = [
        "# Blinded notebook review — eight cases",
        "",
        "Review these cases independently. Do not read the private review key,",
        "published labels, model predictions, or the other reviewer's form.",
        "Do not execute downloaded notebook code. Record answers in your own CSV.",
        "Use the full relevant data flow when a notebook is available; if it is",
        "not recoverable, do not infer a workflow-level verdict from a vague snippet.",
        "",
    ]
    for number, item in enumerate(cases.values(), 1):
        source = item["code_block"]
        # Tilde fences permit literal backticks in the source code.
        longest_tilde_run = max((len(run) for run in re.findall(r"~+", source)), default=0)
        fence = "~" * max(3, longest_tilde_run + 1)
        cell = item.get("cell_index_zero_based")
        cell_label = cell if cell is not None and cell != "" else "not available"
        lines.extend(
            [
                f"## Case {number}: {item['review_id']}",
                "",
                f"Notebook: {item.get('notebook_url') or 'not recovered'}",
                f"Zero-based cell index: {cell_label}",
                "",
                f"{fence}python",
                source,
                fence,
                "",
            ]
        )
    return "\n".join(lines)


def _form(path: Path, expected_ids: set[str]) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path.name}: unexpected form columns")
        rows = list(reader)
    if len(rows) != len(expected_ids):
        raise ValueError(f"{path.name}: expected {len(expected_ids)} rows")
    indexed = {}
    for row in rows:
        identifier = row["review_id"]
        if identifier not in expected_ids or identifier in indexed:
            raise ValueError(f"{path.name}: unknown or duplicate review ID")
        if any(value is None for value in row.values()):
            raise ValueError(f"{path.name}: malformed CSV row")
        judgment = row["judgment"].strip()
        other = [row[field].strip() for field in FIELDS[2:]]
        if judgment:
            if judgment not in JUDGMENTS:
                raise ValueError(f"{path.name}: invalid judgment for {identifier}")
            if row["confidence"].strip() not in CONFIDENCE:
                raise ValueError(f"{path.name}: invalid confidence for {identifier}")
            if not row["rationale"].strip() or not row["evidence_cells"].strip():
                raise ValueError(f"{path.name}: completed case needs rationale and evidence cells")
            if judgment == "confirmed_leakage" and not row["leakage_mechanism"].strip():
                raise ValueError(f"{path.name}: leakage needs a mechanism")
        elif any(other):
            raise ValueError(f"{path.name}: partial case has notes but no judgment")
        indexed[identifier] = row
    return indexed


def compare_blind_reviews(
    packet: Path, first: Path, second: Path, expected_packet_sha256: str
) -> dict:
    """Report coverage, and agreement only when both original forms are complete.

    This checks structure and fixed IDs, not human authorship or independence.
    The report intentionally contains no code, judgments per case, or private key.
    """
    packet_sha = _sha256(packet)
    if packet_sha != expected_packet_sha256:
        raise ValueError("packet fingerprint differs from the frozen packet")
    cases = _packet(packet)
    ids = set(cases)
    left, right = _form(first, ids), _form(second, ids)
    complete = [
        sum(bool(form[identifier]["judgment"].strip()) for identifier in ids)
        for form in (left, right)
    ]
    report = {
        "scope": "post-hoc eight-case persistent-miss review; not prevalence or confirmation",
        "cases_per_reviewer": len(ids),
        "completed_first": complete[0],
        "completed_second": complete[1],
        "status": "incomplete",
        "agreement": None,
        "human_independence_verified": False,
        "input_sha256": {
            "packet": packet_sha,
            "first": _sha256(first),
            "second": _sha256(second),
        },
    }
    if complete != [len(ids), len(ids)]:
        return report

    pairs = [
        (left[identifier]["judgment"].strip(), right[identifier]["judgment"].strip())
        for identifier in sorted(ids)
    ]
    matrix = {a: {b: 0 for b in JUDGMENTS} for a in JUDGMENTS}
    for a, b in pairs:
        matrix[a][b] += 1
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    marginal_a, marginal_b = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(marginal_a[v] * marginal_b[v] for v in JUDGMENTS) / n**2
    report["status"] = "complete_pending_adjudication"
    report["agreement"] = {
        "raw": observed,
        "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
        "kappa_note": "undefined when expected agreement is one" if expected == 1 else None,
        "confusion_matrix": matrix,
        "disagreements": [
            identifier
            for identifier in sorted(ids)
            if left[identifier]["judgment"].strip() != right[identifier]["judgment"].strip()
        ],
        "note": "Only eight selected cases; report counts and disagreements, not population rates.",
    }
    return report
