# Surface-Edit Sensitivity and Fault-Pair Discrimination in Lightweight ML Leakage Detectors

**Exploratory technical-report draft — not submission-ready.** Prepared September
21, 2026. Results come from `results/2026-09-20/robustness_pilot.json`. Authorship,
independent review, and a confirmation study remain outstanding. This draft does not
establish novelty or reproduce a published neural detector. A September 26 supplement
below adds an actual pinned current MLScent run, not historical-paper replication.

## Abstract

Code-level data-leakage detectors should distinguish a change in experimental
procedure from an irrelevant change in source presentation. We conduct an exploratory
study of two lightweight text classifiers using a published labeled Python-code
dataset. The released split contains 1,523 training and 381 test snippets. Of the
test snippets, 340 parse under our Python environment and admit four automatically
checked AST-preserving transformations. Word- and character-based TF–IDF logistic
classifiers achieve original-test F1 scores of 0.500 and 0.551, respectively. Adding
a comment claiming absence of leakage changes 14 and 13 predictions, respectively;
only four and two of these changes turn correct predictions into incorrect ones.
The remaining changes correct existing mistakes. Separately, the classifiers identify
both endpoints correctly in three and zero of sixteen authored clean/faulty pairs.
These results motivate reporting surface stability together with fault discrimination,
rather than using either accuracy or consistency alone. They establish limitations
of these local baselines, not of CodeBERT, LLMs, or leakage detectors generally.

## 1. Introduction

ML evaluation can be compromised when held-out information influences training or
model selection. Code-based detectors attempt to identify such problems without
requiring an analyst to inspect every pipeline. Their usefulness depends on both
recognizing relevant dependencies and resisting irrelevant source changes.

A model that always reports no fault is perfectly stable under renaming or comment
edits, yet misses every fault. Conversely, changes in its decisions after a real
repair are useful only if the directions are correct. We therefore study two separate
properties: stability under AST-preserving presentation edits and joint correctness
on constructed clean/faulty endpoints.

Our contribution at this stage is a reproducible pilot protocol, a dataset-overlap
diagnostic, and measured results for two explicitly identified local baselines.
We do not claim that the metrics, TF–IDF, AST comparison, or paired testing are new.
Whether an expanded study offers a novel empirical contribution remains unresolved.

## 2. Related work and positioning

Yang et al. study static notebook leakage detection [1]. Alturayeif and Hassine
investigate learned code-leakage detection with transfer learning, active learning,
and prompting, and release data and implementation materials [2–4]. LeakageDetector
2.0 provides notebook detection and correction support [5]. The scicode-lint preprint
uses LLM-generated checking patterns and reports controlled and external evaluations
[6]. These establish that both methodology checking and learned detection predate
our work.

The present study reuses the dataset from [3], but does not rerun the CodeBERT training
or active-learning procedure from [2]. Its classifiers must not be labeled as those
authors' models. Prior code-robustness and metamorphic-testing literature must also
be systematically reviewed before claiming originality for an expanded benchmark.

An October 3 update identifies a systematic review specifically covering metamorphic
testing of deep code models [8]. Therefore, stability testing through source edits
cannot itself be our novelty claim. The official FSE 2026 program also lists work
on leakage detection through static slicing and structured LLM prompts [9]. Its full
method and evaluation still need inspection before any gap relative to that work
is asserted. These sources constrain positioning; they are not new experimental
evidence for this report.

## 3. Research questions

- RQ1: How often do local detector predictions change under source transformations
  preserving the parsed AST, and how many changes help or hurt label agreement?
- RQ2: Can the same detectors classify both endpoints of authored fault-changing
  pairs correctly?
- RQ3: What exact-text and canonical-AST matches exist between the released partitions,
  and how do results differ when matching test rows are excluded?

These are exploratory questions. No power calculation, preregistration, or
independent confirmation set is claimed.

## 4. Materials and methods

### 4.1 Data and provenance

We download Figshare version-1 artifacts [3–4] through file identifiers recorded in
the fetch script. Downloads are checked against published MD5 digests and assigned
SHA-256 fingerprints. Raw code is cached locally, not redistributed in our result
records, and is never executed. We retain original text case and original partitions.
Training contains 91 positive labels; testing contains 25 positives. These counts
describe the downloaded files, not a reconstruction of every paper experiment.

Six test rows match training text exactly. Sixteen match a training AST after
removing location attributes; the exact matches fall within that union in this run.
We therefore report both the original 381-row test and a 365-row unmatched subset.
This exclusion is not a retrained, repository-grouped benchmark, nor does it establish
performance inflation in the original paper. Generic snippets may legitimately
repeat; their context and origins require review.

### 4.2 Baselines

Both baselines use logistic regression with C=1, balanced class weights, maximum
2,000 iterations and random state 0. One uses case-sensitive word unigrams and
bigrams. The other uses character 3–5-grams with a 30,000-feature cap and the
vectorizer's default lowercasing. Vectorizers and classifiers fit training data only.
No test-driven hyperparameter search was performed for these baselines. Their
standard classification threshold is retained.

