import json

from researchproof.release import assess_release_readiness


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_release_refuses_single_author_and_missing_human_evidence(tmp_path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "benchmark_card.md").write_text("card", encoding="utf-8")
    (docs / "related_work.md").write_text("work", encoding="utf-8")
    benchmark = tmp_path / "benchmark.jsonl"
    sources = tmp_path / "sources.jsonl"
    write_jsonl(benchmark, [{"case_id": str(index)} for index in range(270)])
    write_jsonl(
        sources,
        [{"source_case_id": str(index), "author_id": "one"} for index in range(36)],
    )
    report = assess_release_readiness(tmp_path, benchmark, sources, None, None)
    assert report["status"] == "not_ready"
    failed = {gate["name"] for gate in report["gates"] if not gate["passed"]}
    assert "independent_source_authors" in failed
    assert "two_reviewer_agreement" in failed
    assert "independent_machine_reproduction" in failed


def test_release_passes_only_with_complete_external_evidence(tmp_path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "benchmark_card.md").write_text("card", encoding="utf-8")
    (docs / "related_work.md").write_text("work", encoding="utf-8")
    benchmark = tmp_path / "benchmark.jsonl"
    sources = tmp_path / "sources.jsonl"
    agreement = tmp_path / "agreement.json"
    reproduction = tmp_path / "reproduction.json"
    write_jsonl(benchmark, [{"case_id": str(index)} for index in range(270)])
    write_jsonl(
        sources,
        [
            {"source_case_id": str(index), "author_id": "a" if index < 18 else "b"}
            for index in range(36)
        ],
    )
    agreement.write_text(json.dumps({"cases": 36, "raw_agreement": 0.94}), encoding="utf-8")
    reproduction.write_text(
        json.dumps({"reproduced": True, "independent_machine": True}), encoding="utf-8"
    )
    report = assess_release_readiness(
        tmp_path, benchmark, sources, agreement, reproduction
    )
    assert report["status"] == "ready"
    assert all(gate["passed"] for gate in report["gates"])

