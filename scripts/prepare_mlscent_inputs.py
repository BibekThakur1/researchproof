"""Prepare static-analysis inputs without running dataset snippets."""

import csv
import hashlib
import json
import warnings
from pathlib import Path
from zipfile import ZipFile

from researchproof.notebook import NotebookError, normalize_notebook
from researchproof.robustness import variants
from researchproof.source_benchmark import build_source_cases


def main():
    rows = []
    corpus = Path("artifacts/peerj2025")
    inventory = json.loads((corpus / "inventory.json").read_text())
    raw = (corpus / "test_annotated.csv").read_bytes()
    if hashlib.sha256(raw).hexdigest() != inventory["test_annotated.csv"]["sha256"]:
        raise ValueError("published input checksum mismatch")
    with (corpus / "test_annotated.csv").open(newline="", encoding="utf-8-sig") as handle:
        published = list(csv.DictReader(handle))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        for index, item in enumerate(published, 1):
            source = item["code_block"]
            edits = {"original": source}
            try:
                edits.update(variants(source))
            except (SyntaxError, ValueError):
                pass
            for edit, text in edits.items():
                rows.append(
                    {
                        "group": f"published-test-row-{index}",
                        "corpus": "peerj_test",
                        "variant": edit,
                        "label": int(item["has_data_leakage"]),
                        "source": text,
                    }
                )
    for case in build_source_cases():
        for prefix, header in (("as_is", ""), ("import_context", "import sklearn\n")):
            rows.append(
                {
                    "group": f"{case.style_id}:{case.template_family}",
                    "corpus": prefix,
                    "variant": case.variant,
                    "label": int(case.variant == "faulty"),
                    "source": header + case.source,
                }
            )
    ase = Path("artifacts/external_ase22")
    ase_inventory = json.loads((ase / "inventory.json").read_text())
    for entry in ase_inventory["files"]:
        if hashlib.sha256((ase / entry["file"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"ASE cached input changed: {entry['file']}")
    with (ase / "ground-truth.csv").open() as handle:
        labels = list(csv.DictReader(handle))
    with ZipFile(ase / "sample-notebooks.zip") as archive:
        for item in labels:
            path = Path(item["nb"])
            member = f"sample_notebooks/{path.parent.name}-{path.stem}.ipynb"
            preparation_error = None
            try:
                source = normalize_notebook(json.loads(archive.read(member)), "document").source
            except (KeyError, ValueError, UnicodeError, NotebookError) as error:
                source = ""
                preparation_error = type(error).__name__
            raw_label = item["pre"].strip()
            label = 1 if raw_label.startswith("Y") else 0 if raw_label.startswith("N") else None
            rows.append(
                {
                    "group": item["nb"],
                    "corpus": "ase22_preprocessing",
                    "variant": "original",
                    "label": label,
                    "source": source,
                    "preparation_error": preparation_error,
                }
            )
    # A positive control and its downstream-training extension: same preprocessing fault.
    base = "import sklearn\nX = scaler.fit_transform(X)\na, b = train_test_split(X)\n"
    for name, source in (
        ("before_split", base),
        ("with_downstream_fit", base + "model.fit(a, y)\n"),
    ):
        rows.append(
            {
                "group": "fit_before_split_control",
                "corpus": "sanity",
                "variant": name,
                "label": 1,
                "source": source,
            }
        )
    destination = Path("artifacts/mlscent_inputs.jsonl")
    complete = Path("examples/mlscent_preprocessing_control.py").read_text()
    for name, text in (("prefix", complete.split("# DOWNSTREAM")[0]), ("full", complete)):
        rows.append(
            {
                "group": "executable_preprocessing_control",
                "corpus": "executable_control",
                "variant": name,
                "label": 1,
                "source": text,
            }
        )
    destination.write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(f"Prepared {len(rows)} inputs; external sources are not executed")


if __name__ == "__main__":
    main()
