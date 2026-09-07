from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from researchproof.audit import runtime_lineage_rules, static_sequence_rules
from researchproof.benchmark import FaultFamily, FaultSeverity, run_benchmark_case


@dataclass(frozen=True)
class RepairVerification:
    dataset_id: str
    fault_family: str
    fault_severity: str
    seed: int
    original_case_id: str
    repaired_case_id: str
    same_pair_id: bool
    same_base_split: bool
    original_static_fault: bool
    repaired_static_fault: bool
    original_runtime_fault: bool
    repaired_runtime_fault: bool
    accuracy_delta: float
    balanced_accuracy_delta: float
    roc_auc_delta: float
    repair_verified: bool


def verify_repair(
    fault_family: FaultFamily | str,
    seed: int,
    *,
    dataset_id: str = "sklearn_breast_cancer",
    severity: FaultSeverity | str = FaultSeverity.MEDIUM,
) -> RepairVerification:
    family = FaultFamily(fault_family)
    severity_level = FaultSeverity(severity)
    _, original = run_benchmark_case(
        family, "faulty", seed, dataset_id=dataset_id, severity=severity_level
    )
    _, repaired = run_benchmark_case(
        family, "clean", seed, dataset_id=dataset_id, severity=severity_level
    )
    original_payload = original.to_dict()
    repaired_payload = repaired.to_dict()
    original_static = static_sequence_rules(original_payload).predicted_fault
    repaired_static = static_sequence_rules(repaired_payload).predicted_fault
    original_runtime = runtime_lineage_rules(original_payload).predicted_fault
    repaired_runtime = runtime_lineage_rules(repaired_payload).predicted_fault
    same_pair = original.pair_id == repaired.pair_id
    same_split = (
        original.base_train_hash == repaired.base_train_hash
        and original.base_test_hash == repaired.base_test_hash
    )
    verified = (
        same_pair
        and same_split
        and original_static
        and original_runtime
        and not repaired_static
        and not repaired_runtime
    )
    return RepairVerification(
        dataset_id=dataset_id,
        fault_family=family.value,
        fault_severity=severity_level.value,
        seed=seed,
        original_case_id=original.case_id,
        repaired_case_id=repaired.case_id,
        same_pair_id=same_pair,
        same_base_split=same_split,
        original_static_fault=original_static,
        repaired_static_fault=repaired_static,
        original_runtime_fault=original_runtime,
        repaired_runtime_fault=repaired_runtime,
        accuracy_delta=repaired.accuracy - original.accuracy,
        balanced_accuracy_delta=repaired.balanced_accuracy - original.balanced_accuracy,
        roc_auc_delta=repaired.roc_auc - original.roc_auc,
        repair_verified=verified,
    )


def verify_repair_suite(
    dataset_ids: list[str],
    seeds: list[int],
    destination: Path,
    *,
    severities: list[str] | None = None,
    fault_families: list[str] | None = None,
) -> Path:
    records: list[dict[str, Any]] = []
    severity_levels = [FaultSeverity(value) for value in (severities or ["medium"])]
    selected_families = [
        FaultFamily(value)
        for value in (fault_families or [family.value for family in FaultFamily])
    ]
    for dataset_id in dataset_ids:
        for seed in seeds:
            for family in selected_families:
                for severity in severity_levels:
                    records.append(
                        asdict(
                            verify_repair(
                                family,
                                seed,
                                dataset_id=dataset_id,
                                severity=severity,
                            )
                        )
                    )
    payload = {
        "status": "engineering_verification_not_a_research_finding",
        "repairs": records,
        "summary": {
            "attempted": len(records),
            "verified": sum(record["repair_verified"] for record in records),
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
