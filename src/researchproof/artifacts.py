from __future__ import annotations

import hashlib
from pathlib import Path

MANIFEST_NAME = "MANIFEST.sha256"


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_artifact_manifest(root: Path) -> Path:
    if not root.is_dir():
        raise ValueError(f"artifact root does not exist: {root}")
    files = sorted(
        path for path in root.rglob("*") if path.is_file() and path.name != MANIFEST_NAME
    )
    if not files:
        raise ValueError("artifact root contains no files")
    lines = [f"{file_sha256(path)}  {path.relative_to(root).as_posix()}" for path in files]
    destination = root / MANIFEST_NAME
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def verify_artifact_manifest(root: Path) -> list[str]:
    manifest = root / MANIFEST_NAME
    if not manifest.is_file():
        raise ValueError(f"missing {MANIFEST_NAME} in {root}")
    failures: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", maxsplit=1)
        path = root / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")
        elif file_sha256(path) != expected:
            failures.append(f"checksum mismatch: {relative}")
    return failures

