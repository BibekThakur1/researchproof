"""Export deterministic review packets; never create human annotations."""

import csv
import hashlib
import json
from pathlib import Path


def main():
    source = Path("artifacts/peerj2025/test_annotated.csv")
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    # Hash-order sample independent of published labels and detector predictions.
    selected = sorted(
        enumerate(rows, 1),
        key=lambda item: hashlib.sha256(f"review-v1:{item[0]}".encode()).hexdigest(),
    )[:20]
    records = [
        {
            "case_id": f"published-test-row-{number}",
            "source": row["code_block"],
            "verdict": None,
            "fault_lines": [],
            "reason": "",
            "missing_context": "",
            "reviewer": "",
            "reviewed_at": "",
        }
        for number, row in selected
    ]
    root = Path("artifacts/pilot_review_v1")
    root.mkdir(parents=True, exist_ok=True)
    for reviewer in ("a", "b"):
        path = root / f"reviewer_{reviewer}.json"
        if path.exists():
            print(f"Preserved existing review: {path}")
            continue
        path.write_text(
            json.dumps(
                {
                    "status": "unreviewed",
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "allowed_verdicts": ["leakage", "no_observed_leakage", "insufficient_context"],
                    "instructions": "Review independently without predictions or published labels.",
                    "cases": records,
                },
                indent=2,
            )
            + "\n"
        )
        print(f"Created unreviewed packet: {path}")


if __name__ == "__main__":
    main()
