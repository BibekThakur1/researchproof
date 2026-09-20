# What is finished, what you should do, and what blocks submission

## Read first

The manuscript is `paper/robustness_pilot_draft.md`. It is an honest technical-report
draft with measured pilot results, not a publishable-paper certificate. The active
direction is evaluating detector robustness, not claiming the earlier provenance
adapter is a new algorithm. Historic results remain available for traceability.

## Finished in this checkpoint

- Downloaded checksum-verified public dataset and code artifacts from Figshare.
- Inspected training code as text; did not execute third-party scripts or call APIs.
- Trained two local TF–IDF classifiers on 1,523 published training snippets.
- Evaluated 381 test snippets, including 340 with four AST-preserving edits each.
- Added constant controls, overlap diagnostics, paired error-direction counts, and
  separate authored fault-pair checks. No test examples were used to fit these models.
- Wrote a draft with methods, tables, interpretations, limitations and references.
- Prepared two unfilled review packets. These are not completed human reviews.

Validation: 135 tests pass with warnings treated as errors; lint passes. Two
consecutive runs of the finalized evaluator produced the same result-file SHA-256:
`14af036f2d5a6e4e5e5ea3162803c29a0cf048817a1561c638008f131ab2ab65`.
This is same-machine repeatability, not independent reproduction.

The raw public files are ignored artifacts. Result records contain IDs, hashes and
predictions, not redistributed source. Downloaded archive code is never imported.

## Reproduce on your friend's M1

Use the existing setup instructions in README to create the environment from the
lockfile. Run from the repository root, preserving any installation errors:

```bash
.venv/bin/python scripts/fetch_peerj_materials.py
.venv/bin/python scripts/evaluate_robustness_pilot.py
.venv/bin/pytest -W error
.venv/bin/ruff check .
.venv/bin/python scripts/export_pilot_review.py
```

Record Python/scikit-learn versions, commit ID, commands, completion time and failures.
Compare per-case predictions and counts, not just a screenshot. Environment versions
may change the full JSON hash; numerical differences require investigation.

## Your first task: review 20 snippets each

Open `artifacts/pilot_review_v1/reviewer_a.json`; give the other file to your friend.
Do not read detector outputs or published labels during this review. Each of you
fills verdict, fault lines, reason, missing context, reviewer and reviewed_at.
Do not force a binary label when the snippet lacks necessary context. Work separately
before discussing disagreements. These snippets are sampled by hash, not selected
because a model failed. This is a label-feasibility pilot, not a representative new
benchmark or a confirmation study. Do not commit raw snippets without license review.

After both files are finished, compare agreements and disagreements, adjudicate with
written reasons, and preserve the original independent files. Existing annotation
utilities may need a format adapter; no agreement percentage is claimed yet.

## Published-baseline reproduction: still technical work, not your paperwork

The downloaded AL4Code archive has CodeBERT training code, not a supplied trained
checkpoint. Its stated dependencies are older than this project's environment.
Training and validating a compatible reproduction remains unfinished. Kaggle compute
can help, but its session availability and account access were not verified here.
Do not substitute these TF–IDF numbers for the published results.

The archive's optional augmentation calls a paid model API. It was not enabled.
Reproduction must distinguish exact historical reproduction (possibly unavailable)
from a documented modern reimplementation and a no-augmentation ablation.

A source-inspection concern needs checking: `AL4Code/demo.py` computes test F2 and
uses that metric in the active-learning stopping comparison at lines 91–113 of the
downloaded version. This observes a code path, not which options produced any paper
table or how much bias it caused. Validate the path and paper protocol before making
public claims; retain a fixed-budget or validation-only stopping comparison in any
reimplementation. No allegation or quantitative inflation claim is justified here.

## Evidence still required before a research submission

1. Reproduce at least one relevant published detector, plus a compatible static
   baseline, with saved configurations and fair category mappings.
2. Human-review fault-changing pairs. The current sixteen pairs are authored source
   controls, not executable, externally validated clean programs.
3. Locate full-workflow origins or collect a separately frozen corpus; group related
   repositories/authors across partitions. Published snippet IDs alone cannot do this.
4. Freeze edit families, metrics and baseline settings before confirmation. The
   currently explored test split must not be relabeled an unseen confirmation set.
5. Add scope-safe naming transformations only after verification. Comment changes
   alone are insufficient evidence of a general semantic-understanding failure.
6. Analyze paired uncertainty by original workflow and report exclusions/coverage.
7. Finish second-machine reproduction and obtain critical human technical feedback.
8. Reassess novelty, select a suitable current call, then finalize formatting,
   anonymity, references, AI-assistance disclosure and author contributions.

If stronger baselines do not show a meaningful issue, or the relevant evaluation
already exists, narrow or stop the claim. More variants of one example do not create
independent evidence. Publication cannot be guaranteed by completing a checklist.

## Ownership

Codex can assist code, tests, data inventories, evaluation, analysis and drafting.
You and your friend must supply genuine human judgments, account/compute decisions,
independent execution, technical understanding, authorship approval and submission.
Do not list experiments, review or publications on a CV before they actually happen.
