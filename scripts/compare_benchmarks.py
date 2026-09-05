from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.reproduce import write_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two generated benchmark indices.")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = write_comparison(args.reference, args.candidate, args.output)
    print(f"Reproducibility comparison written to {destination}")


if __name__ == "__main__":
    main()

