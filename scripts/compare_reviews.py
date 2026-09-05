from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.adjudication import write_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two independent blinded reviews.")
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = write_comparison(args.first, args.second, args.output)
    print(f"Agreement report written to {destination}")


if __name__ == "__main__":
    main()

