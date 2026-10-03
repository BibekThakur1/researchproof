import copy
import hashlib

import pytest

from researchproof.neural_evidence import EXPECTED_PROTOCOL
from researchproof.neural_study import analyze_runs


def fixtures(visible=True):
    """Artificial predictions for software testing, never research findings."""
    runs = []
    for seed in (0, 1, 2):
        config = {
            **copy.deepcopy(EXPECTED_PROTOCOL),
            "seed": seed,
            "status": "completed_modern_fixed_budget_no_augmentation",
            "training_rows": 1523,
            "epochs": 4,
            "test_used_for_selection": False,
            "prediction_records": 1741,
            "implementation_sha256": "a" * 64,
            "device": "cpu",
            "micro_batch": 2,
            "python": "fixture",
            "torch": "fixture",
            "transformers": "fixture",
            "installed_packages": {},
        }
        records = []
        for i in range(381):
            variants = ["original"] + (
                ["neutral_comment", "safe_claim", "fault_claim", "formatting"] if i < 340 else []
            )
            for variant in variants:
                records.append(
                    {
                        "id": str(i),
                        "variant": variant,
                        "label": int(i < 25),
                        "prediction": int(i < 25),
                        "token_input_changed": visible and variant != "original",
                        "source_sha256": hashlib.sha256(f"{i}:{variant}".encode()).hexdigest(),
                    }
                )
        runs.append((config, records))
    return runs


def test_all_seeds_preserved_with_directional_changes():
    runs = fixtures()
    runs[1][1][1]["prediction"] = 0
    report = analyze_runs(runs[::-1])
    assert report["seeds"] == [0, 1, 2]
    assert report["distinct_original_test_cases"] == 381
    rates = report["seed_variation"]["edits"]["neutral_comment"]
    assert rates["harmful_rate_all_pairs"]["mean"] == pytest.approx(1 / 1020)
    assert rates["harmful_rate_all_pairs"]["sample_std"] > 0
    assert rates["corrective_rate_all_pairs"]["mean"] == 0


def test_no_visible_changes_produce_undefined_visible_rate():
    report = analyze_runs(fixtures(visible=False))
    assert report["seed_variation"]["edits"]["safe_claim"]["flip_rate_visible_pairs"] is None


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate_seed",
        "preflight",
        "environment",
        "implementation",
        "source",
        "hash_missing",
        "identity",
        "tokens",
    ],
)
def test_invalid_studies_rejected(fault):
    runs = fixtures()
    if fault == "missing":
        runs.pop()
    elif fault == "duplicate_seed":
        runs[2][0]["seed"] = 1
    elif fault == "preflight":
        runs[0][0]["status"] = "preflight_two_training_rows_not_research"
    elif fault == "environment":
        runs[1][0]["device"] = "cuda"
    elif fault == "implementation":
        runs[1][0]["implementation_sha256"] = "b" * 64
    elif fault == "source":
        runs[1][1][1]["source_sha256"] = "b" * 64
    elif fault == "hash_missing":
        del runs[1][1][1]["source_sha256"]
    elif fault == "identity":
        for row in runs[1][1]:
            row["id"] += "changed"
    else:
        runs[1][1][1]["token_input_changed"] = False
    with pytest.raises(ValueError):
        analyze_runs(runs)
