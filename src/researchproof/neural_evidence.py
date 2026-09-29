"""Validate completed neural evidence; never turn smoke runs into research tables."""

from dataclasses import asdict

from researchproof.audit import classification_metrics

EXPECTED_PROTOCOL = {
    "model": "microsoft/codebert-base",
    "revision": "3b0952feddeffad0063f274080e3c23d75e7eb39",
    "max_length": 512,
    "effective_batch": 16,
    "lr": 5e-5,
    "weight_decay": 0.0,
    "text_preprocessing": "lowercase_like_upstream",
    "dataset_sha256": {
        "train_annotated.csv": "661f366824fef28e9fed3972573983d739217d63cc2fd570d3c104682022e349",
        "test_annotated.csv": "edd9f8c43687ad19828ff8b8c6f20ca08f85fbd7c317261adf93414f1101ecb3",
    },
}


def summarize(run, records):
    if run.get("status") != "completed_modern_fixed_budget_no_augmentation":
        raise ValueError("only a completed full training run can produce research tables")
    if run.get("training_rows") != 1523 or run.get("epochs") != 4:
        raise ValueError("unexpected training protocol")
    if run.get("test_used_for_selection") is not False:
        raise ValueError("test-based selection is outside this protocol")
    if any(run.get(key) != expected for key, expected in EXPECTED_PROTOCOL.items()):
        raise ValueError("unexpected model, data version or training configuration")
    if len(records) != run.get("prediction_records"):
        raise ValueError("incomplete predictions")
    lookup = {}
    for row in records:
        key = (row["id"], row["variant"])
        if key in lookup or type(row["prediction"]) is not int or row["prediction"] not in (0, 1):
            raise ValueError("duplicate record or invalid prediction")
        if type(row["label"]) is not int or row["label"] not in (0, 1):
            raise ValueError("invalid label")
        if type(row["token_input_changed"]) is not bool:
            raise ValueError("invalid token-change flag")
        if row["variant"] == "original" and row["token_input_changed"]:
            raise ValueError("original cannot have changed tokens")
        lookup[key] = row
    originals = [r for r in records if r["variant"] == "original"]
    if len(originals) != 381 or sum(r["label"] for r in originals) != 25:
        raise ValueError("unexpected published test set")
    edits = {}
    for variant in ("neutral_comment", "safe_claim", "fault_claim", "formatting"):
        rows = [r for r in records if r["variant"] == variant]
        if len(rows) != 340:
            raise ValueError("missing transformation records")
        for row in rows:
            original = lookup.get((row["id"], "original"))
            if original is None or row["label"] != original["label"]:
                raise ValueError("unmatched or relabeled pair")
            if not row["token_input_changed"] and row["prediction"] != original["prediction"]:
                raise ValueError("identical token inputs produced different predictions")
        edits[variant] = {
            "paired": len(rows),
            "token_changed": sum(r["token_input_changed"] for r in rows),
            "flips": sum(
                r["prediction"] != lookup[(r["id"], "original")]["prediction"] for r in rows
            ),
            "correct_to_wrong": sum(
                lookup[(r["id"], "original")]["prediction"] == r["label"]
                and r["prediction"] != r["label"]
                for r in rows
            ),
            "wrong_to_correct": sum(
                lookup[(r["id"], "original")]["prediction"] != r["label"]
                and r["prediction"] == r["label"]
                for r in rows
            ),
        }
    if len(records) != 1741:
        raise ValueError("unexpected record count or variant")
    return {
        "metrics": asdict(
            classification_metrics(
                [r["label"] for r in originals], [r["prediction"] for r in originals]
            )
        ),
        "edits": edits,
    }
