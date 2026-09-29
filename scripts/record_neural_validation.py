"""Archive engineering-check metadata without presenting it as research results."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve the earlier record")
    runs = []
    for directory in args.runs:
        path = directory / "run.json"
        raw = path.read_bytes()
        metadata = json.loads(raw)
        if metadata["status"] not in {
            "smoke_random_model_not_research",
            "preflight_two_training_rows_not_research",
        }:
            raise ValueError("this recorder accepts completed engineering checks only")
        if not metadata.get("training_loss") or not metadata.get("prediction_records"):
            raise ValueError("engineering check did not complete")
        runs.append(
            {
                "run_directory": directory.as_posix(),
                "run_sha256": hashlib.sha256(raw).hexdigest(),
                "predictions_sha256": hashlib.sha256(
                    (directory / "predictions.json").read_bytes()
                ).hexdigest(),
                "metadata": metadata,
            }
        )
    report = {
        "evidence_type": "engineering_validation_only",
        "supports_detector_performance_claim": False,
        "full_training_complete": False,
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
