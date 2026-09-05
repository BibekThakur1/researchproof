from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.static_analysis import evaluate_symbolic_analyzer


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the symbolic provenance analyzer.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = evaluate_symbolic_analyzer(args.index, args.output)
    print(f"Symbolic analyzer report written to {destination}")


if __name__ == "__main__":
    main()

