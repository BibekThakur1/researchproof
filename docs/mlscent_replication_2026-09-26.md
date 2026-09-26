# Pinned MLScent evaluation: coverage, stability, and a complete failure witness

## What was run

We ran the actual upstream MLScent implementation, not a locally rewritten detector.
Repository: https://github.com/KarthikShivasankar/ml_smells_detector
Revision: `c22cb3ad5fd2927434dcb77c1f9ce475e44d7cb4` (2026-05-31).
Related publication: [Shivashankar and Martini, MLScent, CAIN 2025](https://arxiv.org/abs/2502.18466).

This revision postdates the paper. These are new experiments with a pinned current
implementation, **not reproduction of the historical paper's scores**. The upstream
checkout was unmodified. Its tests produced 212 passes and one skip. The isolated
environment uses Python 3.13.0 and astroid 3.3.11; other packages are pinned separately.
Core project dependencies were not changed.

CodeBERT training remains unfinished. Docker's daemon was unavailable and the disk
reported roughly 12 GiB available, so this checkpoint used a lightweight CPU baseline
rather than installing a large neural stack or starting a paid cloud job.

## Protocol and mapping

We invoke `ML_SmellDetector.detect_smells` and
`FrameworkSpecificSmellDetector.detect_smells` on temporary UTF-8 Python files.
The general component's warnings containing "data leakage" and the framework
component's exact `Data Leakage Checker` category count as positive evidence.
Other code smells do not count as leakage.

Upstream sometimes returns an empty list after reporting a skip or caught error.
The adapter records these as unknown, not clean. A combined positive requires a
positive component; a combined negative requires both components to answer negative.
Other cases remain unknown. Raw component statuses are retained in the result file.
The analyzed programs are parsed, never imported or executed.

Inputs total 1,933: 381 original PeerJ test snippets, 1,360 AST-preserving edits,
100 normalized ASE notebooks, 88 authored controls with/without an import context,
two short sanity probes and two complete-control stages. These are **not 1,933
independent workflows**. Variants and controls are development examples.

The PeerJ labels cover any data leakage, whereas MLScent's inspected checks have
narrower scope. ASE comparisons use its preprocessing label only. Neither corpus
has been relabeled to exactly match MLScent's intended contract, so report these as
label-agreement diagnostics with coverage, not a fair overall ranking against
learned models. ASE notebooks were already used in earlier exploratory work and
are not an unseen confirmation set.

## Observed results

| Corpus | Inputs | Explicit labels | Answered with label | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PeerJ original snippets | 381 | 381 | 31 | 2 | 3 | 25 | 1 |
| ASE normalized notebooks, preprocessing label | 100 | 66 | 58 | 4 | 3 | 36 | 15 |
| Authored source controls, as-is | 44 | 44 | 0 | 0 | 0 | 0 | 0 |
| Authored controls with explicit sklearn import | 44 | 44 | 44 | 0 | 0 | 28 | 16 |

For PeerJ, each component reports 309 no-import skips, 41 errors, and 31 checked
inputs. This is a compatibility/coverage finding; do not count 350 unanswered cases
as false negatives or correct negatives. On ASE there are 83 answered notebooks
overall, but only 58 have explicit preprocessing labels. The denominator for labeled
coverage is 66, not 100. Normalization failures and detector errors remain in the
100-row inventory. Notebook magics are commented and document order is used, which
can differ from actual execution order.

All four PeerJ edit conditions have 340 paired inputs, but only 31 pairs are answered
at both endpoints. There are zero prediction flips among those answered pairs.
This illustrates why invariance must be accompanied by coverage and fault sensitivity.
It does not establish neural understanding or superiority of this static tool.

Adding `import sklearn` to authored controls is explicitly an adapted input condition.
We do not add imports to the public snippets or treat this intervention as a repair.

## Executable failure witness

`examples/mlscent_preprocessing_control.py` intentionally fits a scaler on all 178
wine-dataset rows before creating a training split of 124 rows. In both the prefix
and complete program, the scaler's recorded fitted sample count remains 178.
Appending the final DecisionTreeClassifier fit does not undo preprocessing exposure.

The general MLScent component warns on the prefix but not on the complete program;
the framework component is negative in both. Source inspection explains the result:
the general rule retains the line number of the last `fit`/`fit_transform` call and
compares it to the split line. A later model fit replaces the earlier preprocessing
position. This is a narrowly demonstrated failure of this pinned implementation.
It does not estimate the frequency or numerical impact of such failures in real
projects. Only this authored example is executed locally; external notebooks are not.

## Reproduction

From the research repository root, after the standard environment setup:

```bash
.venv/bin/python scripts/fetch_peerj_materials.py
.venv/bin/python scripts/fetch_ase22_materials.py
git clone --no-checkout https://github.com/KarthikShivasankar/ml_smells_detector.git artifacts/mlscent_source
git -C artifacts/mlscent_source checkout --detach c22cb3ad5fd2927434dcb77c1f9ce475e44d7cb4
.venv/bin/python -m venv artifacts/mlscent_env
artifacts/mlscent_env/bin/python -m pip install -r requirements-mlscent.txt
PYTHONPATH=artifacts/mlscent_source artifacts/mlscent_env/bin/python -m pytest artifacts/mlscent_source/tests -q
.venv/bin/python scripts/prepare_mlscent_inputs.py
artifacts/mlscent_env/bin/python scripts/run_mlscent_baseline.py
.venv/bin/pytest -W error
.venv/bin/ruff check .
```

Do not clone again if the target already exists. The runner rejects a wrong revision
or dirty upstream checkout. Preparation checks cached data fingerprints. No downloaded
corpus code is executed, and raw notebooks/snippets remain ignored artifacts. The
committed result is `results/2026-09-26/mlscent.json`.

Validation completed: 146 project tests pass with warnings treated as errors; lint
passes. Two finalized runs yielded byte-identical results with SHA-256
`e8fb6c9241333f66f8b393c8c3b087f4e8953340830928f92e996577381f92d4`.
This is repeatability on one machine, not independent replication.

## Submission impact and next steps

We now have a working paper-linked static baseline and an executable failure witness.
This strengthens the artifact but does not finish the paper. The next comparison
must use reviewed, task-matched examples with complete context, plus an actual
reproduced neural baseline. The 20-snippet human-review packets remain necessary to
learn whether independent reviewers can label these examples at all.

Do not claim the broad title "AI detectors do not understand code" from these results.
A more supportable potential contribution is a coverage-aware, paired evaluation of
methodology-checking tools. It becomes a research paper only if independent evidence,
literature comparison and fair baselines establish its value.
