from __future__ import annotations

import ast
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

from researchproof.audit import classification_metrics


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return "dynamic_call"


def extract_ast_features(source: str) -> dict[str, float]:
    tree = ast.parse(source)
    calls = [_call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    features: dict[str, float] = {}
    for call in calls:
        features[f"call={call}"] = features.get(f"call={call}", 0.0) + 1.0
    for left, right in zip(calls, calls[1:]):
        features[f"call_pair={left}->{right}"] = 1.0
    features["assignment_count"] = float(
        sum(isinstance(node, ast.Assign) for node in ast.walk(tree))
    )
    features["subscript_count"] = float(
        sum(isinstance(node, ast.Subscript) for node in ast.walk(tree))
    )
    return features


def leave_one_group_out(cases: list[dict[str, Any]], group_field: str) -> dict[str, Any]:
    folds: list[dict[str, Any]] = []
    labels_all: list[bool] = []
    predictions_all: list[bool] = []
    for held_out in sorted({case[group_field] for case in cases}):
        train = [case for case in cases if case[group_field] != held_out]
        test = [case for case in cases if case[group_field] == held_out]
        vectorizer = DictVectorizer()
        x_train = vectorizer.fit_transform([extract_ast_features(case["source"]) for case in train])
        x_test = vectorizer.transform([extract_ast_features(case["source"]) for case in test])
        y_train = np.asarray([case["variant"] == "faulty" for case in train], dtype=int)
        labels = [case["variant"] == "faulty" for case in test]
        model = LogisticRegression(max_iter=1000, random_state=0).fit(x_train, y_train)
        predictions = model.predict(x_test).astype(bool).tolist()
        folds.append(
            {
                "held_out_group": held_out,
                "metrics": asdict(classification_metrics(labels, predictions)),
            }
        )
        labels_all.extend(labels)
        predictions_all.extend(predictions)
    return {
        "protocol": f"leave_one_complete_{group_field}_out",
        "aggregate_metrics": asdict(classification_metrics(labels_all, predictions_all)),
        "folds": folds,
    }


def evaluate_ast_baseline(index: Path, destination: Path) -> Path:
    cases = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
    payload = {
        "status": "small_source_pilot_not_a_research_finding",
        "warning": "Templates are authored by one implementation and are not externally validated.",
        "evaluations": {
            "held_out_style": leave_one_group_out(cases, "style_id"),
            "held_out_structural_template": leave_one_group_out(cases, "template_family"),
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
