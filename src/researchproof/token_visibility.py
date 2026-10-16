"""Visibility of edits under right truncation; no detector-performance claims."""


def compare_tokens(original, edited, max_length, special_tokens=2):
    if max_length <= special_tokens or special_tokens < 0:
        raise ValueError("token budget must exceed special-token count")
    capacity = max_length - special_tokens
    raw_changed = original != edited
    visible_changed = original[:capacity] != edited[:capacity]
    return {
        "raw_tokens_changed": raw_changed,
        "visible_tokens_changed": visible_changed,
        "change_erased_by_truncation": raw_changed and not visible_changed,
        "original_truncated": len(original) > capacity,
        "edited_truncated": len(edited) > capacity,
    }
