from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.contributions import build_combined_source_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build source index with external templates.")
    parser.add_argument("--contributions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = build_combined_source_index(args.contributions, args.output)
    print(f"Combined source index written to {destination}")


if __name__ == "__main__":
    main()

