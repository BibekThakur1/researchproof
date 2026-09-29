import copy
import runpy
from pathlib import Path

import pytest
import torch
from transformers import RobertaConfig, RobertaForSequenceClassification

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/train_codebert.py"))


@pytest.mark.parametrize("micro_batch", [1, 2, 7])
def test_accumulation_matches_full_logical_batch_including_short_final_batch(micro_batch):
    torch.manual_seed(0)
    torch.set_num_threads(2)
    model = RobertaForSequenceClassification(
        RobertaConfig(
            vocab_size=32,
            hidden_size=12,
            num_hidden_layers=1,
            num_attention_heads=2,
            intermediate_size=16,
            max_position_embeddings=24,
            num_labels=2,
            hidden_dropout_prob=0.0,
            attention_probs_dropout_prob=0.0,
        )
    )
    other = copy.deepcopy(model)
    encoded = {
        "input_ids": torch.randint(4, 32, (19, 8)),
        "attention_mask": torch.ones((19, 8), dtype=torch.long),
    }
    labels = torch.tensor([i % 2 for i in range(19)])
    losses = []
    for current, size in ((model, 16), (other, micro_batch)):
        optimizer = torch.optim.SGD(current.parameters(), lr=0.03)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1)
        losses.append(
            MODULE["train_epoch"](
                current,
                encoded,
                labels,
                optimizer,
                scheduler,
                torch.Generator().manual_seed(3),
                torch.device("cpu"),
                size,
            )
        )
        assert scheduler.last_epoch == 2  # two logical batches, not micro-batch count
    assert losses[0] == pytest.approx(losses[1], abs=1e-6)
    for a, b in zip(model.parameters(), other.parameters(), strict=True):
        torch.testing.assert_close(a, b, rtol=1e-5, atol=1e-7)


def test_bad_dataset_fingerprint_rejected(tmp_path):
    (tmp_path / "train_annotated.csv").write_text("changed\n")
    with pytest.raises(ValueError, match="unexpected dataset version"):
        MODULE["read_rows"](tmp_path, "train_annotated.csv")
