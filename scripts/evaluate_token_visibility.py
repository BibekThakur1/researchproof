"""Measure real tokenizer exposure without training or executing dataset code."""

import argparse
import csv
import hashlib
import json
import warnings
from pathlib import Path

from researchproof.neural_evidence import EXPECTED_PROTOCOL
from researchproof.robustness import variants
from researchproof.token_visibility import compare_tokens


def main():
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve earlier results; choose a new output")
    data = Path("artifacts/peerj2025/test_annotated.csv")
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    if digest != EXPECTED_PROTOCOL["dataset_sha256"]["test_annotated.csv"]:
        raise ValueError("dataset version differs")
    tokenizer = AutoTokenizer.from_pretrained(
        EXPECTED_PROTOCOL["model"],
        revision=EXPECTED_PROTOCOL["revision"],
        use_fast=False,
        cache_dir="artifacts/hf_cache",
        local_files_only=True,
    )
    if tokenizer.truncation_side != "right" or tokenizer.num_special_tokens_to_add() != 2:
        raise ValueError("unexpected tokenizer truncation protocol")
    with data.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    records, excluded = [], []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        for index, row in enumerate(rows, 1):
            source = row["code_block"]
            identifier = f"published-test-row-{index}"
            try:
                changes = variants(source)
            except (SyntaxError, ValueError):
                excluded.append(identifier)
                continue
            original = tokenizer.encode(source.lower(), add_special_tokens=False, truncation=False)
            for name, changed in changes.items():
                edited = tokenizer.encode(
                    changed.lower(), add_special_tokens=False, truncation=False
                )
                for budget in (128, 256, 512):
                    result = compare_tokens(original, edited, budget)
                    # Cross-check the shortcut against the actual training tokenizer call.
                    actual = tokenizer(
                        [source.lower(), changed.lower()],
                        padding="max_length",
                        truncation=True,
                        max_length=budget,
                    )
                    actual_changed = any(values[0] != values[1] for values in actual.values())
                    if result["visible_tokens_changed"] != actual_changed:
                        raise AssertionError("visibility disagrees with actual tokenizer inputs")
                    records.append(
                        {
                            "id": identifier,
                            "variant": name,
                            "max_length": budget,
                            "original_content_tokens": len(original),
                            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                            **result,
                        }
                    )
    summary = {}
    for budget in (128, 256, 512):
        summary[str(budget)] = {}
        for variant in ("neutral_comment", "safe_claim", "fault_claim", "formatting"):
            selected = [r for r in records if r["max_length"] == budget and r["variant"] == variant]
            summary[str(budget)][variant] = {
                "pairs": len(selected),
                **{
                    key: sum(r[key] for r in selected)
                    for key in (
                        "raw_tokens_changed",
                        "visible_tokens_changed",
                        "change_erased_by_truncation",
                        "original_truncated",
                        "edited_truncated",
                    )
                },
            }
    report = {
        "status": "exploratory_tokenizer_diagnostic_not_detector_evaluation",
        "model": EXPECTED_PROTOCOL["model"],
        "revision": EXPECTED_PROTOCOL["revision"],
        "dataset_sha256": digest,
        "text_preprocessing": "lowercase_like_upstream",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "comparison_sha256": hashlib.sha256(
            Path("src/researchproof/token_visibility.py").read_bytes()
        ).hexdigest(),
        "transformation_sha256": hashlib.sha256(
            Path("src/researchproof/robustness.py").read_bytes()
        ).hexdigest(),
        "original_rows": len(rows),
        "excluded_unparseable_ids": excluded,
        "summary": summary,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"excluded": len(excluded), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
