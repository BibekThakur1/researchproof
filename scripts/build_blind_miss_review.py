"""Build a label/prediction-blind review packet for eight persistent misses.

The packet includes third-party code, so keep its output in ignored artifacts
and distribute it only in accordance with the source datasets' terms.
"""

import argparse
import csv
import hashlib
import json
import secrets
from pathlib import Path

from researchproof.neural_evidence import EXPECTED_PROTOCOL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve prior blinded packet")
    if hashlib.sha256(args.test.read_bytes()).hexdigest() != EXPECTED_PROTOCOL[
        "dataset_sha256"
    ]["test_annotated.csv"]:
        parser.error("canonical test fingerprint differs")
    with args.test.open(encoding="utf-8-sig", newline="") as handle:
        testing = list(csv.DictReader(handle))
    with args.audit.open(encoding="utf-8", newline="") as handle:
        audit = list(csv.DictReader(handle))
    if len(audit) != 8:
        parser.error("expected exactly eight audit cases")

    packet = []
    mapping = []
    ids = set()
    for row in audit:
        number = int(row["case_id"].rsplit("-", 1)[1])
        source = testing[number - 1]["code_block"]
        if hashlib.sha256(source.encode()).hexdigest() != row["source_sha256"]:
            parser.error(f"source differs from audit: {row['case_id']}")
        review_id = "R-" + secrets.token_hex(5)
        if review_id in ids:
            parser.error("random review ID collision; retry with new directory")
        ids.add(review_id)
        packet.append({
            "review_id": review_id,
            "code_block": source,
            "notebook_url": row["notebook_url"] or None,
            "cell_index_zero_based": row["cell_index_zero_based"] or None,
        })
        mapping.append({"review_id": review_id, "published_case_id": row["case_id"]})

    args.output.mkdir(parents=True)
    with (args.output / "packet.jsonl").open("w", encoding="utf-8") as handle:
        for item in packet:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    fields = (
        "review_id", "judgment", "leakage_mechanism", "evidence_cells",
        "confidence", "rationale",
    )
    for reviewer in ("reviewer_a", "reviewer_b"):
        with (args.output / f"{reviewer}.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows({"review_id": item["review_id"]} for item in packet)
    with (args.output / "review_key_keep_private.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("review_id", "published_case_id"))
        writer.writeheader()
        writer.writerows(mapping)
    print(f"Wrote eight blinded cases and two empty forms to {args.output}")
    print("Do not give reviewers the review key, model outcomes, or AI trace note.")


if __name__ == "__main__":
    main()
