from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.annotation import export_blind_review
from researchproof.source_benchmark import build_source_cases, read_source_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a blinded source-code review package.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-index",
        type=Path,
        help="Optional combined JSONL index; defaults to repository-authored pilot cases",
    )
    parser.add_argument(
        "--salt",
        required=True,
        help="Private random text used only to shuffle case IDs",
    )
    args = parser.parse_args()
    cases = read_source_benchmark(args.source_index) if args.source_index else build_source_cases()
    form = export_blind_review(cases, args.output, salt=args.salt)
    print(f"Blind review form written to {form}")
    print("Keep adjudication_key.json closed until both independent reviews are complete.")


if __name__ == "__main__":
    main()
