"""Verify and analyze returned evidence locally without loading a model or training."""

import argparse
import hashlib
import json
from pathlib import Path

from researchproof.neural_archive import inspect_archive, render_tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve previous analyses")
    report = inspect_archive(args.archive, args.source_manifest)
    report["archive_sha256"] = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    args.output.mkdir(parents=True)
    (args.output / "analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (args.output / "tables.md").write_text(render_tables(report))
    print(f"Evidence consistency verified; analysis saved to {args.output}")
    print("Human review, independent confirmation and novelty assessment remain separate.")


if __name__ == "__main__":
    main()
