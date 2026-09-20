"""Frozen lightweight baselines on published data; not a CodeBERT reproduction."""

import csv
import hashlib
import json
import platform
import warnings
from dataclasses import asdict
from pathlib import Path

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from researchproof.audit import classification_metrics
from researchproof.robustness import fingerprint, pair_success, variants
from researchproof.source_benchmark import build_source_cases

ROOT = Path("artifacts/peerj2025")


def read(name):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["has_data_leakage"] not in {"0", "1"} or not row["code_block"]:
            raise ValueError("missing or invalid labeled source")
    return rows


def key(source):
    try:
        return fingerprint(source)
    except (SyntaxError, ValueError):
        return None


def main():
    inventory = json.loads((ROOT / "inventory.json").read_text())
    for name in ("train_annotated.csv", "test_annotated.csv"):
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != inventory[name]["sha256"]:
            raise ValueError(f"input differs from downloaded inventory: {name}")
    training, testing = read("train_annotated.csv"), read("test_annotated.csv")
    models = {
        "word_tfidf_logistic": make_pipeline(
            TfidfVectorizer(lowercase=False, ngram_range=(1, 2)),
            LogisticRegression(C=1, class_weight="balanced", max_iter=2000, random_state=0),
        ),
        "character_tfidf_logistic": make_pipeline(
            TfidfVectorizer(analyzer="char", ngram_range=(3, 5), max_features=30000),
            LogisticRegression(C=1, class_weight="balanced", max_iter=2000, random_state=0),
        ),
    }
    for model in models.values():
        model.fit(
            [r["code_block"] for r in training], [int(r["has_data_leakage"]) for r in training]
        )
    train_text = {r["code_block"] for r in training}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        train_ast = {k for r in training if (k := key(r["code_block"])) is not None}
        records = []
        for row_number, row in enumerate(testing, 1):
            source = row["code_block"]
            syntax = key(source)
            inputs = {"original": source}
            if syntax is not None:
                inputs.update(variants(source))
            predictions = {
                name: dict(
                    zip(
                        inputs,
                        model.predict(list(inputs.values())).astype(int).tolist(),
                        strict=True,
                    )
                )
                for name, model in models.items()
            }
            records.append(
                {
                    "id": f"published-test-row-{row_number}",
                    "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                    "label": int(row["has_data_leakage"]),
                    "parseable": syntax is not None,
                    "exact_train_match": source in train_text,
                    "ast_train_match": syntax in train_ast if syntax is not None else False,
                    "predictions": predictions,
                }
            )
    summary = {}
    for name in models:
        summary[name] = {}
        for subset in ("published_test", "no_exact_or_ast_train_match"):
            selected = [
                r
                for r in records
                if subset == "published_test"
                or not (r["exact_train_match"] or r["ast_train_match"])
            ]
            original = [r["predictions"][name]["original"] for r in selected]
            metrics = asdict(classification_metrics([r["label"] for r in selected], original))
            changes = {}
            for variant in ("neutral_comment", "safe_claim", "fault_claim", "formatting"):
                eligible = [r for r in selected if variant in r["predictions"][name]]
                changes[variant] = {
                    "eligible": len(eligible),
                    "flips": sum(
                        r["predictions"][name][variant] != r["predictions"][name]["original"]
                        for r in eligible
                    ),
                    "correct_to_wrong": sum(
                        r["predictions"][name]["original"] == r["label"]
                        and r["predictions"][name][variant] != r["label"]
                        for r in eligible
                    ),
                    "wrong_to_correct": sum(
                        r["predictions"][name]["original"] != r["label"]
                        and r["predictions"][name][variant] == r["label"]
                        for r in eligible
                    ),
                }
            summary[name][subset] = {"n": len(selected), "metrics": metrics, "edits": changes}
    # Separate, authored semantic-change controls. These are not natural external bugs.
    groups = {}
    for case in build_source_cases():
        group = (case.author_id, case.style_id, case.template_family, case.fault_family)
        groups.setdefault(group, {})[case.variant] = case.source
    paired = {}
    for name, model in models.items():
        pairs = []
        for group, endpoints in groups.items():
            if set(endpoints) == {"clean"}:
                continue  # Standalone hard negatives have no injected-fault counterpart.
            if set(endpoints) != {"clean", "faulty"}:
                raise ValueError("invalid constructed pair")
            clean, faulty = model.predict([endpoints["clean"], endpoints["faulty"]]).tolist()
            pairs.append(
                {
                    "group": group,
                    "clean_prediction": clean,
                    "faulty_prediction": faulty,
                    "both_correct": pair_success(bool(clean), bool(faulty)),
                }
            )
        paired[name] = {"pairs": pairs, "both_correct": sum(p["both_correct"] for p in pairs)}
    output = {
        "status": "exploratory_local_baselines_not_published_model_reproduction",
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "training_rows": len(training),
        "test_rows": len(testing),
        "training_positives": sum(int(r["has_data_leakage"]) for r in training),
        "test_positives": sum(r["label"] for r in records),
        "parseable_test": sum(r["parseable"] for r in records),
        "exact_overlap_rows": sum(r["exact_train_match"] for r in records),
        "ast_overlap_rows": sum(r["ast_train_match"] for r in records),
        "inventory": inventory,
        "implementation_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path("scripts/evaluate_robustness_pilot.py"),
                Path("src/researchproof/robustness.py"),
                Path("src/researchproof/source_benchmark.py"),
            )
        },
        "constant_controls": {
            str(value): asdict(
                classification_metrics([r["label"] for r in records], [value] * len(records))
            )
            for value in (False, True)
        },
        "summary": summary,
        "records": records,
        "constructed_semantic_pairs": paired,
        "limitations": [
            "No CodeBERT or LLM reproduction; no independently reviewed new labels.",
            "Snippet IDs do not establish repository independence; no confidence interval claims.",
            "Original test now used for development; not a fresh confirmation set.",
            "AST preservation is not whole-program behavioral equivalence.",
            "Incomplete snippets and context-dependent labels require human review.",
        ],
    }
    destination = Path("results/2026-09-20/robustness_pilot.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in output.items()
                if k not in {"records", "inventory", "constructed_semantic_pairs"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
