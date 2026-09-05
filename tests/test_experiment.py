from researchproof.experiment import run_variant


def test_clean_and_faulty_variants_use_identical_splits() -> None:
    clean = run_variant("clean", seed=7, test_size=0.25, max_iter=500)
    faulty = run_variant("faulty", seed=7, test_size=0.25, max_iter=500)

    assert clean.train_index_hash == faulty.train_index_hash
    assert clean.test_index_hash == faulty.test_index_hash
    assert clean.train_rows == faulty.train_rows
    assert clean.test_rows == faulty.test_rows


def test_metrics_are_valid_probabilities() -> None:
    result = run_variant("clean", seed=19, test_size=0.25, max_iter=500)
    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.balanced_accuracy <= 1.0
    assert 0.0 <= result.roc_auc <= 1.0

