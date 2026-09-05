from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from researchproof.repair import verify_repair_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute and verify paired benchmark repairs.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    destination = verify_repair_suite(
        dataset_ids=[str(dataset_id) for dataset_id in config["datasets"]],
        seeds=[int(seed) for seed in config["seeds"]],
        destination=args.output,
    )
    print(f"Repair verification written to {destination}")


if __name__ == "__main__":
    main()

