from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from researchproof.source_benchmark import SourceCase


def _blind_id(case_id: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{case_id}".encode()).hexdigest()
    return f"review-{digest[:12]}"


def export_blind_review(cases: list[SourceCase], destination: Path, *, salt: str) -> Path:
    if len(salt) < 12:
        raise ValueError("salt must contain at least 12 characters")
    source_dir = destination / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    review_rows: list[dict[str, str]] = []
    key: list[dict[str, object]] = []
    for case in cases:
        blind_id = _blind_id(case.source_case_id, salt)
        (source_dir / f"{blind_id}.py").write_text(case.source, encoding="utf-8")
        review_rows.append(
            {
                "blind_id": blind_id,
                "reviewer": "",
                "valid_experiment": "",
                "fault_category": "",
                "evidence": "",
                "minimal_repair": "",
                "confidence_1_to_5": "",
                "notes": "",
            }
        )
        key.append({"blind_id": blind_id, **asdict(case), "source": "stored_separately"})

    form = destination / "review_form.csv"
    with form.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)
    (destination / "adjudication_key.json").write_text(
        json.dumps(key, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    instructions = "\n".join(
        [
            "# Blinded review instructions",
            "",
            "Review every file in `sources/` without opening `adjudication_key.json`.",
            "",
            "For each case, record whether the experiment is valid for an ordinary held-out ",
            "test evaluation. If invalid, name the methodological problem, describe the ",
            "relevant operation ordering in your own words, and propose the smallest repair. ",
            "Set confidence from 1 (guessing) to 5 (very confident). Do not discuss answers ",
            "with the other reviewer until both CSV files are complete.",
            "",
            "Each reviewer should copy `review_form.csv` to a separately named file such as ",
            "`review_bibek.csv` or `review_friend.csv`. Open the adjudication key only after ",
            "both files are frozen and checksummed. Keep disagreements in the research record ",
            "and resolve each one in writing.",
            "",
        ]
    )
    (destination / "INSTRUCTIONS.md").write_text(instructions, encoding="utf-8")
    return form
