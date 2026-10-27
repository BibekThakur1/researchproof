# Persistent-miss source audit (27 October 2026)

This is an **exploratory, AI-assisted code trace**, not a replacement for the
published labels or the two independent human reviews. The eight cases below
are positive in the published PeerJ test split and predicted negative by all
three archived CodeBERT seeds. The reproducible, code-free case table is
[`persistent_false_negative_audit.csv`](../results/2026-10-27/persistent_false_negative_audit.csv).

## Provenance method and limits

The [PeerJ study](https://doi.org/10.7717/peerj-cs.2730) states that its
1,904 snippets derive from Code4ML and explicitly notes the limitation of
isolated code blocks. [Code4ML 2.0](https://zenodo.org/records/12700065)
publishes notebook metadata with numeric `kernel_id` and a Kaggle URL.
A [third-party annotated derivative](https://huggingface.co/datasets/dimsmauls/code4ml-annotated-rated)
provides recovered `kernel_id` values for some Code4ML rows. We matched the
exact evaluated source text to that derivative, checked candidate IDs in
Code4ML's checksum-verified `kernels_meta.csv`, downloaded public Kaggle
notebooks, and required the exact code cell to occur in each notebook.

Seven of eight snippets match a row of the derivative exactly. Five have a
candidate ID and were independently found as exact cells in the currently
public notebook. Two derivative matches have no recovered ID; one snippet has
no match. **These counts do not establish that the notebooks are the same
historical revisions used during original annotation.** Kaggle `pull` returned
the current public snapshot, not a pinned revision; the derivative's IDs were
recovered by a third party. We have not verified execution order, all input
files, or runtime state. Source matches are provenance evidence, not label
validation.

| Published test row | Source match | Exact notebook cell | Preliminary code-trace observation |
| --- | --- | --- | --- |
| 34 | Yes | [Rental neural network](https://www.kaggle.com/code/oysteijo/rental-neural-network), cell 11 | Cell 3 concatenates training and competition test features; cell 11 scales the combined table; cell 12 separates them. This exposes the training transform to the unlabeled test feature distribution. Whether the target label treats this transductive step as leakage needs an explicit policy. |
| 49 | Yes | Not recovered | No notebook context. Unresolved. |
| 60 | Yes | [Restaurant revenue prediction](https://www.kaggle.com/code/israakhalil/restaurant-revenue-prediction-small), cell 17 | Cell 16 computes normalization statistics from `OH_X_train`; cell 17 applies those *training* statistics to train and test. That local path does not show test-to-train flow. The published positive label requires independent recheck against the whole notebook and annotation policy. |
| 207 | Yes | [XGBoost Rossmann sales](https://www.kaggle.com/code/omarsayed7/xgboost-rossman-sales), cell 48 | Cell 47 imputes the training table; cell 48 fills test `CompetitionDistance` from the training mean. The local operation does not show test-to-train flow. Check other cells and the original labeling unit. |
| 272 | Yes | [Rossmann notebook](https://www.kaggle.com/code/petertrr/notebook4ffbcedf04), cell 6 | Cell 6 standardizes `store.csv` metadata globally; nearby cells do exploratory embedding/clustering. No model train/evaluation split is visible near the target, so leakage cannot be decided from this cell alone. |
| 273 | Yes | Not recovered | No notebook context. Unresolved. |
| 370 | Yes | [Average perceptron movie reviews](https://www.kaggle.com/code/barelydedicated/average-perceptron-movie-review-classification), cell 6 | Cell 1 loads separate training and testing labels; cell 6 fits `GridSearchCV` on `testing_data, testing_labels`. This is strong visible evidence of holdout reuse for model selection. Human reviewers should verify the full workflow and policy before calling it a confirmed miss. |
| 371 | No | Not recovered | No notebook context. Unresolved. |

Cell numbers in this note are **zero-based** notebook-array indices, not Kaggle
UI line numbers. The CSV records source and notebook SHA-256 values, published
label, three predictions, and provenance status without redistributing raw
third-party code. The archived prediction records contain no class confidence
scores, so a confidence column cannot honestly be filled from this run.

## How to reproduce the provenance table

Obtain the canonical PeerJ test CSV, the annotated derivative CSV, Code4ML
`kernels_meta.csv`, and the five public Kaggle notebooks linked above. Keep
third-party source files outside Git. First run
`scripts/match_code4ml_origins.py` against the two CSVs. Then run
`scripts/audit_persistent_false_negatives.py` against that match JSON, the
five notebooks, the canonical test CSV, and the validated Kaggle evidence ZIP.
Both scripts fail on unexpected canonical fingerprints or output overwrite.
The five downloaded notebook snapshots and derivative data are retained only
in ignored `artifacts/` for review.

From the repository root, after obtaining the public source files at the
indicated paths on a fresh checkout:

```sh
PYTHONPATH=src .venv/bin/python scripts/match_code4ml_origins.py \
  --peerj-test artifacts/peerj2025/test_annotated.csv \
  --code4ml-derived artifacts/code4ml_12700065/annotated_derivative.csv \
  --output artifacts/code4ml_12700065/eight_miss_matches.json
PYTHONPATH=src .venv/bin/python scripts/audit_persistent_false_negatives.py \
  --test artifacts/peerj2025/test_annotated.csv \
  --matches artifacts/code4ml_12700065/eight_miss_matches.json \
  --metadata artifacts/code4ml_12700065/kernels_meta.csv \
  --notebooks artifacts/code4ml_12700065/notebooks \
  --archive results/2026-10-27/codebert_evidence.zip \
  --source-manifest artifacts/kaggle_ready_2026-10-20/source_hashes.json \
  --output results/2026-10-27/persistent_false_negative_audit.csv
```

The verified Code4ML metadata MD5 is
`738958a342398cdbb82eb5473405c4c6`; the derivative CSV SHA-256 is
`f96185e6b0a592626a4308d62cebe3cb9dc9e6dc2947bd064a0cae5e790b7a32`.

## Next review artifact

An [eight-case blind-review protocol](HUMAN_NOTEBOOK_REVIEW_2026-10-27.md)
and generator are ready. The generated packet and two blank forms are ignored
local artifacts; the case-to-review-ID key is kept separate. They do not
contain completed human judgments.

## Research decision

This audit weakens any claim that all eight stable negatives are certainly
model failures. It also shows why isolated-snippet labels and model inputs
should not be equated with full-workflow truth. The next valid step is **blind,
independent human review** of each recovered workflow with a written leakage
definition, followed by adjudication. Preserve the original published label
and both initial reviewer judgments. Do not calculate a new accuracy or make
a benchmark-label-error claim from this preliminary trace.
