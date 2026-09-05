import ast
import json

from researchproof.ast_baseline import evaluate_ast_baseline, extract_ast_features
from researchproof.benchmark import FaultFamily
from researchproof.source_benchmark import build_source_cases, write_source_benchmark


def test_source_pilot_has_three_blindable_styles() -> None:
    cases = build_source_cases()
    assert len(cases) == 36
    assert {case.style_id for case in cases} == {
        "descriptive",
        "compact",
        "notebook",
        "helper",
    }
    assert sum(case.variant == "clean" for case in cases) == 24
    assert sum(case.variant == "faulty" for case in cases) == 12


def test_source_pilot_contains_valid_hard_negatives() -> None:
    cases = build_source_cases()
    fault_names = {family.value for family in FaultFamily}
    hard_negatives = [case for case in cases if case.fault_family not in fault_names]
    assert len(hard_negatives) == 12
    assert all(case.variant == "clean" for case in hard_negatives)


def test_every_source_case_parses_as_python() -> None:
    for case in build_source_cases():
        ast.parse(case.source)


def test_ast_features_do_not_receive_gold_metadata() -> None:
    case = build_source_cases()[0]
    features = extract_ast_features(case.source)
    assert not any("variant" in key or "fault_family" in key for key in features)


def test_source_report_holds_out_complete_styles(tmp_path) -> None:
    index = write_source_benchmark(tmp_path / "cases.jsonl")
    report_path = evaluate_ast_baseline(index, tmp_path / "report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    folds = report["evaluations"]["held_out_style"]["folds"]
    assert {fold["held_out_group"] for fold in folds} == {
        "descriptive",
        "compact",
        "notebook",
        "helper",
    }
    structural = report["evaluations"]["held_out_structural_template"]["folds"]
    assert len(structural) == 6
