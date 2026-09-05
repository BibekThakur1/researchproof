import json

import pytest

from researchproof.contributions import (
    ContributionError,
    build_combined_source_index,
    load_contribution,
)


def write_contribution(root, **overrides):
    source = root / "example.py"
    source.write_text("model.fit(x_train, y_train)\n", encoding="utf-8")
    payload = {
        "author_id": "researcher_b",
        "style_id": "independent_style_1",
        "template_family": "independent_clean_fit",
        "fault_family": "valid_hard_negative",
        "variant": "clean",
        "source_file": "example.py",
        "license_statement": "I authored this example and permit research reuse.",
    }
    payload.update(overrides)
    metadata = root / "example.json"
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    return metadata


def test_external_contribution_is_content_addressed(tmp_path) -> None:
    metadata = write_contribution(tmp_path)
    first = load_contribution(metadata)
    second = load_contribution(metadata)
    assert first == second
    assert first.author_id == "researcher_b"


def test_combined_index_contains_second_author(tmp_path) -> None:
    write_contribution(tmp_path)
    destination = build_combined_source_index(tmp_path, tmp_path / "combined.jsonl")
    cases = [json.loads(line) for line in destination.read_text().splitlines()]
    assert {case["author_id"] for case in cases} == {
        "initial_repository_author",
        "researcher_b",
    }


def test_source_path_traversal_is_rejected(tmp_path) -> None:
    metadata = write_contribution(tmp_path, source_file="../outside.py")
    with pytest.raises(ContributionError, match="without directories"):
        load_contribution(metadata)


def test_unregistered_fault_label_is_rejected(tmp_path) -> None:
    metadata = write_contribution(
        tmp_path,
        variant="faulty",
        fault_family="invented_fault",
    )
    with pytest.raises(ContributionError, match="registered fault"):
        load_contribution(metadata)

