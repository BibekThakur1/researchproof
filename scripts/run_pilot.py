from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from researchproof.experiment import run_pilot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the first paired ResearchProof pilot.")
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    destination = run_pilot(config, Path(config["output_dir"]))
    print(f"Pilot artifacts written to {destination}")


if __name__ == "__main__":
    main()

