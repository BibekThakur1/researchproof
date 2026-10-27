"""Find candidate Code4ML notebook IDs for eight persistent CodeBERT misses.

This matches text only; it does not verify that a derived kernel ID identifies
the original notebook or establish the correctness of a leakage label.
"""

import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path

from researchproof.neural_evidence import EXPECTED_PROTOCOL

MISSES = (34, 49, 60, 207, 272, 273, 370, 371)


def normalize(value):
    value = re.sub(r"<br\s*/?>", "\n", html.unescape(value), flags=re.IGNORECASE)
    return re.sub(r"\s+", "", value).casefold()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--peerj-test", type=Path, required=True)
    parser.add_argument("--code4ml-derived", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve prior provenance searches")
    peerj_sha = hashlib.sha256(args.peerj_test.read_bytes()).hexdigest()
    if peerj_sha != EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]:
        parser.error("PeerJ test data fingerprint differs")
    derived_sha = hashlib.sha256(args.code4ml_derived.read_bytes()).hexdigest()
    with args.peerj_test.open(encoding="utf-8-sig", newline="") as handle:
        peerj = list(csv.DictReader(handle))
    targets = {f"published-test-row-{i}": peerj[i - 1]["code_block"] for i in MISSES}
    normalized = {key: normalize(source) for key, source in targets.items()}
    matches = {key: [] for key in targets}
    total = 0
    with args.code4ml_derived.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            candidate = row["code_block"]
            canonical = normalize(candidate)
            for case_id, source in targets.items():
                match_type = (
                    "exact" if candidate == source else
                    "whitespace_html_normalized" if canonical == normalized[case_id] else None
                )
                if match_type is not None:
                    matches[case_id].append({
                        "match_type": match_type,
                        "code4ml_row_id": row["id"],
                        "kernel_id_from_derivative": row["kernel_id"] or None,
                        "source_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
                    })
    report = {
        "status": "candidate_text_matches_not_verified_origins",
        "peerj_test_sha256": peerj_sha,
        "derived_dataset_sha256": derived_sha,
        "derived_dataset_url": (
            "https://huggingface.co/datasets/dimsmauls/code4ml-annotated-rated"
        ),
        "rows_examined": total,
        "cases": matches,
        "limitations": [
            "Derived kernel IDs are third-party recovered IDs and require "
            "original-source verification.",
            "No match does not prove the source notebook is unavailable.",
            "Text matching does not validate the published leakage label.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print({case_id: len(rows) for case_id, rows in matches.items()})


if __name__ == "__main__":
    main()
