import json

import pytest

from researchproof.benchmark import FaultFamily
from researchproof.repair import verify_repair, verify_repair_suite


@pytest.mark.parametrize("family", list(FaultFamily))
def test_repairs_remove_engineered_fault_and_preserve_split(family: FaultFamily) -> None:
    verification = verify_repair(family, seed=7)
    assert verification.same_pair_id is True
    assert verification.same_base_split is True
    assert verification.original_static_fault is True
    assert verification.original_runtime_fault is True
    assert verification.repaired_static_fault is False
    assert verification.repaired_runtime_fault is False
    assert verification.repair_verified is True


def test_repair_suite_writes_summary(tmp_path) -> None:
    destination = verify_repair_suite(
        ["sklearn_breast_cancer"],
        [7, 19],
        tmp_path / "repairs.json",
    )
    report = json.loads(destination.read_text(encoding="utf-8"))
    assert report["summary"] == {"attempted": 8, "verified": 8}
    assert len(report["repairs"]) == 8
