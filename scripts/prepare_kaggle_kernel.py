"""Build a private Kaggle notebook offline. Never uploads, downloads data, or trains."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from package_neural_job import FILES


def code_cell(identifier, source):
    return {
        "cell_type": "code",
        "id": identifier,
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source,
    }


def markdown_cell(identifier, source):
    return {"cell_type": "markdown", "id": identifier, "metadata": {}, "source": source}


def prepare(root, output):
    contents = {name: (root / name).read_bytes() for name in FILES}
    payload = {name: base64.b64encode(raw).decode("ascii") for name, raw in contents.items()}
    hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()}
    template = (root / "scripts/kaggle_runtime.py").read_text()
    source = template.replace("PAYLOAD = {}", f"PAYLOAD = {payload!r}", 1).replace(
        "HASHES = {}", f"HASHES = {hashes!r}", 1
    )
    script = source + "\n\nif __name__ == '__main__':\n    main()\n"
    compile(script, "job.py", "exec")
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "cells": [
            markdown_cell(
                "instructions",
                "# ResearchProof: private CodeBERT experiment\n\n"
                "Choose GPU T4 and enable Internet. Use **Save Version → Save & Run All** "
                "for a saved batch run. Keep this notebook private. The fixed experiment "
                "runs seeds 0, 1 and 2; do not choose a seed based on test scores.\n\n"
                "GPU/session availability is checked before training. A setup failure is "
                "not a research result. Preserve logs before starting a new session.",
            ),
            code_cell("definitions", source),
            markdown_cell(
                "preflight-note",
                "## 1. Check GPU, Internet and disk\n\n"
                "Stops early if required hardware or data/model hosts are unavailable.",
            ),
            code_cell("preflight", "stage(preflight)"),
            markdown_cell(
                "setup-note",
                "## 2. Prepare the isolated environment\n\n"
                "Verify source hashes, fetch pinned data, test the code, and run small "
                "GPU checks. These checks are not experimental findings.",
            ),
            code_cell("setup", "stage(setup)"),
            markdown_cell(
                "training-note",
                "## 3. Run all three prespecified seeds\n\n"
                "Four epochs per seed, 512 tokens and effective batch 16. Training "
                "prints loss after each epoch. Evaluation follows training. The run may "
                "take hours; actual GPU throughput has not been measured yet.",
            ),
            code_cell("training", "stage(train)"),
            markdown_cell(
                "export-note",
                "## 4. Validate and save results\n\n"
                "Download `researchproof_evidence.zip` for small metadata, predictions, "
                "logs and generated tables. Preserve the three checkpoint directories "
                "separately. A complete export does not establish novelty "
                "or publication readiness.",
            ),
            code_cell("export", "stage(export)"),
        ],
    }
    metadata = {
        "id": "bibekthakur1/researchproof-codebert-20261020",
        "title": "ResearchProof CodeBERT 20261020",
        "code_file": "job.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "job.py").write_text(script)
    (output / "job.ipynb").write_text(json.dumps(notebook) + "\n")
    (output / "source_hashes.json").write_text(json.dumps(hashes, indent=2) + "\n")
    (output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    manifest = {
        "purpose": "private GPU execution; no results or data included",
        "source_files": len(hashes),
        "job_sha256": hashlib.sha256(script.encode()).hexdigest(),
        "notebook_sha256": hashlib.sha256((output / "job.ipynb").read_bytes()).hexdigest(),
        "runtime_template_sha256": hashlib.sha256(template.encode()).hexdigest(),
    }
    (output / "package.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return hashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    hashes = prepare(Path(__file__).resolve().parents[1], args.output)
    print(f"Prepared {len(hashes)} allowlisted files in {args.output}; nothing uploaded.")
