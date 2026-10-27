# CodeBERT robustness study: completed Kaggle run

## Status and protocol

Private Kaggle notebook [version 5](https://www.kaggle.com/code/bibekthakur1/researchproof-codebert-20261020) completed on 27 October 2026 using a Tesla T4. Versions 1–4 failed before training and were not hidden or selected away. The frozen protocol trained a CodeBERT classifier for four epochs on 1,523 published training snippets at 512 tokens, effective batch 16, microbatch 2, with seeds 0, 1 and 2. The 381-snippet published test split contains 25 positive and 356 negative cases. Each seed was evaluated on original snippets and four edits of 340 parseable cases. This is a modern fixed-budget implementation, not a reproduction of the original paper's training protocol.

The compact [evidence archive](codebert_evidence.zip) contains configurations, loss histories, per-example predictions, source hashes, environment metadata, logs and analysis; it excludes model checkpoints and raw third-party data. Its SHA-256 is `1315ac01c9e27021f590b8d47dac5e69d970f6caef0918bed21978bc068eafbe`. The inspector verified 19 archive members, matched the frozen source manifest, checked all three complete seeds and independently recomputed the result tables. Checkpoints remain in the private Kaggle saved version.

## Observations

| Seed | TP | TN | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 17 | 353 | 3 | 8 | 0.850 | 0.680 | 0.756 |
| 1 | 15 | 353 | 3 | 10 | 0.833 | 0.600 | 0.698 |
| 2 | 17 | 351 | 5 | 8 | 0.773 | 0.680 | 0.723 |

Mean F1 is 0.726; seed sample SD is 0.029. This SD reflects optimization variation on the **same** cases, not uncertainty on new repositories. The high class imbalance makes accuracy alone misleading.

The four edits produced few prediction changes. Across seeds, mean all-pair flip rates were 0.39% for a neutral comment, 1.67% for a misleading “safe” comment, 1.08% for a misleading “fault” comment, and 0.98% for formatting. These are descriptive means of per-seed rates, not independent 1,020-case estimates. Some flips corrected an original error; [the full table](codebert_tables.md) separates harmful from corrective flips. At 512 tokens, 9/340 appended comments were invisible after truncation, so an unchanged prediction on those cases cannot be credited to model robustness. Six formatting edits were token-equivalent. The study tests these exact edits, not semantic invariance generally.

The previously trained word and character TF-IDF pilots reported F1 0.500 and 0.551 on this published split. Their protocols differ from the CodeBERT run, so this is context, not a controlled superiority result. The present CodeBERT run does not establish a novel detector, invention, patent claim, or publication readiness.

## Limitations and next research gates

The test split was explored before this run. There is no frozen independent confirmation corpus or repository/author-level holdout. Human review packets currently have 0/20 judgments from each of two reviewers, so edit-label validity and inter-rater agreement are unestablished. The source data is narrow and imbalanced; 25 positives make recall sensitive to a few decisions. The observed flip rates are small and may not justify a stand-alone robustness claim. A different research contribution may be needed after a thorough closest-work review.

Before submission: (1) finish blinded independent review and adjudicate disagreements; (2) freeze a separate confirmation corpus and evaluate without tuning against it; (3) compare credible baselines under matched splits/budgets; (4) inspect individual errors and edits for semantic validity; (5) independently rerun the pipeline on a clean environment; (6) conduct a full-paper novelty review and select a venue only after the contribution survives these checks. Report negative findings as well as positive ones.

## Reproduction of evidence validation

From this repository, run `PYTHONPATH=src .venv/bin/python scripts/inspect_codebert_results.py results/2026-10-27/codebert_evidence.zip --source-manifest artifacts/kaggle_ready_2026-10-20/source_hashes.json --output artifacts/recheck_2026-10-27` if the frozen local manifest is available. The archive itself includes the source hash manifest for independent inspection. `codebert_analysis.json` and `codebert_tables.md` are derived files, not additional training runs.
