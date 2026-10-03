"""Compare real JSON pilot packets; never modify or adjudicate reviewer answers."""

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
    parser.add_argument("--data", type=Path, default=Path("artifacts/peerj2025/test_annotated.csv"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; use a new name to preserve the earlier report")
    expected = EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]
    if hashlib.sha256(args.data.read_bytes()).hexdigest() != expected:
        parser.error("canonical dataset fingerprint differs")
    with args.data.open(encoding="utf-8-sig", newline="") as handle:
        sources = {
            f"published-test-row-{i}": row["code_block"]
            for i, row in enumerate(csv.DictReader(handle), 1)
        }
    first, second = json.loads(args.first.read_text()), json.loads(args.second.read_text())
    selected = {
        f"published-test-row-{i}"
        for i in sorted(
            range(1, len(sources) + 1),
            key=lambda i: hashlib.sha256(f"review-v1:{i}".encode()).hexdigest(),
        )[:20]
    }
    for packet in (first, second):
        if {row["case_id"] for row in packet["cases"]} != selected:
            parser.error("packet differs from the frozen 20-case pilot selection")
    report = compare_packets(first, second, sources, expected)
    report["inputs_sha256"] = {
        "first": hashlib.sha256(args.first.read_bytes()).hexdigest(),
        "second": hashlib.sha256(args.second.read_bytes()).hexdigest(),
        "dataset": expected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
