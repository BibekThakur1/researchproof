# ResearchProof: Evaluation-Score Provenance and the Limits of Synthetic Leakage Benchmarks

## Assessment

ResearchProof now supports a reproducible exploratory investigation, with a concrete
representation defect, counterexamples to an evaluation-count heuristic, and a first
external audit using previously published human labels. These findings justify
continued work on a narrower problem: tracking whether evaluation results influence
the choice of the model whose performance is being reported.

The present implementation is not a validated general notebook auditor. External
results contradict any interpretation of the synthetic pilot as evidence of broad
detection ability. The strongest near-term output is a transparent technical report
about these limits and an explicit provenance prototype. A submission arguing for a
new general detector would require substantially more evidence.

The proposed working title is **Evaluation-Score Provenance for Auditing Model
Selection and Test-Set Reuse**. It describes the mechanism under investigation without
claiming priority, novelty, or universal validity.

## Problem in plain language

A researcher trains several models, checks their scores and chooses one. If the same
test data helped choose the winner, reporting its score as an independent final test
can be misleading. But simply evaluating a fixed model twice does not cause it to
learn from those evaluations. Similarly, reporting every predeclared model without
choosing a winner differs from selecting and reporting the best test score.

Counting evaluations therefore loses relevant information. A useful auditor needs
to know which scores affected the decision, which data produced those scores, and
which data supports the final reported evaluation. The prototype represents this
information explicitly. The engineering challenge is obtaining it reliably from
real workflows, where decisions may occur in loops, library calls, files, notebooks,
or a person's reasoning outside the code.

This is research about the reliability of AI experiments. It combines program
analysis, ML evaluation and learned code classifiers. It does not currently train a
new foundation model, and adding an LLM alone would not establish a contribution.

## Closest-work review

The review combines foundational work with directly relevant 2025–2026 publications
and software. Preprints are identified as such; their reported findings have not
been independently reproduced here. The entries below describe the parts relevant
to our design and the comparison still needed.

| Work | Relevant established work | Implication for ResearchProof |
| --- | --- | --- |
| Yang et al., ASE 2022 [1] | Static notebook analysis for preprocessing, overlap and multi-test leakage; public evaluation artifacts | Static leakage detection and repeated-test warnings are prior work. Use their corpus and attempt a compatible detector rerun. |
| Drobnjaković, Subotić and Urban [2] | Abstract-interpretation approach to data-leakage analysis | Set propagation is not a new research contribution by itself. Formal guarantees require an explicit supported language and semantics. |
| Truong et al., LeakageDetector 2.0, 2025 [3] | Notebook detection with quick fixes and LLM-assisted correction | Detection plus repair suggestions is already established. Our clean-counterpart reruns are not arbitrary-code repair. |
| Alturayeif and Hassine, 2025 materials [4] | Transfer learning, active learning and prompting for code leakage detection | Training a code classifier is also prior work. Compare against learned methods only with matched labels and partitions. |
| Samsonau, scicode-lint, 2026 preprint [5] | Local LLM methodology checks with generated patterns and controlled/external evaluations | Methodology checking with an LLM is crowded. Its difference between controlled and external results makes external testing necessary. |
| Roth, 2026 preprint v2 [6] | Large counterfactual leakage-severity study over 2,047 iid datasets and a temporal boundary experiment | A small study showing that test selection changes scores would have weak novelty. Focus on detection semantics and evidence completeness. |
| Blum and Hardt, ICML 2015 [7] | Ladder mechanism for reliable leaderboard evaluation | Adaptive reuse is a longstanding problem. The proposed monitor does not replace statistical reusable-holdout mechanisms. |
| Namaki et al., Vamsa [8] | Automated provenance tracking in data-science scripts | Provenance is an established systems technique; the exact decision boundary and its measured utility must distinguish new work. |
| Eghbali, Burk and Pradel, DyLin, FSE 2025 [9] | Dynamic Python linting | Runtime observation is not new. Compare supported operations, execution coverage and overhead. |
| Shivashankar and Martini, MLScent, 2025 [10] | ML anti-pattern detection tooling | A broad collection of checks would not be a defensible central contribution. |

The literature supports a specific motivation, but does not establish that our
proposed mechanism is novel. In particular, the 2022 work already discusses model
selection and independent evaluation. The potential contribution would have to be a
well-defined, practically useful treatment of score dependencies and missing
provenance, demonstrated beyond explicitly instrumented toy programs.

## Research questions

**RQ1. Representation:** Does Boolean encoding of runtime observations remove the
information required to recognize repeated-test tuning?

