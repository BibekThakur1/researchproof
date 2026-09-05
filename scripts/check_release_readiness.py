from __future__ import annotations

import argparse
import json
from pathlib import Path

from researchproof.release import write_release_readiness


def optional_path(value: str) -> Path | None:
    return None if value == "-" else Path(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check ResearchProof release gates.")
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--agreement", type=optional_path, default=None)
    parser.add_argument("--reproduction", type=optional_path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = write_release_readiness(
        Path.cwd(),
        args.benchmark,
        args.sources,
        args.agreement,
        args.reproduction,
        args.output,
    )
    report = json.loads(destination.read_text(encoding="utf-8"))
    print(f"Release status: {report['status']}")
    for gate in report["gates"]:
        marker = "PASS" if gate["passed"] else "FAIL"
        print(f"[{marker}] {gate['name']}: {gate['evidence']}")


if __name__ == "__main__":
    main()

