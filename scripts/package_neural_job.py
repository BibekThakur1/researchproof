"""Build a small allowlisted compute bundle; do not upload it or include credentials/data."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

FILES = (
    "requirements-neural.txt",
    "docs/compute_bundle.md",
    "docs/codebert_runbook.md",
    "scripts/train_codebert.py",
    "scripts/run_codebert_seeds.py",
    "scripts/summarize_codebert.py",
    "scripts/export_codebert_results.py",
    "scripts/fetch_peerj_materials.py",
    "src/researchproof/__init__.py",
    "src/researchproof/robustness.py",
    "src/researchproof/neural_evidence.py",
    "src/researchproof/neural_study.py",
    "src/researchproof/neural_archive.py",
    "src/researchproof/audit.py",
    "neural_tests/test_training.py",
)


def build_bundle(root, output):
    # Read and validate every source before creating the artifact.
    contents = {name: (root / name).read_bytes() for name in FILES}
    manifest = {
        "purpose": "private compute transfer, not a public release",
        "data_and_credentials_included": False,
        "files_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in contents.items():
            archive.writestr(name, raw)
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_bundle(Path(__file__).resolve().parents[1], args.output)
    print(f"Created {args.output}; keep this transfer private")


if __name__ == "__main__":
    main()