**RQ2. Decision semantics:** Can evaluation-count rules distinguish test-driven model
selection from repeated reporting, validation selection and fresh final evaluation?

**RQ3. Evidence completeness:** Can a monitor distinguish observed absence of reuse
from insufficient execution history, without treating missing information as clean?

**RQ4. External transfer:** Do the current synthetic-source baselines retain useful
recall and false-positive rates on previously published notebook examples?

**RQ5. Practical continuation:** Can score origins be captured across real search
callbacks or persisted results at acceptable overhead, with measurable benefit over
credible static and learned baselines? RQ5 remains untested.

## Study 1: information lost by Boolean features

The original runtime feature extractor maps every evidence value through `bool`.
As a result, one test evaluation and five test evaluations both become 1. The new
experiment preserves the original implementation as the presence baseline and adds
a `log_count` ablation using log(1+x). All detector fitting continues to exclude the
held-out dataset or fault family.

The unchanged v0.4 benchmark contains 360 records. Presence encoding produces four
distinct runtime feature vectors, one shared by both labels. Counting the largest
label group within each identical-vector group gives an empirical classification
ceiling of 315/360, or **87.5%**, for any deterministic classifier restricted to those
features. This is an information limit for this finite dataset, not evidence that
logistic regression needs a larger model.

The proof is direct: identical input vectors require the same deterministic output.
Within a group containing both labels, at least the minority-label count must be
misclassified. Summing each group's majority count gives the maximum possible number
of correct predictions. This elementary diagnostic is not presented as new theory.

| Runtime-only encoding | Dataset-holdout accuracy | Dataset-holdout F1 | Unseen-fault F1 |
| --- | ---: | ---: | ---: |
| Boolean presence | 0.8750 | 0.8571 | 0.0000 |
| log(1+count) | 0.9583 | 0.9565 | 0.0000 |

Count encoding removes the observed vector-label conflicts but does not make all
vectors linearly separable or force a trained classifier to achieve the bound. The
unseen-fault result remains poor. Hybrid log-count features also fail on this protocol.
These results correct the earlier interpretation: part of the runtime failure was
caused by an implementation representation choice, while generalization remains a
separate problem.

## Study 2: controlled score-dependency experiment

The study uses three scikit-learn datasets, five fixed seeds, logistic regression
and decision trees, and candidate budgets of two, three and five. Every split has
disjoint training, validation, selection-test and fresh-test row identities. The
training share is 60%; the remaining shares are approximately 20%, 10% and 10%.
Candidates are trained only on training rows, with preprocessing inside pipelines.

Nine scenarios are evaluated for each dataset/seed/model/budget combination:
single reporting, repeated reporting, predeclared comparison, validation selection,
test selection with cached reporting, test selection followed by fresh evaluation,
single-score threshold selection, pooled-score selection, and missing history.
This gives 810 constructed cases: 720 labeled and 90 with unknown history.

The labels describe observed selection reuse under the stated workflow. They do not
judge the entire experiment. They are generated from construction rules and have not
received independent human validation. The same author developed the API and cases,
and the scenarios reuse fitted models. Thus 810 is not an independent sample size.

The new API represents a score as a value plus dataset-qualified row identities.
Selection combines the provenance of all compared scores and candidate histories,
including losing candidates. Mean-score composition preserves every contributing
origin. Final reporting checks intersection between selection origins and report
rows. Missing history yields an insufficient-evidence verdict unless a positive
reuse witness is already present.

| Method | True positives | False positives | False negatives | F1 |
| --- | ---: | ---: | ---: | ---: |
| Local count-only heuristic | 198 | 270 | 72 | 0.5366 |
| Explicit selection provenance | 270 | 0 | 0 | 1.0000 |
| Remove selection dependencies | 0 | 0 | 270 | 0.0000 |
| Remove row identity | 270 | 180 | 0 | 0.7500 |

The provenance method abstains on all 90 unknown-history cases. The count rule makes
a definite decision on all of them. Unknown cases are not included in accuracy or
F1 denominators, and are reported separately.

The count rule's errors are useful counterexamples. Repeated reporting and fixed
candidate comparison generate false positives. Selection followed by evaluation on
a fresh partition also exposes its lack of report-specific reasoning. A single
score can influence a threshold decision without requiring multiple test calls;
72 such cases evade the heuristic in this run.

Perfect API performance establishes that the explicit mechanism implements these
constructed semantics. It does not establish real-code detection, statistical
validity, novelty or superiority over published tools. Callers currently supply
score origins and selection events; omitted or incorrectly declared events can
defeat the monitor. Automated capture and externally authored tests are the hard
next steps.

