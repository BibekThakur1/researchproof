"""Audit CodeBERT outcomes by train/test source overlap without retraining."""

import argparse
import csv
import hashlib
import json
import warnings
import zipfile
from dataclasses import asdict
from pathlib import Path

from researchproof.audit import classification_metrics
from researchproof.neural_archive import inspect_archive
from researchproof.neural_evidence import EXPECTED_PROTOCOL
from researchproof.robustness import fingerprint


def read_canonical(path, name):
    expected = EXPECTED_PROTOCOL["dataset_sha256"][name]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"canonical data fingerprint differs: {name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if any(row["has_data_leakage"] not in ("0", "1") for row in rows):
        raise ValueError(f"invalid labels: {name}")
    return rows


def syntax_key(text):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return fingerprint(text)
    except (SyntaxError, ValueError):
        return None


def analyze(archive, source_manifest, train_path, test_path):
    inspect_archive(archive, source_manifest)
    training = read_canonical(train_path, "train_annotated.csv")
    testing = read_canonical(test_path, "test_annotated.csv")
    if len(training) != 1523 or len(testing) != 381:
        raise ValueError("unexpected canonical dataset size")
    train_text = {row["code_block"] for row in training}
    train_ast = {key for row in training if (key := syntax_key(row["code_block"])) is not None}
    cases = {}
    for index, row in enumerate(testing, 1):
        text = row["code_block"]
        key = syntax_key(text)
        cases[f"published-test-row-{index}"] = {
            "label": int(row["has_data_leakage"]),
            "exact": text in train_text,
            "ast": key in train_ast if key is not None else False,
        }
    result = {
        "scope": "post-hoc sensitivity analysis of explored published split",
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "data_sha256": EXPECTED_PROTOCOL["dataset_sha256"],
        "overlap_counts": {
            "exact": sum(row["exact"] for row in cases.values()),
            "ast": sum(row["ast"] for row in cases.values()),
            "union": sum(row["exact"] or row["ast"] for row in cases.values()),
        },
        "seeds": [],
    }
    with zipfile.ZipFile(archive) as handle:
        for seed in (0, 1, 2):
            records = json.loads(handle.read(f"seed{seed}/predictions.json"))
            original = {row["id"]: row for row in records if row["variant"] == "original"}
            if set(original) != set(cases):
                raise ValueError("prediction IDs differ from canonical test rows")
            for case_id, prediction in original.items():
                if prediction["label"] != cases[case_id]["label"]:
                    raise ValueError("prediction label differs from canonical data")
                if prediction["source_sha256"] != hashlib.sha256(
                    testing[int(case_id.rsplit("-", 1)[1]) - 1]["code_block"].encode()
                ).hexdigest():
                    raise ValueError("prediction source differs from canonical data")
            summary = {"seed": seed, "subsets": {}}
            for name, condition in (
                ("all", lambda row: True),
                ("nonoverlap", lambda row: not (row["exact"] or row["ast"])),
                ("overlap", lambda row: row["exact"] or row["ast"]),
            ):
                selected = [case_id for case_id, row in cases.items() if condition(row)]
                labels = [cases[case_id]["label"] for case_id in selected]
                predictions = [original[case_id]["prediction"] for case_id in selected]
                summary["subsets"][name] = asdict(classification_metrics(labels, predictions))
            result["seeds"].append(summary)
    result["limitations"] = [
        "Post-hoc exact/AST deduplication does not detect semantic near-duplicates "
        "or shared repositories.",
        "The remaining split is explored and not an independent confirmation corpus.",
        "Small positive counts prohibit strong subgroup performance claims.",
    ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve prior analyses")
    report = analyze(args.archive, args.source_manifest, args.train, args.test)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["overlap_counts"], indent=2))
    for item in report["seeds"]:
        print(item["seed"], item["subsets"]["nonoverlap"])


if __name__ == "__main__":
    main()
