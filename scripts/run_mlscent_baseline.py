"""Run pinned upstream detector APIs on source files, never import the analyzed code.

Run with artifacts/mlscent_env/bin/python after the documented isolated setup.
"""

import contextlib
import hashlib
import importlib.metadata
import io
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

PIN = "c22cb3ad5fd2927434dcb77c1f9ce475e44d7cb4"
UPSTREAM = Path("artifacts/mlscent_source")


def classify(result, diagnostic, component):
    if component == "ml":
        positive = any("data leakage" in item.get("smell", "").lower() for item in result)
    else:
        positive = any(item.get("name") == "Data Leakage Checker" for item in result)
    if "error" in diagnostic.lower():
        return {"status": "error", "prediction": True if positive else None}
    if "Skipping" in diagnostic:
        return {"status": "skipped_no_import", "prediction": None}
    return {"status": "checked", "prediction": positive}


def main():
    head = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "status", "--porcelain"], text=True
    )
    if head != PIN or dirty:
        raise ValueError("upstream must be the clean pinned revision")
    sys.path.insert(0, str(UPSTREAM.resolve()))
    from ml_code_smell_detector import FrameworkSpecificSmellDetector, ML_SmellDetector

    input_path = Path("artifacts/mlscent_inputs.jsonl")
    inputs = [json.loads(line) for line in input_path.read_text().splitlines()]
    records = []
    with tempfile.TemporaryDirectory(prefix="rp_mls_") as directory:
        for index, item in enumerate(inputs):
            if item.get("preparation_error"):
                records.append(
                    {
                        **{k: v for k, v in item.items() if k != "source"},
                        "source_sha256": None,
                        "prediction": None,
                        "components": {
                            name: {"status": "normalization_error", "prediction": None}
                            for name in ("ml", "framework")
                        },
                    }
                )
                continue
            path = Path(directory) / f"sample_{index}.py"
            path.write_text(item["source"], encoding="utf-8")
            components = {}
            for name, detector_type in (
                ("ml", ML_SmellDetector),
                ("framework", FrameworkSpecificSmellDetector),
            ):
                diagnostic = io.StringIO()
                with contextlib.redirect_stderr(diagnostic), contextlib.redirect_stdout(diagnostic):
                    result = detector_type().detect_smells(str(path))
                components[name] = classify(result, diagnostic.getvalue(), name)
            values = [v["prediction"] for v in components.values()]
            prediction = (
                True if True in values else False if all(v is False for v in values) else None
            )
            records.append(
                {
                    **{k: v for k, v in item.items() if k != "source"},
                    "source_sha256": hashlib.sha256(item["source"].encode()).hexdigest(),
                    "components": components,
                    "prediction": prediction,
                }
            )
            if (index + 1) % 250 == 0:
                print(f"Analyzed {index + 1}/{len(inputs)}", flush=True)
    summary = {}
    for corpus in sorted({row["corpus"] for row in records}):
        selection = [
            r
            for r in records
            if r["corpus"] == corpus and (corpus != "peerj_test" or r["variant"] == "original")
        ]
        answered = [r for r in selection if r["prediction"] is not None and r["label"] is not None]
        summary[corpus] = {
            "inputs": len(selection),
            "labeled_inputs": sum(r["label"] is not None for r in selection),
            "answered_including_unlabeled": sum(r["prediction"] is not None for r in selection),
            "answered": len(answered),
            "positive_labels_answered": sum(r["label"] for r in answered),
            "tp": sum(r["label"] == 1 and r["prediction"] for r in answered),
            "fp": sum(r["label"] == 0 and r["prediction"] for r in answered),
            "tn": sum(r["label"] == 0 and not r["prediction"] for r in answered),
            "fn": sum(r["label"] == 1 and not r["prediction"] for r in answered),
        }
    original = {
        r["group"]: r for r in records if r["corpus"] == "peerj_test" and r["variant"] == "original"
    }
    edits = {}
    for edit in ("neutral_comment", "safe_claim", "fault_claim", "formatting"):
        matched = [
            (original[r["group"]], r)
            for r in records
            if r["corpus"] == "peerj_test" and r["variant"] == edit
        ]
        answered = [
            (a, b)
            for a, b in matched
            if a["prediction"] is not None and b["prediction"] is not None
        ]
        edits[edit] = {
            "paired": len(matched),
            "both_answered": len(answered),
            "flips": sum(a["prediction"] != b["prediction"] for a, b in answered),
        }
    output = {
        "status": "pinned_current_upstream_run_not_historical_paper_replication",
        "upstream": "https://github.com/KarthikShivasankar/ml_smells_detector",
        "revision": PIN,
        "python": platform.python_version(),
        "astroid": importlib.metadata.version("astroid"),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "summary": summary,
        "edits": edits,
        "records": records,
        "limitations": [
            "No-import skips and caught detector errors are unknown, never clean negatives.",
            "Snippet any-leakage labels may exceed this detector's covered categories.",
            "No claim of reproducing the publication's historical version or benchmark scores.",
            "Import-context condition modifies authored controls, not public snippets.",
        ],
    }
    destination = Path("results/2026-09-26/mlscent.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"summary": summary, "edits": edits}, indent=2))


if __name__ == "__main__":
    main()
