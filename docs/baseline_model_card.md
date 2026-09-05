# Baseline model card

## Models

ResearchProof currently includes three learned logistic-regression baselines:

- static operation and transition features;
- binary runtime-lineage evidence;
- the union of static and runtime features.

A separate source pilot uses logistic regression over shallow AST call and call-pair
features. These models were selected for interpretability and low compute cost, not
because they are expected to be state of the art.

The repository also includes a deterministic symbolic provenance baseline. It tracks
whether transformed unsplit values or held-out rows flow into model fitting and stops
treating later full-data fitting as leakage once the recorded evaluation is complete.
This is an engineering reference implementation, not a new formal static-analysis
claim; prior abstract-interpretation systems are substantially more rigorous.

## Training and evaluation

Executable baselines use both leave-one-complete-dataset-out and
leave-one-complete-fault-family-out evaluation. The source baseline uses naming-style
and structural-template holdouts. Gold labels, predictive
scores, case IDs, dataset IDs, and fault-family names are excluded from input
features. The current source corpus is too small for hyperparameter searching.

Current learned baselines fail completely to recognize a held-out fault family. This
is expected from sparse mechanism-specific features and is a central negative result
for development, not a reason to tune on the test folds.

## Metrics

Reports include confusion counts, accuracy, precision, recall, F1, false-positive
rate, Brier score, and expected calibration error where probabilities are available.
Selective-risk curves report coverage versus error after ranking predictions by model
confidence. Current fault-family holdout results show that abstention based on ordinary
logistic-regression confidence can retain the wrong cases, so confidence must not be
treated as uncertainty under distribution shift.

## Limitations

The executable evidence fields directly describe contaminated row access, making
those baselines sanity checks rather than realistic detectors. The symbolic source
baseline tracks direct assignments and simple single-return helper summaries, but not
nested calls, branches, loops, mutation, closures, or imported functions. None of the
models should be deployed or described as a validity certificate.

## Compute

All current baselines run on CPU and are suitable for an Apple M1 laptop. No GPU,
external model API, or proprietary dataset is required.
