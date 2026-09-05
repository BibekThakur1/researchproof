from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.annotation import export_blind_review
from researchproof.source_benchmark import build_source_cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a blinded source-code review package.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--salt",
        required=True,
        help="Private random text used only to shuffle case IDs",
    )
    args = parser.parse_args()
    form = export_blind_review(build_source_cases(), args.output, salt=args.salt)
    print(f"Blind review form written to {form}")
    print("Keep adjudication_key.json closed until both independent reviews are complete.")


if __name__ == "__main__":
    main()
