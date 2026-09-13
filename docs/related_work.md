# Closest work and novelty boundary

This document is a living literature map, updated on 13 September 2026. It
separates established work from the contribution ResearchProof is currently testing.
It is not evidence that the project is novel, and it must be updated before any
submission.

The expanded [research report](research_report_2026-09-13.md) adds directly relevant
2026 work: scicode-lint (arXiv:2603.17893) and Which Leakage Types Matter?
(arXiv:2604.04199v2). These substantially constrain novelty claims about LLM-based
methodology checking and counterfactual leakage-severity experiments. It also covers
Vamsa, DyLin, MLScent, learned leakage detectors, and reusable-leaderboard work.

The ASE 2022 public evaluation materials have now been tested locally. That is an
exploratory evaluation of our existing analyzer against published labels; the original
published detector has not been rerun. The new explicit score-provenance API has not
been evaluated on those raw notebooks. Do not compare their scores as equal-input
methods.

## Closest systems and datasets

| Work | Established contribution | Boundary relevant to ResearchProof |
| --- | --- | --- |
| Yang et al., *Data Leakage in Notebooks: Static Detection and Better Processes* (2022) | Static analysis for common leakage patterns, evaluated across more than 100,000 public notebooks. | ResearchProof must not claim that static leakage detection or notebook-scale analysis is new. Its proposed comparison must test whether runtime lineage and executed repairs add value under held-out structures. |
| Drobnjaković, Subotić, and Urban, *Abstract Interpretation-Based Data Leakage Static Analysis* (2022; revised 2024) | A formal static analysis based on abstract interpretation, implemented in NBLyzer and evaluated on more than 2,000 Kaggle notebooks. | ResearchProof must compare against or carefully delimit formal/static lineage analysis. A bag-of-AST-calls baseline is not a sufficient technical contribution. |
| Truong et al., *LeakageDetector 2.0* (2025) | A VS Code extension targeting overlap, preprocessing, and multi-test leakage, with conventional quick fixes and LLM-guided correction. | Detection plus repair suggestions already exists. ResearchProof would need evidence that executable counterfactual verification, calibrated abstention, severity-controlled evaluation, or broader generalization testing is materially different. |
| Kapoor and Narayanan, *Leakage and the Reproducibility Crisis in Machine-Learning-Based Science* (2023) | Cross-disciplinary evidence of leakage-related reproducibility failures, an eight-part taxonomy, and model information sheets. | This establishes the importance and taxonomy of the problem. ResearchProof should align labels with it where possible and must not present the general motivation as new. |
| Drozdova et al., *Code4ML* (2022/2023) | A large corpus of annotated ML code drawn from Kaggle notebooks, suitable for code-understanding research. | Code4ML may support realistic source-template discovery, but its annotations are not automatically gold labels for methodological validity. Any reuse needs a license and label-quality review. |

## Candidate gap being tested

The current hypothesis is that three evidence sources may be more useful together than
alone:

1. source structure and approximate data flow;
2. runtime row/label lineage;
3. execution of a minimally repaired counterfactual pipeline.

The intended output is not merely a warning. It is a calibrated decision that may
abstain when evidence is incomplete, plus a repair whose effect can be checked under
the same task and split. Whether this combination is meaningfully different from the
systems above remains an empirical and literature-review question.

## Claims currently prohibited

Until the closest-work and experiments are stronger, project materials must not say:

- “the first data-leakage detector”;
- “the first automated repair system”;
- “the first AI system for trustworthy experiments”;
- “solves data leakage”;
- “generalizes to real-world notebooks”;
- “publication-ready” or “patentable.”

## Evidence needed for a defensible contribution

- A benchmark with independently authored pipelines and blinded validity labels.
- Dataset-, author-, template-, and fault-family-level holdouts.
- Credible reimplementations or runnable comparisons with the closest applicable work.
- Evidence that runtime or counterfactual components add value beyond a strong static
  analyzer.
- False-alarm analysis on valid but suspicious-looking pipelines.
- Calibration and selective-risk evaluation, not only classification accuracy.
- Reproducible failure analysis and compute-cost reporting.
- A repeated search of papers, software repositories, and relevant patents before
  drafting novelty language.

## Verified references

1. Chenyang Yang, Rachel A. Brower-Sinning, Grace A. Lewis, and Christian Kästner.
   “Data Leakage in Notebooks: Static Detection and Better Processes.” 2022.
   <https://arxiv.org/abs/2209.03345>
2. Filip Drobnjaković, Pavle Subotić, and Caterina Urban. “Abstract
   Interpretation-Based Data Leakage Static Analysis.” 2022; revised 2024.
   <https://arxiv.org/abs/2211.16073>
3. Owen Truong, Terrence Zhang, Arnav Marchareddy, Ryan Lee, Jeffery Busold, Michael
   Socas, and Eman Abdullah AlOmar. “LeakageDetector 2.0: Analyzing Data Leakage in
   Jupyter-Driven Machine Learning Pipelines.” 2025.
   <https://arxiv.org/abs/2509.15971>
4. Sayash Kapoor and Arvind Narayanan. “Leakage and the Reproducibility Crisis in
   Machine-Learning-Based Science.” *Patterns* 4 (2023), 100804.
   <https://doi.org/10.1016/j.patter.2023.100804>
5. Anastasia Drozdova, Polina Guseva, Ekaterina Trofimova, Anna Scherbakova, and
   Andrey Ustyuzhanin. “Code4ML: a Large-Scale Dataset of Annotated Machine Learning
   Code.” 2022/2023. <https://arxiv.org/abs/2210.16018>
