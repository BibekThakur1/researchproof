from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from researchproof.benchmark import FaultFamily


@dataclass(frozen=True)
class SourceCase:
    source_case_id: str
    template_family: str
    fault_family: str
    variant: str
    source: str


_STYLES = {
    "descriptive": ("features", "labels", "x_train", "x_test", "y_train", "y_test"),
    "compact": ("a", "b", "tr_x", "te_x", "tr_y", "te_y"),
    "notebook": ("data", "target", "train_data", "test_data", "train_y", "test_y"),
}


def _split(names: tuple[str, ...]) -> str:
    x, y, x_train, x_test, y_train, y_test = names
    return (
        f"{x_train}, {x_test}, {y_train}, {y_test} = "
        f"train_test_split({x}, {y}, test_size=0.25, random_state=7, stratify={y})"
    )


def _source(family: FaultFamily, variant: str, names: tuple[str, ...]) -> str:
    x, y, x_train, x_test, y_train, y_test = names
    split = _split(names)
    if family is FaultFamily.PREPROCESSING_BEFORE_SPLIT:
        body = (
            [
                "scaler = StandardScaler()",
                f"{x} = scaler.fit_transform({x})",
                split,
            ]
            if variant == "faulty"
            else [
                split,
                "scaler = StandardScaler()",
                f"{x_train} = scaler.fit_transform({x_train})",
                f"{x_test} = scaler.transform({x_test})",
            ]
        )
    elif family is FaultFamily.TRAIN_TEST_OVERLAP:
        body = [split]
        if variant == "faulty":
            body.extend(
                [
                    f"{x_train} = np.concatenate([{x_train}, {x_test}[:10]])",
                    f"{y_train} = np.concatenate([{y_train}, {y_test}[:10]])",
                ]
            )
    else:
        body = (
            [
                "selector = SelectKBest(f_classif, k=10)",
                f"{x} = selector.fit_transform({x}, {y})",
                split,
            ]
            if variant == "faulty"
            else [
                split,
                "selector = SelectKBest(f_classif, k=10)",
                f"{x_train} = selector.fit_transform({x_train}, {y_train})",
                f"{x_test} = selector.transform({x_test})",
            ]
        )
    body.extend(
        [
            "model = LogisticRegression(max_iter=2000)",
            f"model.fit({x_train}, {y_train})",
            f"score = model.score({x_test}, {y_test})",
        ]
    )
    return "\n".join(body) + "\n"


def build_source_cases() -> list[SourceCase]:
    cases: list[SourceCase] = []
    for style, names in _STYLES.items():
        for family in FaultFamily:
            for variant in ("clean", "faulty"):
                source = _source(family, variant, names)
                material = f"{style}:{family.value}:{variant}:{source}"
                case_id = f"source-{hashlib.sha256(material.encode()).hexdigest()[:16]}"
                cases.append(
                    SourceCase(
                        source_case_id=case_id,
                        template_family=style,
                        fault_family=family.value,
                        variant=variant,
                        source=source,
                    )
                )
    return cases


def write_source_benchmark(destination: Path) -> Path:
    cases = build_source_cases()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(asdict(case), sort_keys=True) + "\n" for case in cases),
        encoding="utf-8",
    )
    return destination

