"""Versioned JSON transport for explicit selection evidence, without pickle execution.

Checksums detect accidental changes, not malicious edits or omitted instrumentation.
Missing provenance is represented as incomplete even when a scalar score survives.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from researchproof.selection_provenance import ModelState, Rows, Score


def _digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _rows(value: object) -> Rows:
    if not isinstance(value, list):
        raise ValueError("row provenance must be a list")
    result = set()
    for item in value:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or type(item[1]) is not int
        ):
            raise ValueError("each row needs a dataset namespace and integer identity")
        result.add((item[0], item[1]))
    return frozenset(result)


def save_scores(path: Path, models: list[ModelState], scores: list[Score]) -> None:
    if not models or len(models) != len(scores):
        raise ValueError("one score per model is required")
    if len({model.model_id for model in models}) != len(models):
        raise ValueError("model IDs must be unique")
    payload = {
        "version": 1,
        "records": [
            {
                "model_id": model.model_id,
                "value": score.value,
                "selection_rows": sorted(model.selection_rows),
                "observed_rows": sorted(score.observed_rows),
                "model_complete": model.complete,
                "score_complete": score.complete,
            }
            for model, score in zip(models, scores, strict=True)
        ],
    }
    envelope = {"payload": payload, "sha256": _digest(payload)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_scores(path: Path) -> tuple[list[ModelState], list[Score]]:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(envelope, dict) or not isinstance(envelope.get("payload"), dict):
        raise ValueError("invalid score envelope")
    payload = envelope["payload"]
    if envelope.get("sha256") != _digest(payload):
        raise ValueError("score checksum mismatch")
    if type(payload.get("version")) is not int or payload["version"] != 1:
        raise ValueError("unsupported score format")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("non-empty score records are required")
    models, scores = [], []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid score record")
        identifier = record.get("model_id")
        value = record.get("value")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("model ID is required")
        if type(value) not in (int, float):
            raise ValueError("numeric score is required")
        for field in ("model_complete", "score_complete"):
            if field in record and type(record[field]) is not bool:
                raise ValueError("completeness must be Boolean")
        selection = _rows(record["selection_rows"]) if "selection_rows" in record else frozenset()
        observed = _rows(record["observed_rows"]) if "observed_rows" in record else frozenset()
        models.append(
            ModelState(
                identifier,
                selection,
                record.get("model_complete", False) and "selection_rows" in record,
            )
        )
        scores.append(
            Score(
                float(value),
                observed,
                record.get("score_complete", False) and bool(observed),
            )
        )
    if len({model.model_id for model in models}) != len(models):
        raise ValueError("duplicate model ID")
    return models, scores
