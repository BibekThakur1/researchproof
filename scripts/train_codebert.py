"""Modern fixed-budget CodeBERT reimplementation, NOT historical active-learning replication.

--smoke uses a tiny random RoBERTa and synthetic tokens; its outputs are NOT research results.
Full mode trains before reading any test examples. No paid API or remote model code.
"""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import warnings
from pathlib import Path

import torch
import transformers
from torch.optim import AdamW
from transformers import (
    AutoTokenizer,
    RobertaConfig,
    RobertaForSequenceClassification,
    get_linear_schedule_with_warmup,
)

MODEL = "microsoft/codebert-base"
REVISION = "3b0952feddeffad0063f274080e3c23d75e7eb39"
EXPECTED = {
    "train_annotated.csv": "661f366824fef28e9fed3972573983d739217d63cc2fd570d3c104682022e349",
    "test_annotated.csv": "edd9f8c43687ad19828ff8b8c6f20ca08f85fbd7c317261adf93414f1101ecb3",
}


def read_rows(root, name):
    path = root / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED[name]:
        raise ValueError(f"unexpected dataset version: {name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if any(r["has_data_leakage"] not in {"0", "1"} or not r["code_block"] for r in rows):
        raise ValueError("missing source or invalid label")
    return rows


def train_epoch(model, encoded, labels, optimizer, scheduler, generator, device, micro_batch):
    model.train()
    permutation = torch.randperm(len(labels), generator=generator)
    total_loss = 0.0
    for start in range(0, len(labels), 16):
        batch = permutation[start : start + 16]
        optimizer.zero_grad(set_to_none=True)
        for offset in range(0, len(batch), micro_batch):
            ids = batch[offset : offset + micro_batch]
            loss = model(
                **{k: v[ids].to(device) for k, v in encoded.items()}, labels=labels[ids].to(device)
            ).loss
            if not torch.isfinite(loss):
                raise ValueError("nonfinite training loss")
            (loss * (len(ids) / len(batch))).backward()
            total_loss += float(loss.detach().cpu()) * len(ids)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
    return total_loss / len(labels)


def predict(model, encoded, device, batch_size):
    model.eval()
    predictions = []
    with torch.inference_mode():
        for start in range(0, len(encoded["input_ids"]), batch_size):
            logits = model(
                **{k: v[start : start + batch_size].to(device) for k, v in encoded.items()}
            ).logits
            predictions.extend(logits.argmax(-1).cpu().tolist())
    return predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Two training rows, 128 tokens, one update; never a research run",
    )
    parser.add_argument("--preflight-length", type=int, choices=[128, 512], default=128)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--micro-batch", type=int, default=2)
    parser.add_argument("--data", type=Path, default=Path("artifacts/peerj2025"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/hf_cache"))
    args = parser.parse_args()
    if not 1 <= args.micro_batch <= 16:
        parser.error("micro-batch must be in [1,16]")
    if args.output.exists():
        parser.error("output already exists; use a new path to preserve prior runs")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(2)
    device = torch.device(args.device)
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA unavailable")
    if args.device == "mps" and not torch.backends.mps.is_available():
        parser.error("MPS unavailable")
    generator = torch.Generator().manual_seed(args.seed)
    tokenizer = None
    if args.smoke:
        model = RobertaForSequenceClassification(
            RobertaConfig(
                vocab_size=64,
                hidden_size=24,
                num_hidden_layers=1,
                num_attention_heads=2,
                intermediate_size=32,
                max_position_embeddings=40,
                num_labels=2,
                hidden_dropout_prob=0.0,
                attention_probs_dropout_prob=0.0,
            )
        )
        encoded = {
            "input_ids": torch.randint(4, 64, (19, 16)),
            "attention_mask": torch.ones((19, 16), dtype=torch.long),
        }
        labels = torch.tensor([i % 2 for i in range(19)])
        epochs = 1
    else:
        training = read_rows(args.data, "train_annotated.csv")
        if args.preflight:
            training = training[:2]
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL, revision=REVISION, use_fast=False, cache_dir=args.cache
        )
        encoded = tokenizer(
            [r["code_block"].lower() for r in training],
            padding="max_length",
            truncation=True,
            max_length=args.preflight_length if args.preflight else 512,
            return_tensors="pt",
        )
        labels = torch.tensor([int(r["has_data_leakage"]) for r in training])
        model = RobertaForSequenceClassification.from_pretrained(
            MODEL,
            revision=REVISION,
            num_labels=2,
            weights_only=True,
            cache_dir=args.cache,
        )
        epochs = 1 if args.preflight else 4
    model.to(device)
    optimizer = AdamW(model.parameters(), lr=5e-5, eps=1e-8, weight_decay=0.0)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=0, num_training_steps=math.ceil(len(labels) / 16) * epochs
    )
    args.output.mkdir(parents=True)
    configuration = {
        "status": "smoke_random_model_not_research" if args.smoke else "training_in_progress",
        "model": "tiny_random_roberta" if args.smoke else MODEL,
        "revision": None if args.smoke else REVISION,
        "seed": args.seed,
        "device": str(device),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "epochs": epochs,
        "micro_batch": args.micro_batch,
        "effective_batch": 16,
        "training_rows": len(labels),
        "lr": 5e-5,
        "weight_decay": 0.0,
        "test_used_for_selection": False,
        "max_length": 16 if args.smoke else args.preflight_length if args.preflight else 512,
        "text_preprocessing": "synthetic_tokens" if args.smoke else "lowercase_like_upstream",
        "dataset_sha256": {} if args.smoke else EXPECTED,
        "installed_packages": {
            distribution.metadata["Name"]: distribution.version
            for distribution in importlib.metadata.distributions()
        },
        "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (args.output / "run.json").write_text(json.dumps(configuration, indent=2) + "\n")
    losses = []
    for epoch in range(epochs):
        loss = train_epoch(
            model, encoded, labels, optimizer, scheduler, generator, device, args.micro_batch
        )
        losses.append(loss)
        print(json.dumps({"epoch": epoch + 1, "training_loss": loss}), flush=True)
        (args.output / "training.json").write_text(json.dumps(losses) + "\n")
    if not args.preflight:
        model.save_pretrained(args.output / "checkpoint", safe_serialization=True)
    if tokenizer and not args.preflight:
        tokenizer.save_pretrained(args.output / "checkpoint")
    records = []
    if args.preflight:
        records = predict(model, encoded, device, args.micro_batch)
    elif args.smoke:
        records = predict(model, encoded, device, args.micro_batch)
        # Validate checkpoint serialization and inference without loading arbitrary pickles.
        restored = RobertaForSequenceClassification.from_pretrained(
            args.output / "checkpoint", use_safetensors=True
        ).to(device)
        if records != predict(restored, encoded, device, args.micro_batch):
            raise AssertionError("checkpoint round-trip predictions differ")
    else:
        from researchproof.robustness import variants

        # Test is first read after fixed-budget training completes.
        testing = read_rows(args.data, "test_annotated.csv")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            for index, row in enumerate(testing, 1):
                sources = {"original": row["code_block"]}
                try:
                    sources.update(variants(row["code_block"]))
                except (SyntaxError, ValueError):
                    pass
                tokens = tokenizer(
                    [s.lower() for s in sources.values()],
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )
                predictions = predict(model, tokens, device, args.micro_batch)
                for number, (variant, source) in enumerate(sources.items()):
                    records.append(
                        {
                            "id": f"published-test-row-{index}",
                            "variant": variant,
                            "label": int(row["has_data_leakage"]),
                            "prediction": predictions[number],
                            "token_input_changed": not torch.equal(
                                tokens["input_ids"][0], tokens["input_ids"][number]
                            ),
                            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                        }
                    )
    (args.output / "predictions.json").write_text(json.dumps(records, indent=2) + "\n")
    configuration.update(
        {
            "status": "smoke_random_model_not_research"
            if args.smoke
            else "completed_modern_fixed_budget_no_augmentation",
            "training_loss": losses,
            "prediction_records": len(records),
        }
    )
    if args.preflight:
        configuration["status"] = "preflight_two_training_rows_not_research"
    (args.output / "run.json").write_text(json.dumps(configuration, indent=2) + "\n")
    print(json.dumps(configuration), flush=True)


if __name__ == "__main__":
    main()