Constant-positive and constant-negative controls are included in the result file.
Always predicting negative obtains 356/381 accuracy (93.44%) but zero positive
recall. Accuracy alone is consequently unsuitable for assessing this imbalanced task.

### 4.3 Surface transformations

For parseable test snippets we append a neutral comment, a comment asserting no
leakage, and a comment asserting leakage; a fourth transformation unparses the AST
to normalize presentation. Each candidate must reproduce the original AST excluding
location attributes. We do not rename variables in this pilot.

Forty-one snippets cannot be parsed and receive original predictions only. Their
exclusion from transformation denominators is explicit. AST identity does not prove
equivalence for source-inspecting programs, line-number-sensitive behavior, or
tools treating comments as directives. The unparsing condition also removes comments
and changes formatting simultaneously; it cannot isolate those effects.

### 4.4 Fault-changing controls and metrics

Sixteen existing authored pairs span four fault families and four source styles.
The labeled distinction is the designated leakage condition, not general program
correctness. These are source controls, not independently reviewed executable
workflows. Related styles are not independent observations.

For surface edits we count prediction flips, correct-to-wrong flips, and
wrong-to-correct flips. For fault pairs, success requires a negative prediction on
the clean endpoint and a positive prediction on the faulty endpoint. A reversed
prediction change is failure. We report confusion matrices and F1 for original
predictions. We do not produce inferential intervals over correlated variants.

## 5. Results

### 5.1 Original predictions

| Baseline | TP | FP | FN | TN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Word TF–IDF | 13 | 14 | 12 | 342 | .481 | .520 | .500 |
| Character TF–IDF | 19 | 25 | 6 | 331 | .432 | .760 | .551 |

After excluding exact/AST training matches, F1 is .531 for both baselines when rounded
to three decimals. The word score increases and the character score decreases.
This does not support a general claim that overlap inflated both local scores.

### 5.2 Surface sensitivity

Each cell below gives flips, followed by correct-to-wrong/wrong-to-correct counts.
All transformation denominators are 340 parseable original test snippets.

| Edit | Word baseline | Character baseline |
| --- | ---: | ---: |
| Neutral comment | 8 (2 / 6) | 1 (0 / 1) |
| No-leakage claim | 14 (4 / 10) | 13 (2 / 11) |
| Leakage claim | 14 (4 / 10) | 12 (2 / 10) |
| AST unparsing | 1 (0 / 1) | 3 (2 / 1) |

The comments are appended rather than replacing original text. They change lexical
representations and can influence decisions without altering parsed operations.
Opposite claims share vocabulary; similar aggregate effects do not establish that
the models interpret or follow either claim. Most claim-comment flips improve label
agreement, so describing all flips as successful attacks would be incorrect.

### 5.3 Fault-pair discrimination

The word classifier correctly classifies both endpoints in 3/16 pairs. The character
classifier does so in 0/16. This is evidence of poor transfer to these authored
controls, not proof of an inability to reason or a measured neural-model failure.
The controls differ from the training corpus and may involve incomplete context.

## 6. Discussion

Our results show why stability and useful detection must be measured separately.
High invariance can coexist with poor fault discrimination. They also show why
surface perturbation findings need directional error accounting: changes sometimes
correct an already wrong answer. A future benchmark should preserve this accounting
while expanding to published neural and static baselines and externally authored
workflows with reviewed labels.

The result is not a new detector and should not be marketed as one. The project's
earlier provenance integration remains supporting infrastructure, not the central
contribution of this pilot report.

## 7. Threats and missing evidence

The study uses two simple classifiers, one public snippet dataset, four fixed edits,
and a small authored control set. Snippet identifiers do not recover repository or
author groups. Source snippets may lack context needed to verify labels. AST
preservation is narrower than complete semantic equivalence. Transformation-eligible
rows differ from nonparseable rows. The test set is now development evidence.

No modern LLM or CodeBERT has been evaluated in this pilot. The supplement evaluates
a current revision of the paper-linked static tool MLScent, with incomplete task
alignment; it does not reproduce the historical paper's numbers. No human agreement
study or second-machine replication has been completed.
New confirmation data, grouping information, label adjudication, and baseline
reproduction are prerequisites for broader conclusions. These limitations currently
prevent a submission claiming robust comparative findings across detector classes.

## 8. Reproducibility and responsible reporting

Run the pinned fetcher, evaluation script and test suite listed in the handoff
document. Results record data hashes, implementation hashes and environment versions.
No external source is executed and no paid model API is used. Further release must
respect dataset/source licenses and the selected venue's anonymity requirements.
Human authors must verify claims and disclose AI assistance under venue policy.

## 9. Conclusion

This pilot provides reproducible evidence of surface sensitivity and weak authored
fault-pair transfer for two lexical leakage classifiers. It does not establish a
novel algorithm or the failure of published neural detectors. Its immediate value is
a tested evaluation scaffold and specific questions for a larger independent study.

