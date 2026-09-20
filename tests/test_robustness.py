import pytest

from researchproof.robustness import fingerprint, pair_success, variants


@pytest.mark.parametrize(
    "source",
    [
        "x = 1",
        "x = '# not a comment'\n",
        "def f(x):\n    return x + 1\n",
        "a = [x for x in range(3)]\n",
        "# leading comment\nx=1 # trailing comment",
        "x = 'नेपाली'",
        "from __future__ import annotations\nx: int = 1",
        "x = '''multiple\nlines'''\n",
        "x = 1 + \\\n+2\n",
    ],
)
def test_every_edit_preserves_ast(source):
    for candidate in variants(source).values():
        assert fingerprint(candidate) == fingerprint(source)


def test_invalid_source_not_silently_changed():
    with pytest.raises(SyntaxError):
        variants("def broken(")


@pytest.mark.parametrize(
    "clean,faulty,expected",
    [
        (False, True, True),
        (True, False, False),
        (True, True, False),
        (False, False, False),
    ],
)
def test_pair_metric_rejects_constant_and_reversed_detectors(clean, faulty, expected):
    assert pair_success(clean, faulty) is expected
