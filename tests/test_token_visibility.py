import pytest

from researchproof.token_visibility import compare_tokens


def test_tail_edit_disappears_at_capacity():
    result = compare_tokens([1, 2, 3], [1, 2, 3, 4], 5)
    assert result["change_erased_by_truncation"]
    assert not result["visible_tokens_changed"]
    assert not result["original_truncated"]
    assert result["edited_truncated"]


def test_visible_change_is_not_erased():
    result = compare_tokens([1, 2, 3], [1, 9, 3, 4], 5)
    assert result["visible_tokens_changed"]
    assert not result["change_erased_by_truncation"]


def test_identical_tokens_are_not_truncation_erasure():
    result = compare_tokens([1, 2, 3, 4], [1, 2, 3, 4], 5)
    assert result["original_truncated"]
    assert not result["raw_tokens_changed"]
    assert not result["change_erased_by_truncation"]


def test_shorter_visible_input_changes_attention_length():
    assert compare_tokens([1, 2, 3], [1, 2], 5)["visible_tokens_changed"]


def test_invalid_budget():
    with pytest.raises(ValueError):
        compare_tokens([], [], 2)
