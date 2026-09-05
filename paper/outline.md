# ResearchProof manuscript outline

This is a writing scaffold, not a completed paper. Bracketed fields remain empty until
the corresponding frozen experiment has been run.

## Working title

**ResearchProof: Evaluating Hybrid Static, Runtime-Lineage, and Counterfactual Auditing
of Machine-Learning Experiments**

The title should change if the eventual contribution is narrower.

## Abstract structure

1. **Problem:** Executable ML pipelines can produce misleading evaluations despite
   running without errors.
2. **Gap:** State what the final closest-work review shows is not adequately evaluated.
3. **Method:** Describe only components present in the released artifact.
4. **Evaluation:** Insert frozen benchmark size, partitions, baselines, and uncertainty
   protocol.
5. **Results:** Insert effect sizes and confidence intervals from generated tables.
6. **Limitations:** Name unsupported libraries, fault families, and external-validity
   limits.

Do not write the numerical result sentences before the release gate passes.

## 1. Introduction

- Explain methodological validity failures without implying that every leakage event
  increases accuracy.
- Motivate verification using documented reproducibility failures.
- State three research questions.
- List contributions conservatively and distinguish benchmark, mechanism, and
  empirical findings.

## 2. Background and related work

- Leakage taxonomies and reproducibility.
- Static notebook leakage detection.
- Abstract-interpretation and provenance analyses.
- Developer tools and automatic correction.
- ML-code corpora and learned code analysis.
- Calibration, abstention, and distribution shift where directly relevant.

The section must be based on `docs/related_work.md` and a repeated search performed
near submission.

## 3. Problem formulation

- Define a pipeline, data partitions, observed row sets, and a validity fault.
- Define the detector outputs: fault probability, evidence, action, and abstention.
- Define counterfactual repair verification.
- State what the system cannot prove.

## 4. Benchmark construction

- Dataset selection and checksums.
- Clean/faulty pairing.
- Severity definition.
- Source-template and hard-negative construction.
- Independent authorship and blinded annotation.
- Dataset, template, author, and fault-family partitions.
- Threats from duplicated clean controls and synthetic injectors.

## 5. Methods

### 5.1 Rule baselines

Always-clean, sequence rules, and runtime-lineage rules.

### 5.2 Learned baselines

Static, runtime, and hybrid sparse logistic-regression models.

### 5.3 Symbolic provenance

Direct assignment tracking and function summaries. Clearly distinguish this limited
implementation from formal abstract interpretation.

### 5.4 Uncertainty and selective action

Ordinary confidence and feature-support adjustment are negative baselines. The final
method belongs here only after it improves preregistered selective-risk criteria.

### 5.5 Counterfactual repair

Explain task/split preservation, rerun isolation, and verification conditions.

## 6. Experimental protocol

- Frozen configurations and dependency lock.
- Baseline reproduction.
- Leave-one-dataset, template, author, and fault-family tests.
- Metrics and confidence intervals.
- Ablations and robustness cases.
- Compute and runtime accounting.
- Multiple-comparison correction if several hypotheses are tested.

## 7. Results

Generate, do not hand-edit:

- Table 1: benchmark composition.
- Table 2: in-distribution and held-out performance.
- Table 3: false alarms on hard negatives.
- Table 4: calibration and selective risk.
- Table 5: component ablations.
- Table 6: repair success and semantic-preservation review.
- Figure 1: architecture.
- Figure 2: risk-coverage curves.
- Figure 3: fault-severity versus paired score difference.

## 8. Failure analysis

- False positives grouped by valid pattern.
- False negatives grouped by data-flow construct.
- Confident errors under unseen fault families.
- Repair failures and changed task semantics.
- Cases with reviewer disagreement.

## 9. Threats to validity

- Construct validity of injected faults.
- Internal validity and shared clean controls.
- External validity beyond scikit-learn tabular classification.
- Label reliability and author recognition.
- Dataset and template leakage across evaluation partitions.
- Researcher degrees of freedom during iterative benchmark development.

## 10. Ethics and responsible release

- No use as a developer-quality score or automatic scientific certificate.
- Dataset and source license review.
- Safe execution of untrusted notebooks.
- Disclosure of abstention and unsupported cases.

## 11. Conclusion

State only findings supported by frozen artifacts. Emphasize remaining failure modes
and the next research question rather than claiming the general problem is solved.

