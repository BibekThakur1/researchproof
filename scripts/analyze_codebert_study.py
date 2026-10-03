"""Validate and summarize three full seed runs; refuse partial or mixed studies."""

import argparse
import hashlib
import json
from pathlib import Path

from researchproof.neural_study import analyze_runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve prior analyses")
    runs, fingerprints = [], {}
    for seed in (0, 1, 2):
        directory = args.study_directory / f"seed{seed}"
        configuration = directory / "run.json"
        predictions = directory / "predictions.json"
        run = json.loads(configuration.read_text())
        if run.get("seed") != seed:
            raise ValueError("seed metadata does not match directory")
        runs.append((run, json.loads(predictions.read_text())))
        fingerprints[str(seed)] = {
            "run_sha256": hashlib.sha256(configuration.read_bytes()).hexdigest(),
            "predictions_sha256": hashlib.sha256(predictions.read_bytes()).hexdigest(),
        }
    report = analyze_runs(runs)
    report["input_fingerprints"] = fingerprints
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Validated three seeds; descriptive report saved to {args.output}")


if __name__ == "__main__":
    main()
