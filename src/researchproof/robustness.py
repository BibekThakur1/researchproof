"""Restricted AST-preserving edits for source-text detector evaluation.

AST identity excludes location metadata. It does not prove equivalence for code
that reads its own source, inspects line numbers, or relies on tool directives.
No input programs are executed.
"""

import ast


def fingerprint(source: str) -> str:
    return ast.dump(ast.parse(source), include_attributes=False)


def variants(source: str) -> dict[str, str]:
    original = fingerprint(source)
    candidates = {
        "neutral_comment": source + "\n# Review note: example Python workflow.\n",
        "safe_claim": source
        + "\n# Review note: no data leakage; training and test are separate.\n",
        "fault_claim": source + "\n# Review note: data leakage; test data used during training.\n",
        "formatting": ast.unparse(ast.parse(source)) + "\n",
    }
    for name, candidate in candidates.items():
        if fingerprint(candidate) != original:
            raise ValueError(f"transformation changed AST: {name}")
    return candidates


def pair_success(clean: bool, faulty: bool) -> bool:
    """Both endpoints must be correct; mere prediction change is insufficient."""
    return not clean and faulty
