# Exposure-Aware Robustness Auditing of a CodeBERT Data-Leakage Classifier

**Working empirical-study draft — not ready for submission.** Authorship,
human review, independent confirmation, and final novelty assessment are open.
No findings below should be described as a new algorithm or invention.

## Abstract (provisional)

Code-level data-leakage detectors are commonly evaluated on labeled snippets,
but aggregate classification scores do not show whether predictions are stable
under innocuous source edits or whether those edits survive model preprocessing.
We audit a fixed-budget CodeBERT classifier trained on a published leakage
dataset. Three prespecified seeds are evaluated on 381 original test snippets
and four AST-preserving edits of 340 parseable snippets. Original F1 ranges from
0.698 to 0.756. Prediction flips are uncommon, but eight of 25 positive cases
are missed by all seeds. Nine appended-comment pairs are invisible at the
512-token model limit. Six test cases exactly match training text and 12 match
nonempty training ASTs; excluding those 12 does not consistently lower F1.
We distinguish harmful from corrective flips and retain
case-level evidence. These are within-corpus descriptive findings on an
explored split; independent labels and external confirmation are pending.

## 1. Introduction

When a detector says a pipeline is free of leakage, a false negative may let
an invalid experiment proceed. Yet a single benchmark F1 does not identify
which failures persist across training randomness or whether a textual edit
can change a prediction without changing the relevant program structure.
This paper asks: (RQ1) How accurately does a fixed-budget CodeBERT classifier
identify leakage on the published split? (RQ2) Under AST-preserving edits,
how often are model inputs actually changed, and how often do predictions
change? (RQ3) Are errors concentrated in particular cases across seeds?

The contribution *candidate* is an auditable evaluation protocol combining
source transformation checks, tokenizer exposure checks, directional outcomes,
and cross-seed case-level analysis. Each ingredient has precedent; whether the
combination merits publication is still unresolved.

## 2. Related work and positioning

