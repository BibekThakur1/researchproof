from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReleaseGate:
    name: str
    passed: bool
    evidence: str


def _json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def assess_release_readiness(
    repository: Path,
    benchmark_index: Path,
    source_index: Path,
    agreement_report: Path | None,
    reproduction_report: Path | None,
) -> dict[str, Any]:
    benchmark = _jsonl(benchmark_index)
    sources = _jsonl(source_index)
    agreement = _json(agreement_report)
    reproduction = _json(reproduction_report)
    authors = sorted({case.get("author_id", "") for case in sources if case.get("author_id")})
    gates = [
        ReleaseGate(
            "minimum_executable_cases",
            len(benchmark) >= 270,
            f"found {len(benchmark)}; require at least 270",
        ),
        ReleaseGate(
            "minimum_source_cases",
            len(sources) >= 36,
            f"found {len(sources)}; require at least 36",
        ),
        ReleaseGate(
            "independent_source_authors",
            len(authors) >= 2,
            f"found {len(authors)} author IDs: {authors}",
        ),
        ReleaseGate(
            "two_reviewer_agreement",
            bool(agreement and agreement.get("cases", 0) == len(sources)),
            "agreement report must cover every source case",
        ),
        ReleaseGate(
            "agreement_threshold",
            bool(agreement and float(agreement.get("raw_agreement", 0.0)) >= 0.90),
            "raw agreement must be at least 0.90 before adjudication",
        ),
        ReleaseGate(
            "independent_machine_reproduction",
            bool(
                reproduction
                and reproduction.get("reproduced") is True
                and reproduction.get("independent_machine") is True
            ),
            "comparison must reproduce and be explicitly recorded as a second machine",
        ),
        ReleaseGate(
            "benchmark_card",
            (repository / "docs" / "benchmark_card.md").is_file(),
            "docs/benchmark_card.md",
        ),
        ReleaseGate(
            "closest_work_map",
            (repository / "docs" / "related_work.md").is_file(),
            "docs/related_work.md",
        ),
    ]
    return {
        "status": "ready" if all(gate.passed for gate in gates) else "not_ready",
        "gates": [asdict(gate) for gate in gates],
    }


def write_release_readiness(
    repository: Path,
    benchmark_index: Path,
    source_index: Path,
    agreement_report: Path | None,
    reproduction_report: Path | None,
    destination: Path,
) -> Path:
    report = assess_release_readiness(
        repository,
        benchmark_index,
        source_index,
        agreement_report,
        reproduction_report,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination

