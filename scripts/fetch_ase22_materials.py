"""Fetch pinned public research materials for local, read-only source analysis."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REVISION = "3aec5fa09788d6659c6e1eac79cdc503340d9694"
ROOT = Path("artifacts/external_ase22")
BASE = f"https://raw.githubusercontent.com/malusamayo/GitHubAPI-Crawler/{REVISION}"
EXPECTED = {
    "README.md": "5c230cf5645b8920db9abf520ffdd0fa3ec29534aee0afeff02cbe52e7996677",
    "ground-truth.csv": "bb6a349d3514f08e695815e98af02d1f794bfe4d1a48f98c9ff686673b6e4efc",
    "analysis-result.csv": "873246c3f7bac0dd47a2ad79107ab00e0367a64bd3cf7f813a101f4c62ef63ec",
    "sample-notebooks.zip": "b645e3efb3fb5dcaf5dadb0b33d441d6816aede4af8a17ce482a5116f9896ca1",
}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    inventory = []
    for name in ("README.md", "ground-truth.csv", "analysis-result.csv", "sample-notebooks.zip"):
        relative = f"evaluation_materials/{name}"
        destination = ROOT / name
        if not destination.exists():
            partial = destination.with_name(destination.name + ".part")
            subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--silent",
                    "--show-error",
                    "--location",
                    "--proto",
                    "=https",
                    "--max-time",
                    "180",
                    "--max-filesize",
                    "60000000",
                    f"{BASE}/{relative}",
                    "--output",
                    str(partial),
                ],
                check=True,
            )
            if hashlib.sha256(partial.read_bytes()).hexdigest() != EXPECTED[name]:
                raise ValueError(f"download checksum mismatch: {name}")
            partial.replace(destination)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != EXPECTED[name]:
            raise ValueError(f"cached checksum mismatch: {name}")
        inventory.append(
            {
                "file": name,
                "url": f"{BASE}/{relative}",
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "bytes": destination.stat().st_size,
            }
        )
    (ROOT / "inventory.json").write_text(
        json.dumps(
            {
                "repository": "https://github.com/malusamayo/GitHubAPI-Crawler",
                "revision": REVISION,
                "files": inventory,
                "redistribution": "Not established for notebook corpus; cached locally only.",
                "execution": "Source is parsed only; external code is never executed.",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Cached pinned materials in {ROOT}")


if __name__ == "__main__":
    main()
