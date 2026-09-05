from researchproof.source_benchmark import build_source_cases
from researchproof.static_analysis import analyze_source


def test_symbolic_analyzer_detects_current_faulty_source_cases() -> None:
    faulty = [case for case in build_source_cases() if case.variant == "faulty"]
    assert faulty
    assert all(analyze_source(case.source) for case in faulty)


def test_symbolic_analyzer_accepts_current_clean_and_hard_negative_cases() -> None:
    clean = [case for case in build_source_cases() if case.variant == "clean"]
    assert clean
    assert all(analyze_source(case.source) == [] for case in clean)


def test_unused_full_data_transform_is_not_reported() -> None:
    source = """
diagnostic = StandardScaler().fit_transform(features)
x_train, x_test, y_train, y_test = train_test_split(features, labels)
model.fit(x_train, y_train)
score = model.score(x_test, y_test)
"""
    assert analyze_source(source) == []


def test_post_evaluation_refit_is_not_reported() -> None:
    source = """
x_train, x_test, y_train, y_test = train_test_split(features, labels)
model.fit(x_train, y_train)
score = model.score(x_test, y_test)
deployment_model.fit(features, labels)
"""
    assert analyze_source(source) == []

