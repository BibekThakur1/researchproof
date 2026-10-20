"""Export completed CodeBERT evidence without checkpoints, caches or raw source datasets."""

import argparse
from pathlib import Path

from researchproof.neural_archive import build_archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_archive(args.study, args.context, args.output)
    print(f"Validated three seeds; compact evidence saved to {args.output}")


if __name__ == "__main__":
    main()
