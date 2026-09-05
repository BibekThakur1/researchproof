from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.statistics import summarize_paired_effects


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize paired clean/faulty score changes.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = summarize_paired_effects(args.index, args.output)
    print(f"Paired effect report written to {destination}")


if __name__ == "__main__":
    main()

