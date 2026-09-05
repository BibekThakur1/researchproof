from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.notebook import load_notebook


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Jupyter code cells for auditing.")
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--ordering", choices=("document", "execution"), default="document")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    program = load_notebook(args.notebook, args.ordering)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(program.source, encoding="utf-8")
    print(f"Normalized {len(program.cells)} code cells to {args.output}")


if __name__ == "__main__":
    main()

