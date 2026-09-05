from __future__ import annotations

import argparse
from pathlib import Path

from researchproof.artifacts import build_artifact_manifest, verify_artifact_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or verify an artifact checksum manifest.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        failures = verify_artifact_manifest(args.root)
        if failures:
            raise SystemExit("\n".join(failures))
        print(f"Verified artifact manifest in {args.root}")
    else:
        destination = build_artifact_manifest(args.root)
        print(f"Artifact manifest written to {destination}")


if __name__ == "__main__":
    main()

