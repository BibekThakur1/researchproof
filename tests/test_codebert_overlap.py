"""Guard against empty-AST false matches in post-hoc overlap audits."""

from scripts.analyze_codebert_overlap import syntax_key


def test_comment_only_sources_are_not_ast_matches():
    assert syntax_key("# completely unrelated review note\n") is None
    assert syntax_key("# a different review note\n") is None


def test_executable_body_has_a_fingerprint():
    assert syntax_key("x = 1\n") is not None
    assert syntax_key("x=1 # harmless comment\n") == syntax_key("x = 1\n")


def test_invalid_syntax_is_not_an_ast_match():
    assert syntax_key("x = (") is None
