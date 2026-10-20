"""Run all three prespecified seeds, retaining logs and validating completed outputs."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from researchproof.neural_evidence import summarize


def validate_directory(directory, seed):
    run = json.loads((directory / "run.json").read_text())
    if run.get("seed") != seed:
        raise ValueError("run seed does not match the requested directory")
    records = json.loads((directory / "predictions.json").read_text())
    return summarize(run, records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=["cuda", "mps", "cpu"], default="cuda")
    parser.add_argument("--micro-batch", type=int, choices=range(1, 17), default=2)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--cache", type=Path, help="Optional shared model cache outside saved outputs"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    cache = args.cache.resolve() if args.cache else root / "artifacts/hf_cache"
    environment["HF_XET_CACHE"] = str(cache / "xet")
    for seed in (0, 1, 2):
        directory = destination / f"seed{seed}"
        if directory.exists():
            # Failed/partial runs raise instead of being overwritten or counted complete.
            validate_directory(directory, seed)
            print(f"Preserved validated completed seed {seed}", flush=True)
            continue
        command = [
            sys.executable,
            str(root / "scripts/train_codebert.py"),
            "--device",
            args.device,
            "--seed",
            str(seed),
            "--micro-batch",
            str(args.micro_batch),
            "--output",
            str(directory),
            "--cache",
            str(cache),
        ]
        log_path = destination / f"seed{seed}.log"
        with log_path.open("x") as log:
            log.write(json.dumps({"command": command, "working_directory": str(root)}) + "\n")
            log.flush()
            with subprocess.Popen(
                command,
                cwd=root,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            ) as process:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    print(line, end="", flush=True)
                if process.wait() != 0:
                    raise RuntimeError(
                        f"seed {seed} failed; preserve {log_path} and diagnose before retrying"
                    )
        validate_directory(directory, seed)
    print(
        "All three runs passed structural evidence validation. Scientific review remains required."
    )


if __name__ == "__main__":
    main()
