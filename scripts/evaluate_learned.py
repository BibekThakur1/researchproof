from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.learned import evaluate_learned_baselines


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate learned ResearchProof baselines.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = evaluate_learned_baselines(args.index, args.output)
    print(f"Learned baseline report written to {destination}")


if __name__ == "__main__":
    main()

