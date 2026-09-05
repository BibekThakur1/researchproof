from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from researchproof.audit import classification_metrics


@dataclass(frozen=True)
class StaticFinding:
    kind: str
    line: int
    explanation: str


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return _name(node.value)
    return None


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _assigned_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        result: list[str] = []
        for item in target.elts:
            result.extend(_assigned_names(item))
        return result
    return []


def _provenance(node: ast.AST, values: dict[str, set[str]]) -> set[str]:
    symbol = _name(node)
    if symbol is not None:
        return set(values.get(symbol, {"unsplit_value"}))
    if isinstance(node, (ast.List, ast.Tuple)):
        result: set[str] = set()
        for item in node.elts:
            result.update(_provenance(item, values))
        return result
    if isinstance(node, ast.Call) and _call_name(node) == "concatenate" and node.args:
        return _provenance(node.args[0], values)
    return set()


def analyze_source(source: str) -> list[StaticFinding]:
    tree = ast.parse(source)
    values: dict[str, set[str]] = {}
    findings: list[StaticFinding] = []
    evaluation_seen = False

    def record(kind: str, node: ast.AST, explanation: str) -> None:
        finding = StaticFinding(kind=kind, line=getattr(node, "lineno", 0), explanation=explanation)
        if finding not in findings:
            findings.append(finding)

    for statement in tree.body:
        value = statement.value if isinstance(statement, (ast.Assign, ast.Expr)) else None
        call = value if isinstance(value, ast.Call) else None

        if isinstance(statement, ast.Assign) and call and _call_name(call) == "train_test_split":
            outputs = _assigned_names(statement.targets[0])
            if len(outputs) >= 4 and len(call.args) >= 2:
                feature_source = _provenance(call.args[0], values)
                target_source = _provenance(call.args[1], values)
                values[outputs[0]] = {"train_features"} | feature_source
                values[outputs[1]] = {"test_features"} | feature_source
                values[outputs[2]] = {"train_target"} | target_source
                values[outputs[3]] = {"test_target"} | target_source
            continue

        if isinstance(statement, ast.Assign) and call and _call_name(call) == "fit_transform":
            output_names = _assigned_names(statement.targets[0])
            input_provenance = _provenance(call.args[0], values) if call.args else set()
            tags = set(input_provenance)
            if "train_features" not in input_provenance:
                tags.add("preprocessed_before_split")
                if len(call.args) >= 2:
                    tags.add("target_selected_before_split")
            for output in output_names:
                values[output] = tags
            continue

        if isinstance(statement, ast.Assign) and call and _call_name(call) == "concatenate":
            combined = _provenance(call, values)
            for output in _assigned_names(statement.targets[0]):
                values[output] = combined
            continue

        if isinstance(statement, ast.Assign) and isinstance(value, ast.Name):
            for output in _assigned_names(statement.targets[0]):
                values[output] = _provenance(value, values)

        if call and _call_name(call) == "score":
            evaluation_seen = True
            continue

        if call and _call_name(call) == "fit" and call.args and not evaluation_seen:
            fitted = _provenance(call.args[0], values)
            if "test_features" in fitted:
                record(
                    "test_data_reaches_model_fit",
                    call,
                    "A value derived from held-out features reaches model fitting.",
                )
            if "target_selected_before_split" in fitted:
                record(
                    "supervised_selection_before_split",
                    call,
                    "Features selected using unsplit targets reach model fitting.",
                )
            elif "preprocessed_before_split" in fitted:
                record(
                    "preprocessing_before_split",
                    call,
                    "A transformation fitted on unsplit features reaches model fitting.",
                )
    return findings


def evaluate_symbolic_analyzer(index: Path, destination: Path) -> Path:
    cases = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
    labels = [case["variant"] == "faulty" for case in cases]
    predictions = [bool(analyze_source(case["source"])) for case in cases]
    payload: dict[str, Any] = {
        "status": "small_source_pilot_not_a_research_finding",
        "analyzer": "symbolic_provenance_v0_1",
        "metrics": asdict(classification_metrics(labels, predictions)),
        "failures": [
            {
                "source_case_id": case["source_case_id"],
                "expected_fault": label,
                "predicted_fault": prediction,
            }
            for case, label, prediction in zip(cases, labels, predictions, strict=True)
            if label != prediction
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination

