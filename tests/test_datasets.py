import pytest

from researchproof.datasets import available_datasets, load_dataset


@pytest.mark.parametrize("dataset_id", available_datasets())
def test_registered_datasets_have_aligned_rows(dataset_id: str) -> None:
    dataset = load_dataset(dataset_id)
    assert len(dataset.features) == len(dataset.target) == len(dataset.row_ids)
    assert dataset.features.ndim == 2
    assert len(set(dataset.row_ids.tolist())) == len(dataset.row_ids)


def test_unknown_dataset_has_actionable_error() -> None:
    with pytest.raises(ValueError, match="unknown dataset"):
        load_dataset("missing_dataset")
