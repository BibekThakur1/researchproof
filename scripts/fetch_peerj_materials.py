"""Fetch pinned public artifacts as data; never import or execute archive code."""

import hashlib
import json
import subprocess
from pathlib import Path

FILES = {
    "train_annotated.csv": (43808766, "a71cdf85661b4d58b6d97db730a7dc28"),
    "test_annotated.csv": (43808769, "0c68a121b4129e52b1f445e85e9c5672"),
    "AL4Code.zip": (43808844, "1636c037e5243db3e5a77652b19ec098"),
}


def main():
    root = Path("artifacts/peerj2025")
    root.mkdir(parents=True, exist_ok=True)
    inventory = {}
    for name, (identifier, expected) in FILES.items():
        path = root / name
        url = f"https://ndownloader.figshare.com/files/{identifier}"
        if path.exists():
            raw = path.read_bytes()
        else:
            raw = subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--silent",
                    "--show-error",
                    "--location",
                    "--max-time",
                    "60",
                    url,
                ],
                check=True,
                capture_output=True,
            ).stdout
        if hashlib.md5(raw).hexdigest() != expected:
            raise ValueError(f"published artifact checksum mismatch: {name}")
        if not path.exists():
            path.write_bytes(raw)
        inventory[name] = {
            "url": url,
            "md5": expected,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    inventory["attribution"] = (
        "Alturayeif and Hassine (2025), Figshare dataset 24893799.v1 and code 24893832.v1; "
        "metadata license CC BY 4.0. Raw materials cached, not redistributed."
    )
    (root / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
