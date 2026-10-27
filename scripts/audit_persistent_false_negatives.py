"""Trace persistent misses to public notebooks without relabeling examples.

The third-party Code4ML match file only supplies candidate notebook IDs. A
candidate is counted as source-verified only when the downloaded notebook has
the exact evaluated code cell. This script does not infer a leakage label.
"""

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path

from researchproof.neural_archive import inspect_archive
from researchproof.neural_evidence import EXPECTED_PROTOCOL

MISSES = (34, 49, 60, 207, 272, 273, 370, 371)
METADATA_MD5 = "738958a342398cdbb82eb5473405c4c6"


def digest(path, algorithm="sha256"):
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--notebooks", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve prior audit")
    if digest(args.test) != EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]:
        parser.error("canonical test fingerprint differs")
    if digest(args.metadata, "md5") != METADATA_MD5:
        parser.error("Code4ML metadata fingerprint differs")
    inspect_archive(args.archive, args.source_manifest)

    with args.test.open(encoding="utf-8-sig", newline="") as handle:
        testing = list(csv.DictReader(handle))
    with args.metadata.open(encoding="utf-8-sig", newline="") as handle:
        metadata = {row["kernel_id"]: row for row in csv.DictReader(handle)}
    candidates = json.loads(args.matches.read_text())["cases"]
    predictions = {}
    with zipfile.ZipFile(args.archive) as archive:
        for seed in (0, 1, 2):
            records = json.loads(archive.read(f"seed{seed}/predictions.json"))
            predictions[seed] = {
                row["id"]: row for row in records if row["variant"] == "original"
            }

    rows = []
    for number in MISSES:
        case_id = f"published-test-row-{number}"
        original = testing[number - 1]
        source = original["code_block"]
        source_sha = hashlib.sha256(source.encode()).hexdigest()
        if original["has_data_leakage"] != "1":
            raise ValueError(f"{case_id} is not published positive")
        for seed in (0, 1, 2):
            prediction = predictions[seed][case_id]
            if (prediction["label"], prediction["prediction"], prediction["source_sha256"]) != (
                1, 0, source_sha
            ):
                raise ValueError(f"{case_id} is not an exact persistent miss")
        hits = candidates[case_id]
        if len(hits) > 1:
            raise ValueError(f"multiple derivative matches for {case_id}; inspect manually")
        hit = hits[0] if hits else {}
        kernel_id = hit.get("kernel_id_from_derivative")
        if hit and (hit["match_type"] != "exact" or hit["source_sha256"] != source_sha):
            raise ValueError(f"derived source mismatch: {case_id}")
        notebook_path = None
        notebook_sha = None
        cell_indices = []
        notebook_url = None
        if kernel_id:
            if kernel_id not in metadata:
                raise ValueError(f"unknown Code4ML kernel: {kernel_id}")
            notebooks = list((args.notebooks / kernel_id).glob("*.ipynb"))
            if len(notebooks) != 1:
                raise ValueError(f"expected one notebook for {kernel_id}")
            notebook_path = notebooks[0]
            notebook_sha = digest(notebook_path)
            notebook = json.loads(notebook_path.read_text())
            cell_indices = [
                index for index, cell in enumerate(notebook["cells"])
                if cell["cell_type"] == "code" and "".join(cell["source"]) == source
            ]
            notebook_url = "https://www.kaggle.com/code" + metadata[kernel_id]["kernel_link"]
        rows.append({
            "case_id": case_id,
            "published_label": 1,
            "seed0_prediction": 0,
            "seed1_prediction": 0,
            "seed2_prediction": 0,
            "source_sha256": source_sha,
            "derived_code4ml_row_id": hit.get("code4ml_row_id", ""),
            "candidate_kernel_id": kernel_id or "",
            "notebook_url": notebook_url or "",
            "notebook_sha256": notebook_sha or "",
            "cell_index_zero_based": ";".join(map(str, cell_indices)),
            "exact_source_verified": bool(cell_indices),
            "context_judgment": "pending_independent_human_review",
            "note": (
                "Current public notebook snapshot; historical revision not verified"
                if cell_indices else "Original notebook not source-verified"
            ),
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    verified = sum(row["exact_source_verified"] for row in rows)
    print(f"Verified exact notebook cell in {verified}/8 cases")
    print(f"Audit written to {args.output}")


if __name__ == "__main__":
    main()
