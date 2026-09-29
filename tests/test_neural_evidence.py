import pytest

from researchproof.neural_evidence import EXPECTED_PROTOCOL, summarize


def completed_fixture():
    """Synthetic validator fixture only, never experimental evidence."""
    run = {
        **EXPECTED_PROTOCOL,
        "status": "completed_modern_fixed_budget_no_augmentation",
        "training_rows": 1523,
        "epochs": 4,
        "test_used_for_selection": False,
        "prediction_records": 1741,
    }
    records = []
    for i in range(381):
        variants = ["original"]
        if i < 340:
            variants += ["neutral_comment", "safe_claim", "fault_claim", "formatting"]
        for variant in variants:
            records.append(
                {
                    "id": str(i),
                    "variant": variant,
                    "label": int(i < 25),
                    "prediction": int(i < 25),
                    "token_input_changed": variant != "original",
                }
            )
    return run, records


def test_complete_fixture_and_directional_flips():
    run, records = completed_fixture()
    records[1]["prediction"] = 0
    summary = summarize(run, records)
    assert summary["edits"]["neutral_comment"]["correct_to_wrong"] == 1
    assert summary["edits"]["neutral_comment"]["wrong_to_correct"] == 0
    assert summary["edits"]["neutral_comment"]["paired"] == 340


@pytest.mark.parametrize(
    "corruption", ["duplicate", "label", "token", "unchanged", "missing", "version"]
)
def test_corrupted_evidence_is_rejected(corruption):
    run, records = completed_fixture()
    if corruption == "duplicate":
        records[1] = dict(records[0])
    elif corruption == "label":
        records[0]["label"] = 2
    elif corruption == "token":
        records[1]["token_input_changed"] = "true"
    elif corruption == "unchanged":
        records[1]["token_input_changed"] = False
        records[1]["prediction"] = 0
    elif corruption == "missing":
        records.pop()
    else:
        run["revision"] = "unknown"
    with pytest.raises(ValueError):
        summarize(run, records)


@pytest.mark.parametrize(
    "status",
    [
        "training_in_progress",
        "smoke_random_model_not_research",
        "preflight_two_training_rows_not_research",
    ],
)
def test_unfinished_and_smoke_evidence_cannot_make_research_tables(status):
    with pytest.raises(ValueError, match="completed full"):
        summarize({"status": status}, [])


def test_full_run_requires_original_dataset_and_protocol():
    with pytest.raises(ValueError, match="training protocol"):
        summarize(
            {
                "status": "completed_modern_fixed_budget_no_augmentation",
                "training_rows": 2,
                "epochs": 1,
            },
            [],
        )


def test_test_selection_flag_is_rejected():
    with pytest.raises(ValueError, match="test-based selection"):
        summarize(
            {
                "status": "completed_modern_fixed_budget_no_augmentation",
                "training_rows": 1523,
                "epochs": 4,
                "test_used_for_selection": True,
            },
            [],
        )