## Study 3: external notebook audit

The original ASE 2022 artifact repository provides human ground truth, archived
predictions and sampled notebooks. The download is pinned to revision
`3aec5fa09788d6659c6e1eac79cdc503340d9694`, with independently recorded SHA-256 values.
All 100 ground-truth rows are considered. Notebooks are parsed without execution.
No sampled notebook source is added to this repository. [11]

There are 66 rows with explicit labels for each leakage category. The local
normalizer/parser handles 86 of 100 notebooks; 58 have both usable source and explicit
labels. Eight labeled cases remain unanswered. Blank category labels are not turned
into clean labels. The normalization uses document order and comments out notebook
magic commands; that policy can itself cause parsing failures and differs from the
original authors' environment.

The symbolic analyzer is unchanged from the earlier local baseline:

| Category | Answered / eligible | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Preprocessing | 58 / 66 | 0.2500 | 0.1053 | 0.1481 |
| Overlap | 58 / 66 | 0.0000 | 0.0000 | 0.0000 |
| Multi-test | 58 / 66 | 1.0000 | 0.0357 | 0.0690 |

The single multi-test true positive gives perfect precision but extremely low recall.
It would be misleading to emphasize precision alone. Similarly, overlap accuracy is
high because most answered notebooks lack that particular label; the analyzer misses
all seven labeled overlap cases in the answered subset.

An exploratory follow-up trains the existing AST logistic model only on the 44
built-in source snippets, with its existing configuration and a 0.5 decision
threshold. On the 58 eligible external notebooks it finds all 39 any-fault positives
but falsely flags 18 of 19 clean examples. Its F1 is 0.8125 and its false-positive
rate is **94.7%**. An always-fault predictor has F1 approximately 0.8041 on the same
subset. The learned model therefore provides little practical discrimination despite
an apparently respectable aggregate F1.

The archive's saved published predictions are summarized separately in the evidence
file. They are not a fresh execution of the original tool. Soufflé is absent from
this environment and the Docker daemon is not running; no claim of reproducing that
detector's runtime or comparing identical tool environments is made.

## What the evidence supports

Three development findings are now reproducible. First, the original runtime
representation has a demonstrable information ceiling. Second, evaluation counts
alone are insufficient for the proposed observed-selection semantics. Third,
self-authored source success transfers poorly to the external corpus, and a high
F1 can mask a nearly always-positive detector.

The findings concern these implementations and datasets. They are not discoveries
that test-set selection is harmful; that is established. They also do not support
a claim that the prototype outperforms a published analyzer. The external study
tests the old source analyzer and AST model, while the provenance study tests an
explicit API. Those input conditions are different and must not be collapsed into
one comparison table implying equal capabilities.

## Threats to validity and corrections to earlier project claims

Synthetic variants share code and model fits. Dataset holdouts in generated traces
retain the same fault vocabulary. The small datasets are convenient engineering
resources rather than a representative sample of scientific applications. Wine's
final partitions are particularly small. No population-level confidence interval is
attached to constructed detection counts.

The external corpus is old, includes unsupported libraries, and has missing or
unusable sources. A set of notebooks does not automatically establish independent
projects or authors. After this exploratory inspection it must not be called an
unseen confirmation set for future tuned versions.

The runtime monitor currently records calls explicitly added to the benchmark. It
does not automatically capture arbitrary third-party training code. The repair suite
reruns predefined clean counterparts; it has not learned to edit arbitrary programs.
The static analyzer is a small heuristic with limited flow and library support.
Previous perfect pilot scores should be described with these limits.

The score API assumes complete declared selection history. Raw-number conversion,
serialization without origins, unobserved human choices, row-ID renaming and nested
search code remain unvalidated boundaries. A row intersection is evidence of reuse
under the declared semantics; it is not an estimate of resulting optimism or a proof
that every use is statistically impermissible under all evaluation protocols.

## Publication path and next experiment

The most defensible next experiment captures score provenance across one real
workflow boundary, such as a search callback or persisted evaluation table. Specify
the supported path, introduce deliberate provenance loss, and measure whether the
system reports insufficient evidence instead of silently accepting the result.
Track both detection utility and instrumentation cost.

Freeze the implementation before evaluating new independently written workflows.
Include harmless repeated reporting, cached scores, aggregation, nested validation,
fresh final tests, and unsupported operations. Have two people independently review
workflow labels and resolve disagreements in writing. A friend can reproduce the
current commands on another laptop now; this does not require new devices or GPUs.

