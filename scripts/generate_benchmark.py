from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from researchproof.benchmark import generate_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paired ResearchProof benchmark cases.")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    destination = generate_benchmark(
        seeds=[int(seed) for seed in config["seeds"]],
        output_dir=Path(config["output_dir"]),
        dataset_ids=[str(dataset_id) for dataset_id in config["datasets"]],
        severities=[str(severity) for severity in config["severities"]],
        fault_families=[str(family) for family in config["fault_families"]],
        test_size=float(config["test_size"]),
    )
    print(f"Benchmark index written to {destination}")


if __name__ == "__main__":
    main()
