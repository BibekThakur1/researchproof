"""Freeze prediction-hidden review packets for CodeBERT failure analysis.

Selection is post hoc and must never be called an unbiased confirmation sample.
Do not show selection.json to reviewers until both reviews are complete.
"""

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path

from researchproof.neural_archive import inspect_archive
from researchproof.neural_evidence import EXPECTED_PROTOCOL

VARIANTS = ("neutral_comment", "safe_claim", "fault_claim", "formatting")


def choose_cases(archive, source_manifest):
    inspect_archive(archive, source_manifest)
    with zipfile.ZipFile(archive) as handle:
        indexed = []
        for seed in (0, 1, 2):
            rows = json.loads(handle.read(f"seed{seed}/predictions.json"))
            indexed.append({(row["id"], row["variant"]): row for row in rows})
    originals = {key[0] for key in indexed[0] if key[1] == "original"}
    persistent_misses = {
        case_id for case_id in originals
        if indexed[0][(case_id, "original")]["label"] == 1
        and all(indexed[seed][(case_id, "original")]["prediction"] == 0 for seed in (0, 1, 2))
    }
    flips = {
        case_id for case_id in originals for seed in (0, 1, 2) for variant in VARIANTS
        if (case_id, variant) in indexed[seed]
        and indexed[seed][(case_id, variant)]["prediction"]
        != indexed[seed][(case_id, "original")]["prediction"]
    }
    return persistent_misses, flips


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; do not overwrite frozen review packets")
    dataset_sha = hashlib.sha256(args.data.read_bytes()).hexdigest()
    if dataset_sha != EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]:
        parser.error("canonical test data fingerprint differs")
    misses, flips = choose_cases(args.archive, args.source_manifest)
    if len(misses) != 8 or len(flips) != 16 or misses & flips:
        parser.error("unexpected case selection; inspect the archived evidence")
    with args.data.open(encoding="utf-8-sig", newline="") as handle:
        sources = {
            f"published-test-row-{i}": row["code_block"]
            for i, row in enumerate(csv.DictReader(handle), 1)
        }
    chosen = sorted(misses | flips, key=lambda case_id: hashlib.sha256(
        f"targeted-review-v1:{case_id}".encode()
    ).hexdigest())
    if not set(chosen) <= sources.keys():
        parser.error("selected case missing from canonical data")
    mapping = {}
    packet_cases = []
    for number, case_id in enumerate(chosen, 1):
        review_id = f"R{number:02d}"
        mapping[review_id] = {
            "source_case_id": case_id,
            "selection_reason": (
                "persistent_false_negative" if case_id in misses else "prediction_flip"
            ),
        }
        packet_cases.append({
            "case_id": review_id,
            "source": sources[case_id],
            "verdict": None,
            "fault_lines": [],
            "reason": "",
            "missing_context": "",
            "reviewer": "",
            "reviewed_at": "",
        })
    archive_sha = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    packet = {
        "status": "unreviewed_targeted_posthoc_sample",
        "dataset_sha256": dataset_sha,
        "archive_sha256": archive_sha,
        "instructions": (
            "Judge the supplied snippet independently. Do not inspect model predictions "
            "or the selection key. Use insufficient_context where a reliable leakage "
            "decision requires missing code."
        ),
        "allowed_verdicts": ["leakage", "no_observed_leakage", "insufficient_context"],
        "cases": packet_cases,
    }
    args.output.mkdir(parents=True)
    for reviewer in ("a", "b"):
        (args.output / f"reviewer_{reviewer}.json").write_text(json.dumps(packet, indent=2) + "\n")
    (args.output / "selection_private.json").write_text(json.dumps({
        "warning": "Post-hoc failure sample; keep hidden until both human reviews are complete.",
        "dataset_sha256": dataset_sha,
        "archive_sha256": archive_sha,
        "mapping": mapping,
    }, indent=2) + "\n")
    print(f"Created two unreviewed 24-case packets at {args.output}")
    print("Keep selection_private.json away from reviewers until review is complete.")


if __name__ == "__main__":
    main()
