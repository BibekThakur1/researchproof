"""Read-only evaluation against published ASE'22 labels; never execute notebooks."""

from __future__ import annotations

import csv
import hashlib
import json
import warnings
from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

import researchproof.static_analysis as static_analysis
from researchproof.ast_baseline import extract_ast_features
from researchproof.audit import classification_metrics
from researchproof.notebook import NotebookError, normalize_notebook
from researchproof.source_benchmark import build_source_cases

ROOT = Path("artifacts/external_ase22")


def label(text: str) -> bool | None:
    text = text.strip()
    if text.startswith("Y"):
        return True
    if text.startswith("N"):
        return False
    return None


def main() -> None:
    training = build_source_cases()
    vectorizer = DictVectorizer()
    features = vectorizer.fit_transform([extract_ast_features(case.source) for case in training])
    learned = LogisticRegression(max_iter=1000, random_state=0).fit(
        features,
        [case.variant == "faulty" for case in training],
    )
    with (ROOT / "ground-truth.csv").open() as handle:
        gold = list(csv.DictReader(handle))
    with (ROOT / "analysis-result.csv").open() as handle:
        archived = {row["nb"]: row for row in csv.DictReader(handle)}
    records = []
    with ZipFile(ROOT / "sample-notebooks.zip") as archive:
        for row in gold:
            path = Path(row["nb"])
            member = f"sample_notebooks/{path.parent.name}-{path.stem}.ipynb"
            record = {
                "notebook": row["nb"],
                "member": member,
                "labels": {key: label(row[key]) for key in ("pre", "overlap", "multi")},
            }
            historical = archived.get(row["nb"])
            record["archived_predictions"] = {
                key: historical[key] == "True" if historical else None
                for key in ("pre", "overlap", "multi")
            }
            try:
                raw = archive.read(member)
                payload = json.loads(raw)
                source = normalize_notebook(payload, "document").source
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", SyntaxWarning)
                    findings = static_analysis.analyze_source(source)
                    probability = float(
                        learned.predict_proba(vectorizer.transform([extract_ast_features(source)]))[
                            0, 1
                        ]
                    )
                kinds = {finding.kind for finding in findings}
                record.update(
                    {
                        "status": "parsed",
                        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                        "syntax_warnings": len(caught),
                        "learned_any_probability": probability,
                        "predictions": {
                            "pre": bool(
                                kinds
                                & {
                                    "preprocessing_before_split",
                                    "supervised_selection_before_split",
                                }
                            ),
                            "overlap": "test_data_reaches_model_fit" in kinds,
                            "multi": "repeated_test_tuning" in kinds,
                        },
                        "finding_lines": [finding.line for finding in findings],
                    }
                )
            except (KeyError, SyntaxError, NotebookError, UnicodeError, ValueError) as error:
                record.update(
                    {
                        "status": type(error).__name__,
                        "predictions": {key: None for key in ("pre", "overlap", "multi")},
                        "error": str(error)[:200],
                    }
                )
            records.append(record)

    summary = {
        "status": "external_exploratory_evaluation_frozen_local_analyzer",
        "corpus_rows": len(records),
        "parsed": sum(r["status"] == "parsed" for r in records),
        "normalization": "document order; notebook magics commented; no external code execution",
        "local_analyzer_sha256": hashlib.sha256(
            Path(static_analysis.__file__).read_bytes()
        ).hexdigest(),
        "inventory": json.loads((ROOT / "inventory.json").read_text()),
        "local": {},
        "archived_published_output": {},
        "warning": (
            "Archived predictions are the authors' saved output, not a rerun. Different input "
            "normalization and tool environments prevent a controlled head-to-head claim. "
            "Missing/blank labels and unparsed sources are excluded with coverage reported."
        ),
    }
    for key in ("pre", "overlap", "multi"):
        eligible = [r for r in records if r["labels"][key] is not None]
        for field, dest in (
            ("predictions", "local"),
            ("archived_predictions", "archived_published_output"),
        ):
            answered = [r for r in eligible if r[field][key] is not None]
            result = asdict(
                classification_metrics(
                    [r["labels"][key] for r in answered],
                    [r[field][key] for r in answered],
                )
            )
            result.update({"eligible": len(eligible), "unanswered": len(eligible) - len(answered)})
            summary[dest][key] = result
    known = [r for r in records if all(v is not None for v in r["labels"].values())]
    predicted = [r for r in known if "learned_any_probability" in r]
    summary["synthetic_trained_ast_external"] = {
        "training_cases": len(training),
        "external_training_cases": 0,
        "eligible": len(known),
        "unanswered": len(known) - len(predicted),
        "decision_threshold": 0.5,
        "metrics": asdict(
            classification_metrics(
                [any(r["labels"].values()) for r in predicted],
                [r["learned_any_probability"] >= 0.5 for r in predicted],
            )
        ),
        "always_fault_metrics": asdict(
            classification_metrics(
                [any(r["labels"].values()) for r in predicted],
                [True] * len(predicted),
            )
        ),
    }
    (ROOT / "evaluation_records.json").write_text(json.dumps(records, indent=2) + "\n")
    (ROOT / "evaluation_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "corpus_rows",
                    "parsed",
                    "local",
                    "synthetic_trained_ast_external",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