## Supplement: current MLScent implementation (September 26)

We additionally executed upstream MLScent [7] at revision
`c22cb3ad5fd2927434dcb77c1f9ce475e44d7cb4`, without modifying its implementation.
Its own suite passed 212 tests with one skipped. We mapped its two leakage-checking
components to positive/negative/unknown decisions, retaining skips and caught errors
as unknown rather than negative. Full methods, commands and evidence are in
`docs/mlscent_replication_2026-09-26.md` and `results/2026-09-26/mlscent.json`.

On the PeerJ originals, only 31/381 snippets received definite combined answers:
309 lacked required import context and 41 produced component errors. The answered
subset had TP=2, FP=3, TN=25 and FN=1 against broad published leakage labels. All
four surface-edit conditions produced zero flips among 31 answered pairs; this is
not a stability claim over all 340 transformed inputs. On the previously explored
ASE corpus, 58/66 explicitly preprocessing-labeled notebooks received answers, with
TP=4, FP=3, TN=36 and FN=15. These category/coverage differences prevent an overall
ranking against the lexical models from these aggregates.

A complete authored executable example provides a narrower finding. MLScent warns
after full-data scaling followed by a split, but the warning disappears when a
subsequent model fit is appended. Execution confirms the scaler has still seen all
178 rows, versus 124 training rows. The upstream rule's last-fit line tracking
explains this result. This witness demonstrates a specific rule failure, not its
real-world prevalence or score-inflation magnitude. Independently reviewed full
workflows and neural-baseline reproduction remain outstanding.

## Implementation update (September 29; not experimental results)

A pinned modern CodeBERT training and evaluation runner is now implemented, with
fixed-budget training before test-set access and checks rejecting smoke/preflight
outputs as scientific evidence. Tiny-model serialization and a real-checkpoint
two-example CPU training preflight passed. Full neural training, held-out scores
and repeated-seed robustness estimates remain outstanding. No neural performance
claim follows from these implementation checks. See `docs/codebert_runbook.md`.

## Supplement: tokenizer exposure (October 16)

We additionally measured edit visibility using the pinned CodeBERT tokenizer and
the documented lowercasing protocol, without training a detector. Among 340
parseable original snippets, each appended-comment condition changes full token
sequences in all 340 cases. At the intended 512-token limit, only 331 changes remain
visible: nine (2.65%) produce identical model inputs after truncation. Diagnostic
limits of 256 and 128 erase 28 (8.24%) and 88 (25.88%) changes, respectively.
These shorter limits are not new training conditions. For AST-unparsing, six pairs
already have identical full token sequences; no additional change is erased at 512.

Every comparison was checked against actual padded/truncated tokenizer inputs.
The saved record is `results/2026-10-16/token_visibility.json`; two runs were
byte-identical. These are exposure measurements, not prediction or accuracy results.
They justify separate source-eligible and token-visible denominators, but do not
establish a novel method or meaningful detector-performance difference.

## References

1. Yang et al. (2022). *Data Leakage in Notebooks: Static Detection and Better Processes*.
   https://arxiv.org/abs/2209.03345
2. Alturayeif and Hassine (2025). *Data leakage detection in machine learning code:
   transfer learning, active learning, or low-shot prompting?* PeerJ Computer Science,
   11:e2730. https://doi.org/10.7717/peerj-cs.2730
3. Alturayeif and Hassine (2025). Dataset, version 1.
   https://doi.org/10.6084/m9.figshare.24893799.v1
4. Alturayeif and Hassine (2025). Code, version 1.
   https://doi.org/10.6084/m9.figshare.24893832.v1
5. Truong et al. (2025). *LeakageDetector 2.0: Analyzing Data Leakage in Jupyter-Driven
   Machine Learning Pipelines*. https://arxiv.org/abs/2509.15971
6. Samsonau (2026). *scicode-lint: Detecting Methodology Bugs in Scientific Python
   Code with LLM-Generated Patterns*. Preprint, v2. https://arxiv.org/abs/2603.17893v2
7. Shivashankar and Martini (2025). *MLScent A tool for Anti-pattern detection in ML
   projects*. CAIN 2025. https://arxiv.org/abs/2502.18466
8. Asgari, de Koning, Derakhshanfar and Panichella (2025). *Metamorphic Testing of
   Deep Code Models: A Systematic Literature Review*. https://arxiv.org/abs/2507.22610
9. Draoui, Mkaouer and Newman (2026). *Improving Data Leakage Detection in Machine
   Learning Notebooks through Static Slicing and Structured LLM Prompts*.
   FSE 2026 research-program entry (full paper not inspected in this update).
   https://conf.researchr.org/track/fse-2026/fse-2026-research-papers

# October 27 evidence addendum

The completed three-seed CodeBERT Kaggle experiment and its limitations are
documented in `results/2026-10-27/report.md`. This draft's earlier statements
that no full CodeBERT run exists describe the original pilot stage and are
superseded by that report. Do not submit this draft without integrating the
validated results, human review, confirmation experiments and a novelty audit.
