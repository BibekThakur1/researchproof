import hashlib
import json
import subprocess
import sys

import pytest

from researchproof.score_store import load_scores, save_scores
from researchproof.selection_provenance import (
    ModelState,
    Score,
    audit_report,
    choose_model,
    row_keys,
)


def example(path):
    models = [ModelState("a"), ModelState("b")]
    scores = [Score(0.8, row_keys("dataset", [1, 2])), Score(0.7, row_keys("dataset", [1, 2]))]
    save_scores(path, models, scores)
    return models, scores


def rewrite(path, mutate):
    envelope = json.loads(path.read_text())
    mutate(envelope["payload"])
    body = json.dumps(envelope["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False)
    envelope["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    path.write_text(json.dumps(envelope))


def test_new_process_preserves_selection_and_fresh_test_semantics(tmp_path):
    path = tmp_path / "scores.json"
    example(path)
    program = """
import sys
from pathlib import Path
from researchproof.score_store import load_scores
from researchproof.selection_provenance import choose_model, audit_report, Score, row_keys
models, scores = load_scores(Path(sys.argv[1]))
chosen = choose_model(models, scores)
assert audit_report(chosen, scores[0]).status == 'selection_reuse'
fresh = Score(.9, row_keys('dataset', [3]))
assert audit_report(chosen, fresh).status == 'no_observed_selection_reuse'
print(chosen.model_id)
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(path)], check=True, capture_output=True, text=True
    )
    assert result.stdout.strip() == "a"


@pytest.mark.parametrize(
    "field", ["selection_rows", "observed_rows", "model_complete", "score_complete"]
)
def test_missing_provenance_never_becomes_verified_absence(tmp_path, field):
    path = tmp_path / "scores.json"
    example(path)
    rewrite(path, lambda payload: [record.pop(field) for record in payload["records"]])
    models, scores = load_scores(path)
    chosen = choose_model(models, scores)
    fresh = Score(0.9, row_keys("dataset", [3]))
    assert audit_report(chosen, fresh).status == "insufficient_evidence"


def test_scalar_edit_without_checksum_update_is_rejected(tmp_path):
    path = tmp_path / "scores.json"
    example(path)
    data = json.loads(path.read_text())
    data["payload"]["records"][0]["value"] = 0.1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="checksum"):
        load_scores(path)


def test_model_selection_history_round_trip(tmp_path):
    path = tmp_path / "scores.json"
    models, scores = example(path)
    selected = choose_model(models, scores)
    save_scores(path, [selected], [scores[0]])
    restored, values = load_scores(path)
    assert restored == [selected]
    assert audit_report(restored[0], values[0]).status == "selection_reuse"


def test_fractional_row_id_is_rejected_even_with_valid_checksum(tmp_path):
    path = tmp_path / "scores.json"
    example(path)
    rewrite(path, lambda payload: payload["records"][0].update(observed_rows=[["dataset", 1.5]]))
    with pytest.raises(ValueError, match="integer"):
        load_scores(path)
