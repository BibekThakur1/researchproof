# Research plan

## Problem statement

Machine-learning experiments can be methodologically invalid while remaining syntactically correct and fully executable. Existing linters, static analyses, notebook studies, and learned code detectors provide useful evidence, but a deployable research assistant must connect three questions: what the code appears to do, what the data actually did at runtime, and whether a corrected rerun changes the conclusion. The current pilot includes both row-contamination failures and the process-level failure of repeatedly tuning against the final test set.

## Proposed contribution

ResearchProof will study a hybrid auditing procedure built around three evidence channels:

1. **Structural evidence:** abstract syntax, API calls, operation order, and data-flow hints.
2. **Runtime lineage:** which samples and labels each operation observed and when model selection touched evaluation data.
3. **Counterfactual verification:** execute a minimally repaired pipeline and compare its behavior with the original run.

The contribution is not the existence of any one rule. The research question is whether their carefully evaluated combination detects faults more reliably, generalizes beyond authored templates, and produces repairs that can be verified rather than merely explained.

## Initial fault families

The benchmark will grow only after each injector is independently tested.

1. Exact train/test overlap.
2. Near-duplicate records crossing the split.
3. Preprocessing fitted before splitting.
4. Features derived directly or indirectly from the target.
5. Patient, user, device, or site groups crossing the split.
6. Future observations leaking into past-oriented evaluation.
7. Oversampling or augmentation before splitting.
8. Repeated tuning against the final test set.
9. Feature selection using all labels.
10. Reporting the best random seed without a predeclared selection rule.

## Evaluation principles

The benchmark unit is a paired clean/faulty pipeline created from the same dataset, task, model family, and seed. Fault injection should change one methodological decision whenever possible. Detector evaluation must split by complete dataset and pipeline-template families to prevent memorization. A leave-one-fault-family-out setting will test whether the system recognizes unseen kinds of failure.

Primary detector metrics are macro F1, per-fault recall, false-positive rate on clean pipelines, area under the precision-recall curve, expected calibration error, and selective risk when the detector may abstain. Repair evaluation records whether the corrected run removes the fault, remains executable, preserves the intended prediction task, and changes the reported score.

## Go/no-go gates

- **Gate 1:** At least four injectors create stable paired cases with deterministic manifests.
- **Gate 2:** Two independent reviewers agree on the fault label and repair for at least 90% of a pilot sample.
- **Gate 3:** A simple rule baseline leaves meaningful false positives or missed cases; otherwise a heavier detector is not justified.
- **Gate 4:** Runtime or counterfactual evidence adds measurable value on held-out templates.
- **Gate 5:** A second machine can reproduce the reduced primary result from a clean checkout.

Failure at a gate means revising or narrowing the question, not hiding the result.