A workshop or technical report becomes plausible if the failure analysis, API scope
and external comparison are carefully developed. A full conference submission needs
a stronger technical mechanism or substantially broader validated evidence. No venue
acceptance or admissions outcome can be predicted from the present pilot.

## Patent screening boundary

The technical distinctiveness is currently unestablished. Searches for test-data
leakage and model-evaluation patents returned prior disclosures involving evaluation
interfaces, maintained split state and duplication checks, including the interactive
model-evaluation family represented by CA2953969C. [12] This was an initial search,
not an exhaustive claims analysis. Ordinary provenance unions and Boolean/count
features do not, on their own, justify presenting an inventive architecture.

## Reproduction and evidence

From the repository root after installing the pinned dependencies:

```bash
source .venv/bin/activate
python scripts/generate_benchmark.py --config configs/benchmark_pilot.yaml
python scripts/run_selection_study.py
python scripts/evaluate_learned.py \
  --index artifacts/benchmark_v0_4/runs.jsonl \
  --output artifacts/selection_study_v1/encoding_ablation.json
python scripts/fetch_ase22_materials.py
python scripts/evaluate_external_ase22.py
python scripts/build_research_evidence.py
ruff check .
python -m pytest -W error
```

`results/2026-09-13/evidence.json` contains metrics, input hashes, dataset fingerprints,
library versions and implementation hashes. `tables.md` contains generated tables.
Raw generated traces and external source remain in ignored `artifacts/` directories.
The notebook archive is about 43 MB. There are no paid APIs or GPU requirements in
these experiments. A different platform may produce small numerical differences;
compare semantic decisions and report any discrepancy rather than editing outputs.

## Sources

1. Yang, C., Brower-Sinning, R. A., Lewis, G. A., and Kästner, C. *Data Leakage in
   Notebooks: Static Detection and Better Processes*. ASE 2022.
   https://www.cs.cmu.edu/~ckaestne/pdf/ase22.pdf
2. Drobnjaković, F., Subotić, P., and Urban, C. *Abstract Interpretation-Based Data
   Leakage Static Analysis*. arXiv record, with later revisions.
   https://arxiv.org/abs/2211.16073
3. Truong, O., et al. *LeakageDetector 2.0: Analyzing Data Leakage in Jupyter-Driven
   Machine Learning Pipelines*. 2025. https://arxiv.org/abs/2509.15971
4. Alturayeif, N., and Hassine, J. *Code for Data Leakage Detection in Machine
   Learning Code*. Research software, February 2025.
   https://figshare.com/articles/code/Code_for_Data_Leakage_Detection_in_Machine_Learning_Code/24893832
5. Samsonau, S. V. *scicode-lint: Detecting Methodology Bugs in Scientific Python
   Code with LLM-Generated Patterns*. Preprint v1, March 2026.
   https://arxiv.org/html/2603.17893v1
6. Roth, S. *Which Leakage Types Matter? A Quantitative Landscape Across 2,047
   Benchmark Datasets*. Preprint v2, May 2026. https://arxiv.org/html/2604.04199v2
7. Blum, A., and Hardt, M. *The Ladder: A Reliable Leaderboard for Machine Learning
   Competitions*. ICML 2015. https://proceedings.mlr.press/v37/blum15.html
8. Namaki, M. H., et al. *Vamsa: Automated Provenance Tracking in Data Science
   Scripts*. 2020. https://arxiv.org/abs/2001.01861
9. Eghbali, A., Burk, F., and Pradel, M. *DyLin: A Dynamic Linter for Python*.
   FSE 2025. https://software-lab.org/publications/fse2025_DyLin.pdf
10. Shivashankar, K., and Martini, A. *MLScent: A Tool for Anti-pattern Detection in
    ML Projects*. 2025. https://arxiv.org/abs/2502.18466
11. Yang et al., evaluation artifact repository, inspected at the pinned revision.
    https://github.com/malusamayo/GitHubAPI-Crawler/tree/3aec5fa09788d6659c6e1eac79cdc503340d9694/evaluation_materials
12. *Interactive interfaces for machine learning model evaluations*, CA2953969C.
    https://patents.google.com/patent/CA2953969C/en

Sources checked on 13 September 2026. Search terms included data leakage static
analysis, repeated evaluation versus model selection, score provenance, counterfactual
leakage repair, 2026 methodology linting, and test-data leakage patents. Source status
and versions are stated where they affect interpretation. No absence-of-prior-work
claim is inferred from these searches.
