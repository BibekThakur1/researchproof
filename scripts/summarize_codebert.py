import argparse
import hashlib
import json
from pathlib import Path

from researchproof.neural_evidence import summarize

parser = argparse.ArgumentParser(description="Summarize only a completed full neural run")
parser.add_argument("run_directory", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
configuration = args.run_directory / "run.json"
predictions = args.run_directory / "predictions.json"
summary = summarize(json.loads(configuration.read_text()), json.loads(predictions.read_text()))
summary["run_sha256"] = hashlib.sha256(configuration.read_bytes()).hexdigest()
summary["predictions_sha256"] = hashlib.sha256(predictions.read_bytes()).hexdigest()
if args.output.exists():
    parser.error("output exists; choose a new destination")
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