[Alturayeif and Hassine (2025)](https://peerj.com/articles/cs-2730/) already
study CodeBERT-based leakage detection using the underlying data. Our model
training is a baseline implementation, not a novel detector or exact reproduction
of their optimization procedure. They also explicitly acknowledge the lack of
cross-cell context in their snippet labels. [Asgari et al. (2025)](https://arxiv.org/abs/2507.22610)
review metamorphic testing for deep code models; semantic-preserving edits and
robustness measurements are not new in themselves. [Applis et al. (2021)](https://doi.org/10.1109/ASE51524.2021.9678706)
already transform CodeBERT inputs in another task, and a [2026 CodeBERT
preprint](https://arxiv.org/pdf/2609.21203) already reports directional flips
and grouped uncertainty for vulnerability classification. [Draoui et al. (2026)](https://doi.org/10.1145/3808199)
study leakage detection with static slicing and structured LLM prompts. A
[2025 abstract-interpretation study](https://caterinaurban.github.io/pdf/scp2025.pdf)
also finds that notebook leakage often spans multiple cells; context
dependence is not a new observation. A
[recent real-world notebook study](https://www.sciencedirect.com/science/article/abs/pii/S0950584926003253)
reports fine-grained annotations of 614 model pairs. We have not established
whether its artifact is available, licensed, or compatible with this task.
The latter two full papers need deeper comparison before novelty claims; the
[bounded closest-work audit](../docs/CLOSEST_WORK_AUDIT_2026-10-27.md)
records what was verified and what remains unknown.

## 3. Methods

The published data comprises 1,523 training and 381 test code snippets, with
25 positive test labels. We fine-tuned `microsoft/codebert-base` at pinned
revision `3b0952feddeffad0063f274080e3c23d75e7eb39`. The frozen protocol
uses four epochs, maximum length 512, effective batch 16, microbatch 2,
learning rate 5e-5, and seeds 0, 1, and 2. All three runs completed in a
private Kaggle GPU notebook. The test data was not used for model selection.
This test set has nevertheless been explored by the research project and is
not a fresh confirmation set.

For each of 340 Python-parseable test snippets, we append a neutral comment,
append a comment claiming the code is safe, append a comment claiming a fault,
or reformat via `ast.unparse`. The generator requires equality of Python AST
fingerprints excluding location attributes. This is a bounded structural
check, not proof of semantic equivalence for self-inspecting programs or
tooling-sensitive comments. For each pair we record whether token IDs presented
to CodeBERT differ, whether the prediction flips, and whether that flip changes
an originally correct answer to wrong or vice versa. We do not pool seeds as
independent datasets.

The [archived evidence](../results/2026-10-27/codebert_evidence.zip) contains
fixed configurations, loss logs, per-case predictions and hashes, environment
metadata, and independently recomputed tables. The archive deliberately omits
raw third-party code and checkpoint weights. See the
[validated report](../results/2026-10-27/report.md) for its SHA-256 and exact
reproduction command.

## 4. Results on the explored split

| Seed | TP | TN | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 17 | 353 | 3 | 8 | .850 | .680 | .756 |
| 1 | 15 | 353 | 3 | 10 | .833 | .600 | .698 |
| 2 | 17 | 351 | 5 | 8 | .773 | .680 | .723 |

Eight positive test cases are false negatives in every seed, while ten of
381 original cases have differing predictions across seeds. Across all edits
and seeds, 16 distinct cases exhibit at least one prediction flip; eight are
positive and eight negative. The mean per-seed all-pair flip rates are 0.39%
(neutral comment), 1.67% (safe claim), 1.08% (fault claim), and 0.98%
(formatting). The full per-seed counts, including harmful and corrective
flips, are in the [generated table](../results/2026-10-27/codebert_tables.md).
At 512 tokens, 9/340 appended-comment edits are invisible; 6/340 formatting
edits produce equivalent token inputs. An unchanged prediction when the edit
was invisible is not evidence of learned robustness.

The published split also contains six exact training-text duplicates and 12
nonempty-AST training matches. Excluding the union of those 12 test cases
leaves 369 examples, including all 25 positives. Nonoverlap F1 is 0.756,
0.698, and 0.739 for seeds 0, 1, and 2 respectively. All eight persistent
false negatives remain in this subset. This post-hoc deduplication is a
sensitivity check, not independent validation. An earlier analysis incorrectly
counted unrelated comment-only snippets as AST matches; the
[corrected analysis](../results/2026-10-27/codebert_overlap_nonempty_ast_v2.json)
supersedes it and provides exact confusion counts and checksums.

On exactly matched original cases, CodeBERT is correct where word TF–IDF is
wrong on 17–18 cases per seed, while word TF–IDF alone is correct on 3–4.
Against character TF–IDF, CodeBERT alone is correct on 21–24 cases while the
lexical model alone is correct on 3–4. However, on the positive subset,
character TF–IDF identifies 2–4 cases per seed missed by CodeBERT, with no
positive-only wins for CodeBERT. The [matched-case analysis](../results/2026-10-27/matched_baseline_analysis.json)
checks source hashes and labels. It is descriptive because training protocols
differ and the split has already been explored.

## 5. Discussion and threats to validity

The strongest present lead is persistent false-negative behavior on a small
set of positives, not an across-the-board lack of robustness. A preliminary
[source-provenance audit](../docs/PERSISTENT_MISS_PROVENANCE_2026-10-27.md)
matched five of eight misses to exact cells in public notebook snapshots.
Their surrounding code includes both a clear holdout-reuse pattern and local
operations that appear to use training-derived statistics correctly. This
does **not** establish that any published label is wrong: historical notebook
revisions, full execution context, the annotation unit, and independent human
judgments are still missing. An expanded [positive-label provenance
check](../docs/POSITIVE_CONTEXT_GATE_2026-10-29.md) found exact current
notebook cells for 15 of 25 published positives. Their cases suggest that a
cell's own behavior and a notebook-level workflow label may be different
constructs, but the analysis is post hoc and source recoverability is
selective. No revised performance estimate follows from it. The post-hoc
targeted-review sample can generate explanations but cannot estimate population
prevalence. The 25 positive cases are too few for fine-grained subgroup claims
without large uncertainty. Three seeds show optimizer variation, not three
independent test samples. Strong accuracy is partly a class-imbalance effect.
The transformation study uses only four edit families; broader robustness is
unmeasured. Cross-paper performance numbers are not directly comparable
because protocols differ.

## 6. Release gates before submission

1. Two people first complete the blinded eight-case notebook-context packet
   independently; preserve the original forms, report agreement, and adjudicate
   disagreements separately. This selected packet explains persistent misses
   but cannot measure label-error prevalence. The older 20-case snippet pilot
   and 24-case targeted packet are separate, still-unreviewed exploratory
   materials—not substitutes for notebook-context review. If the eight cases
   reveal a recurrent context problem, prespecify a larger balanced sample
   including negatives before inspecting its model outcomes.
2. Obtain or construct a separately sampled, licensed confirmation corpus
   with repository grouping. Freeze the sampling/exclusion rule before scoring.
   The [data-source audit](../docs/CONFIRMATION_DATA_AUDIT_2026-10-27.md)
   explains why currently cached sources do not yet meet this requirement.
3. Evaluate CodeBERT and credible matched-task baselines on that corpus,
   including coverage, precision, recall, false-positive rate, and paired
   uncertainty at the original repository or workflow level.
4. Conduct a full-text closest-work comparison, particularly against the
   2025 review's closest primary studies and the 2026 leakage papers.
5. Reproduce the saved analysis on another machine, audit data/weight release
   rights, agree authorship and AI-assistance disclosure, then obtain independent
   technical feedback before choosing a venue.

If these gates fail, report an exploratory replication/negative result rather
than presenting this as a novel method paper.
