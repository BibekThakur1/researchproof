from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from researchproof.benchmark import FaultFamily


@dataclass(frozen=True)
class SourceCase:
    source_case_id: str
    author_id: str
    style_id: str
    template_family: str
    fault_family: str
    variant: str
    source: str


_STYLES = {
    "descriptive": ("features", "labels", "x_train", "x_test", "y_train", "y_test"),
    "compact": ("a", "b", "tr_x", "te_x", "tr_y", "te_y"),
    "notebook": ("data", "target", "train_data", "test_data", "train_y", "test_y"),
    "helper": ("matrix", "outcome", "fit_x", "holdout_x", "fit_y", "holdout_y"),
}


def _split(names: tuple[str, ...]) -> str:
    x, y, x_train, x_test, y_train, y_test = names
    return (
        f"{x_train}, {x_test}, {y_train}, {y_test} = "
        f"train_test_split({x}, {y}, test_size=0.25, random_state=7, stratify={y})"
    )


def _helper_source(family: FaultFamily, variant: str, names: tuple[str, ...]) -> str:
    x, y, x_train, x_test, y_train, y_test = names
    split = _split(names)
    if family is FaultFamily.PREPROCESSING_BEFORE_SPLIT:
        definition = "def prepare(values):\n    return StandardScaler().fit_transform(values)"
        body = (
            [definition, f"{x} = prepare({x})", split]
            if variant == "faulty"
            else [definition, split, f"{x_train} = prepare({x_train})"]
        )
    elif family is FaultFamily.TRAIN_TEST_OVERLAP:
        definition = (
            "def extend(values, held_out):\n"
            "    return np.concatenate([values, held_out[:10]])"
        )
        body = [definition, split]
        if variant == "faulty":
            body.extend(
                [
                    f"{x_train} = extend({x_train}, {x_test})",
                    f"{y_train} = extend({y_train}, {y_test})",
                ]
            )
    else:
        definition = (
            "def choose(values, outcomes):\n"
            "    selector = SelectKBest(f_classif, k=10)\n"
            "    return selector.fit_transform(values, outcomes)"
        )
        body = (
            [definition, f"{x} = choose({x}, {y})", split]
            if variant == "faulty"
            else [definition, split, f"{x_train} = choose({x_train}, {y_train})"]
        )
    body.extend(
        [
            "model = LogisticRegression(max_iter=2000)",
            f"model.fit({x_train}, {y_train})",
            f"score = model.score({x_test}, {y_test})",
        ]
    )
    return "\n".join(body) + "\n"


def _source(
    family: FaultFamily, variant: str, names: tuple[str, ...], style: str
) -> str:
    if style == "helper":
        return _helper_source(family, variant, names)
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


def _hard_negative_sources(names: tuple[str, ...]) -> dict[str, str]:
    x, y, x_train, x_test, y_train, y_test = names
    split = _split(names)
    return {
        "unused_full_data_diagnostic": "\n".join(
            [
                f"diagnostic_only = StandardScaler().fit_transform({x})",
                split,
                "pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))",
                f"pipeline.fit({x_train}, {y_train})",
                f"score = pipeline.score({x_test}, {y_test})",
            ]
        )
        + "\n",
        "post_evaluation_refit": "\n".join(
            [
                split,
                "pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))",
                f"pipeline.fit({x_train}, {y_train})",
                f"score = pipeline.score({x_test}, {y_test})",
                f"deployment_model = clone(pipeline).fit({x}, {y})",
            ]
        )
        + "\n",
        "pipeline_cross_validation": "\n".join(
            [
                "pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))",
                f"scores = cross_val_score(pipeline, {x}, {y}, cv=5)",
                "score = scores.mean()",
            ]
        )
        + "\n",
    }


def build_source_cases() -> list[SourceCase]:
    cases: list[SourceCase] = []
    for style, names in _STYLES.items():
        for family in FaultFamily:
            for variant in ("clean", "faulty"):
                source = _source(family, variant, names, style)
                material = f"{style}:{family.value}:{variant}:{source}"
                case_id = f"source-{hashlib.sha256(material.encode()).hexdigest()[:16]}"
                cases.append(
                    SourceCase(
                        source_case_id=case_id,
                        author_id="initial_repository_author",
                        style_id=style,
                        template_family=family.value,
                        fault_family=family.value,
                        variant=variant,
                        source=source,
                    )
                )
        for hard_negative, source in _hard_negative_sources(names).items():
            material = f"{style}:{hard_negative}:clean:{source}"
            case_id = f"source-{hashlib.sha256(material.encode()).hexdigest()[:16]}"
            cases.append(
                SourceCase(
                    source_case_id=case_id,
                    author_id="initial_repository_author",
                    style_id=style,
                    template_family=hard_negative,
                    fault_family=hard_negative,
                    variant="clean",
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


def read_source_benchmark(source: Path) -> list[SourceCase]:
    cases: list[SourceCase] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        try:
            payload = json.loads(line)
            cases.append(SourceCase(**payload))
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(f"invalid source case at line {line_number}: {error}") from error
    if not cases:
        raise ValueError("source benchmark is empty")
    return cases
