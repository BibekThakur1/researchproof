"""Trace all published positive test snippets to Code4ML and public notebooks.

This is post-hoc source provenance, not independent label validation. The
output omits third-party source code and never changes published labels.
"""

import argparse
import csv
import hashlib
import json
import zipfile
from collections import defaultdict
from pathlib import Path

from researchproof.neural_archive import inspect_archive
from researchproof.neural_evidence import EXPECTED_PROTOCOL

DERIVATIVE_SHA256 = "f96185e6b0a592626a4308d62cebe3cb9dc9e6dc2947bd064a0cae5e790b7a32"
CODE4ML_METADATA_MD5 = "738958a342398cdbb82eb5473405c4c6"


def digest(path, algorithm="sha256"):
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def analyze(test, derivative, metadata_file, notebooks, archive, manifest):
    if digest(test) != EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]:
        raise ValueError("canonical PeerJ test fingerprint differs")
    if digest(derivative) != DERIVATIVE_SHA256:
        raise ValueError("derived Code4ML CSV fingerprint differs")
    if digest(metadata_file, "md5") != CODE4ML_METADATA_MD5:
        raise ValueError("Code4ML metadata fingerprint differs")
    inspect_archive(archive, manifest)
    with test.open(encoding="utf-8-sig", newline="") as handle:
        testing = list(csv.DictReader(handle))
    with derivative.open(encoding="utf-8-sig", newline="") as handle:
        index = defaultdict(list)
        for row in csv.DictReader(handle):
            index[row["code_block"]].append(row)
    with metadata_file.open(encoding="utf-8-sig", newline="") as handle:
        metadata = {row["kernel_id"]: row for row in csv.DictReader(handle)}
    with zipfile.ZipFile(archive) as handle:
        predictions = [
            {
                row["id"]: row
                for row in json.loads(handle.read(f"seed{seed}/predictions.json"))
                if row["variant"] == "original"
            }
            for seed in (0, 1, 2)
        ]

    cases = []
    for number, row in enumerate(testing, 1):
        if row["has_data_leakage"] != "1":
            continue
        case_id = f"published-test-row-{number}"
        source = row["code_block"]
        source_sha = hashlib.sha256(source.encode()).hexdigest()
        outcomes = []
        for seed in (0, 1, 2):
            outcome = predictions[seed][case_id]
            if (outcome["label"], outcome["source_sha256"]) != (1, source_sha):
                raise ValueError(f"prediction source/label mismatch: {case_id}")
            outcomes.append(outcome["prediction"])
        hits = index[source]
        if len(hits) > 1:
            raise ValueError(f"multiple exact derivative matches: {case_id}")
        hit = hits[0] if hits else None
        kernel_id = hit["kernel_id"] if hit else ""
        notebook_sha = None
        notebook_url = None
        cell_indices = []
        if kernel_id:
            if kernel_id not in metadata:
                raise ValueError(f"candidate kernel absent from Code4ML metadata: {kernel_id}")
            files = list((notebooks / kernel_id).glob("*.ipynb"))
            if len(files) != 1:
                raise ValueError(f"expected one downloaded notebook for {kernel_id}")
            notebook_sha = digest(files[0])
            notebook = json.loads(files[0].read_text())
            cell_indices = [
                i for i, cell in enumerate(notebook["cells"])
                if cell["cell_type"] == "code" and "".join(cell["source"]) == source
            ]
            notebook_url = "https://www.kaggle.com/code" + metadata[kernel_id]["kernel_link"]
        cases.append({
            "case_id": case_id,
            "published_label": 1,
            "predictions_seed_0_1_2": outcomes,
            "source_sha256": source_sha,
            "exact_derivative_match": bool(hit),
            "derived_code4ml_row_id": hit["id"] if hit else None,
            "candidate_kernel_id": kernel_id or None,
            "notebook_url": notebook_url,
            "current_notebook_sha256": notebook_sha,
            "exact_cell_indices_zero_based": cell_indices,
            "source_verified_in_current_notebook": bool(cell_indices),
            "context_judgment": "pending_independent_human_review",
        })
    if len(cases) != 25:
        raise ValueError("unexpected number of published positives")
    return {
        "status": "exploratory_positive_source_provenance_not_label_validation",
        "canonical_test_sha256": digest(test),
        "derivative_sha256": digest(derivative),
        "code4ml_metadata_md5": digest(metadata_file, "md5"),
        "archive_sha256": digest(archive),
        "summary": {
            "published_positive_cases": len(cases),
            "exact_derivative_matches": sum(c["exact_derivative_match"] for c in cases),
            "candidate_kernel_ids": sum(c["candidate_kernel_id"] is not None for c in cases),
            "exact_current_notebook_cells": sum(
                c["source_verified_in_current_notebook"] for c in cases
            ),
        },
        "cases": cases,
        "limitations": [
            "Current Kaggle notebook snapshots are not pinned historical annotation revisions.",
            "Third-party recovered kernel IDs may not identify the original annotation source.",
            "Exact code-cell matches verify current source presence, not leakage labels.",
            "All 25 cases were selected by published positive label after test-set exploration.",
            "No label correction or new detector accuracy is justified without independent review.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--derivative", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--notebooks", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve previous provenance audit")
    report = analyze(
        args.test, args.derivative, args.metadata, args.notebooks,
        args.archive, args.source_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(report["summary"])


if __name__ == "__main__":
    main()
