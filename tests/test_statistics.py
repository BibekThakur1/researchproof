import json

import pytest

from researchproof.statistics import bootstrap_mean_interval, paired_differences


def run(pair, variant, score, family="example"):
    return {
        "pair_id": pair,
        "variant": variant,
        "fault_family": family,
        "base_train_hash": f"train-{pair}",
        "base_test_hash": f"test-{pair}",
        "accuracy": score,
    }


def test_paired_difference_uses_faulty_minus_clean() -> None:
    runs = [run("a", "clean", 0.7), run("a", "faulty", 0.9)]
    differences = paired_differences(runs, "accuracy")
    assert differences[0][2] == pytest.approx(0.2)


def test_incomplete_pair_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        paired_differences([run("a", "faulty", 0.9)], "accuracy")


def test_bootstrap_summary_is_deterministic() -> None:
    first = bootstrap_mean_interval([0.1, 0.2, 0.3], samples=500, seed=7)
    second = bootstrap_mean_interval([0.1, 0.2, 0.3], samples=500, seed=7)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["pairs"] == 3

