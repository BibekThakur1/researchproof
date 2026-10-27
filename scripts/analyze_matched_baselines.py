"""Compare saved CodeBERT and lexical decisions on identical published cases."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from researchproof.neural_archive import inspect_archive
from researchproof.neural_evidence import EXPECTED_PROTOCOL

BASELINES = ("word_tfidf_logistic", "character_tfidf_logistic")


def analyze(archive, source_manifest, pilot_path):
    inspect_archive(archive, source_manifest)
    pilot = json.loads(pilot_path.read_text())
    expected = EXPECTED_PROTOCOL["dataset_sha256"]
    if any(pilot["inventory"][name]["sha256"] != digest for name, digest in expected.items()):
        raise ValueError("lexical pilot used a different dataset version")
    lexical = {row["id"]: row for row in pilot["records"]}
    if len(lexical) != 381:
        raise ValueError("lexical pilot is missing original cases")
    report = {
        "scope": "exploratory matched-case descriptive comparison on explored split",
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "pilot_sha256": hashlib.sha256(pilot_path.read_bytes()).hexdigest(),
        "cases": 381,
        "seeds": [],
        "limitations": [
            "All models share one explored published test split.",
            "Lexical and CodeBERT training protocols differ; this is not a controlled ablation.",
            "Case-wise agreement does not establish statistical superiority or generalization.",
        ],
    }
    with zipfile.ZipFile(archive) as handle:
        for seed in (0, 1, 2):
            rows = json.loads(handle.read(f"seed{seed}/predictions.json"))
            neural = {row["id"]: row for row in rows if row["variant"] == "original"}
            if set(neural) != set(lexical):
                raise ValueError("original test IDs differ between models")
            seed_result = {"seed": seed, "baselines": {}}
            for baseline in BASELINES:
                subsets = {}
                for group, selected in (
                    ("all", list(neural)),
                    ("positive", [case_id for case_id in neural if neural[case_id]["label"] == 1]),
                    ("negative", [case_id for case_id in neural if neural[case_id]["label"] == 0]),
                ):
                    outcomes = {
                        "both_correct": 0,
                        "codebert_only_correct": 0,
                        "lexical_only_correct": 0,
                        "both_wrong": 0,
                    }
                    for case_id in selected:
                        a, b = neural[case_id], lexical[case_id]
                        if a["label"] != b["label"] or a["source_sha256"] != b["source_sha256"]:
                            raise ValueError("labels or source fingerprints differ")
                        codebert_correct = a["prediction"] == a["label"]
                        lexical_correct = b["predictions"][baseline]["original"] == b["label"]
                        key = (
                            "both_correct" if codebert_correct and lexical_correct
                            else "codebert_only_correct" if codebert_correct
                            else "lexical_only_correct" if lexical_correct
                            else "both_wrong"
                        )
                        outcomes[key] += 1
                    subsets[group] = outcomes
                seed_result["baselines"][baseline] = subsets
            report["seeds"].append(seed_result)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve previous analyses")
    report = analyze(args.archive, args.source_manifest, args.pilot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["seeds"], indent=2))


if __name__ == "__main__":
    main()
