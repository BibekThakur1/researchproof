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

## Additional case-level audit (27 October)

I re-read the three archived prediction files by original case ID. Of the 25
positive cases, **eight were false negatives in every seed** (`published-test-row-34`,
`49`, `60`, `207`, `272`, `273`, `370`, `371`); all other 17 positives were
identified by at least two seeds. Ten of 381 originals had seed disagreement,
including two positives. A two-of-three majority would yield TP 17, TN 353,
FP 3, FN 8. These are repeated decisions on the same cases, not independent
replications of the test population. Stable failure across random seeds is a
reason to examine those eight examples, **not** evidence of a shared causal
mechanism or invalid labels.

Across all four edits and three seeds, only 16 distinct original cases had any
prediction flip; eight were positive and eight negative. Seven of those 16 cases
flipped in more than one seed. The four-edit, any-seed grouping was examined
after seeing results and should not be presented as a preregistered statistical
test. The next manual review should examine the eight persistent misses and the
16 flip cases without showing reviewers model predictions first. The review
must check whether each edit truly preserves the leakage label and whether the
original dataset label is defensible.

## Train/test overlap sensitivity analysis

A checksum-verified reanalysis of the canonical published CSV files found six
exact text matches and 16 AST-fingerprint matches between training and test
snippets. The six exact matches are included within the 16 AST matches. After
removing all 16 overlapping test cases, 365 cases remain, including 23 positives.

| Seed | Full-split F1 | Nonoverlap F1 | Nonoverlap TP | Nonoverlap FN |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0.756 | 0.732 | 15 | 8 |
| 1 | 0.698 | 0.667 | 13 | 10 |
| 2 | 0.723 | 0.714 | 15 | 8 |

Thus the reported score is somewhat sensitive to train/test code overlap. The
eight cases missed by every seed are all in the nonoverlap subset. This is a
post-hoc sensitivity analysis, not a new independent test: AST equality does
not detect semantic near-duplicates, shared repository origins or label errors.
The [machine-readable analysis](codebert_overlap_analysis.json) is generated by
`scripts/analyze_codebert_overlap.py` after validating the archive and both
canonical dataset checksums. It does not expose raw third-party snippets.

## Closest-work check (27 October)

The [2025 PeerJ study](https://peerj.com/articles/cs-2730/) already trains
CodeBERT for leakage detection on this dataset; our trained classifier is a
baseline, not a novel model. A [2025 systematic review](https://arxiv.org/abs/2507.22610)
examines 45 primary studies of metamorphic testing for deep code models, so
testing model stability under code edits is established. The
[FSE 2026 paper](https://doi.org/10.1145/3808199) addresses leakage detection
with static slicing and LLM reasoning; its full text still needs comparison.
An [Information and Software Technology study](https://www.sciencedirect.com/science/article/abs/pii/S0950584926003253)
reports fine-grained manual annotation of 614 notebook pipelines and evaluates
three detection paradigms; availability, licensing, unit of analysis, and split
compatibility must be checked before treating its corpus as independent
confirmation data. This search does **not** establish that our narrow
exposure-aware, directional-flip audit is novel enough for publication.

## Limitations and next research gates

The test split was explored before this run. There is no frozen independent confirmation corpus or repository/author-level holdout. Human review packets currently have 0/20 judgments from each of two reviewers, so edit-label validity and inter-rater agreement are unestablished. The source data is narrow and imbalanced; 25 positives make recall sensitive to a few decisions. The observed flip rates are small and may not justify a stand-alone robustness claim. A different research contribution may be needed after a thorough closest-work review.

Before submission: (1) finish blinded independent review and adjudicate disagreements; (2) freeze a separate confirmation corpus and evaluate without tuning against it; (3) compare credible baselines under matched splits/budgets; (4) inspect individual errors and edits for semantic validity; (5) independently rerun the pipeline on a clean environment; (6) conduct a full-paper novelty review and select a venue only after the contribution survives these checks. Report negative findings as well as positive ones.

## Reproduction of evidence validation

From this repository, run `PYTHONPATH=src .venv/bin/python scripts/inspect_codebert_results.py results/2026-10-27/codebert_evidence.zip --source-manifest artifacts/kaggle_ready_2026-10-20/source_hashes.json --output artifacts/recheck_2026-10-27` if the frozen local manifest is available. The archive itself includes the source hash manifest for independent inspection. `codebert_analysis.json` and `codebert_tables.md` are derived files, not additional training runs.
