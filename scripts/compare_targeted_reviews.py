"""Compare two completed targeted packets after both human reviews finish."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from researchproof.neural_evidence import EXPECTED_PROTOCOL
from researchproof.pilot_review import compare_packets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve previous review comparisons")
    dataset_sha = hashlib.sha256(args.data.read_bytes()).hexdigest()
    if dataset_sha != EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]:
        parser.error("canonical test data fingerprint differs")
    selection = json.loads(args.selection.read_text())
    if selection.get("dataset_sha256") != dataset_sha:
        parser.error("selection fingerprint differs")
    with args.data.open(encoding="utf-8-sig", newline="") as handle:
        canonical = {
            f"published-test-row-{i}": row["code_block"]
            for i, row in enumerate(csv.DictReader(handle), 1)
        }
    mapping = selection["mapping"]
    if len(mapping) != 24:
        parser.error("targeted selection must contain 24 cases")
    sources = {review_id: canonical[item["source_case_id"]] for review_id, item in mapping.items()}
    first = json.loads(args.first.read_text())
    second = json.loads(args.second.read_text())
    for packet in (first, second):
        if set(row["case_id"] for row in packet.get("cases", [])) != set(sources):
            parser.error("packet IDs differ from frozen selection")
        if packet.get("archive_sha256") != selection["archive_sha256"]:
            parser.error("packet archive fingerprint differs")
        packet["source_sha256"] = dataset_sha
    report = compare_packets(first, second, sources, dataset_sha)
    report["scope"] = "post-hoc targeted error analysis, not an unbiased confirmation sample"
    report["inputs_sha256"] = {
        "first": hashlib.sha256(args.first.read_bytes()).hexdigest(),
        "second": hashlib.sha256(args.second.read_bytes()).hexdigest(),
        "selection": hashlib.sha256(args.selection.read_bytes()).hexdigest(),
        "dataset": dataset_sha,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
