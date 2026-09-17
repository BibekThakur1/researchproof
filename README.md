# ResearchProof

ResearchProof is an experimental framework for studying a simple but serious question:

> Can a machine-learning workflow detect when its own reported performance is based on an invalid experimental procedure?

Many ML projects run without errors and still produce misleading results. Examples include fitting a transformer before the train/test split, allowing duplicate records to cross the split, selecting features with access to test labels, or repeatedly tuning against the final test set. ResearchProof will create controlled pairs of *clean* and *faulty* experiments, trace how data moves through each pipeline, and test whether static and runtime evidence can identify the fault and propose a verifiable repair.

This repository begins with a narrow, reproducible scope: tabular classification in Python using pandas and scikit-learn. We are deliberately not claiming a new universal detector. The first phase establishes whether the benchmark can be built reliably and whether the proposed hybrid detector improves on straightforward rules and code-only baselines.

## Current status

The [September 18 checkpoint](docs/progress_2026-09-18.md) adds a restricted
GridSearchCV capture adapter. Across 18 searches and 54 constructed report-origin
probes, it matches the library's choices but shows **no advantage over a simple
split-role baseline**. All 118 tests pass; external usefulness remains unproven.

See the [publication plan](docs/publication_plan.md) for the active paper scope,
required external evaluation, coauthor tasks, and submission criteria. The new
`scripts/run_persistence_pilot.py` tests saved evidence with actual model fits;
it remains a development experiment, not an external benchmark.

The [September 16 implementation checkpoint](docs/progress_2026-09-16.md) adds
versioned score-provenance persistence and separate-process regression checks.
All 108 tests pass; this is implementation validation, not new external accuracy evidence.

The latest [research report](docs/research_report_2026-09-13.md) documents three
exploratory studies: a runtime-feature information-loss diagnostic, 810 constructed
score-provenance cases, and an external audit of published ASE 2022 notebooks.
[Generated evidence and tables](results/2026-09-13/tables.md) include substantial
failures: the synthetic-trained AST model falsely flags 18 of 19 eligible clean
external notebooks. These results narrow the next research question to evaluation-
score provenance and instrumentation completeness. They do not establish a general
detector or publication readiness.

The project is at the benchmark-construction and external-validation stage. There are
development observations, but no frozen research results yet.

The smallest executable pilot compares two versions of the same classification experiment:

1. **Clean:** split the data first; fit preprocessing only on the training set.
2. **Faulty:** fit preprocessing on the complete dataset before splitting.

Both runs record their configuration, data fingerprints, scores, and runtime in machine-readable JSON. This gives us the smallest end-to-end unit needed for later auditing.

## Repository map

```text
configs/                 Experiment configuration
data/                    Data policy and local-cache guidance
docs/                    Research and benchmark specifications
paper/                   Manuscript outline and evidence-to-claim ledger
scripts/                 Commands used to reproduce experiments
src/researchproof/       Core Python package
tests/                   Unit tests for the benchmark machinery
.github/                 CI and issue templates
```

## Run the first pilot

Python 3.11 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python scripts/run_pilot.py --config configs/pilot.yaml
python scripts/generate_benchmark.py --config configs/benchmark_pilot.yaml
python scripts/evaluate_baselines.py \
  --index artifacts/benchmark_v0_4/runs.jsonl \
  --output artifacts/benchmark_v0_4/baselines.json
python scripts/verify_repairs.py \
  --config configs/benchmark_pilot.yaml \
  --output artifacts/benchmark_v0_4/repairs.json
python scripts/evaluate_learned.py \
  --index artifacts/benchmark_v0_4/runs.jsonl \
  --output artifacts/benchmark_v0_4/learned_baselines.json
python scripts/summarize_effects.py \
  --index artifacts/benchmark_v0_4/runs.jsonl \
  --output artifacts/benchmark_v0_4/paired_effects.json
python scripts/generate_source_pilot.py
python scripts/build_source_index.py \
  --contributions artifacts/contributions \
  --output artifacts/source_pilot_external/cases.jsonl
python scripts/evaluate_symbolic.py \
  --index artifacts/source_pilot_v0_1/cases.jsonl \
  --output artifacts/source_pilot_v0_1/symbolic_baseline.json
python scripts/export_blind_review.py \
  --source-index artifacts/source_pilot_external/cases.jsonl \
  --output artifacts/blind_review_v0_1 \
  --salt 'replace-with-private-random-text'
# After two independent reviewers complete separate CSV files:
python scripts/compare_reviews.py \
  --first artifacts/blind_review_v0_1/review_bibek.csv \
  --second artifacts/blind_review_v0_1/review_friend.csv \
  --output artifacts/blind_review_v0_1/agreement.json
python scripts/seal_artifacts.py artifacts/benchmark_v0_4
python scripts/seal_artifacts.py artifacts/benchmark_v0_4 --verify
# Normalize a Jupyter notebook using its recorded execution order:
python scripts/normalize_notebook.py notebook.ipynb \
  --ordering execution \
  --output artifacts/normalized_notebook.py
# Compare with a benchmark generated from a second checkout or laptop:
python scripts/compare_benchmarks.py \
  --reference artifacts/benchmark_v0_4/runs.jsonl \
  --candidate /path/to/second/checkout/artifacts/benchmark_v0_4/runs.jsonl \
  --output artifacts/reproduction_comparison.json
python scripts/check_release_readiness.py \
  --benchmark artifacts/benchmark_v0_4/runs.jsonl \
  --sources artifacts/source_pilot_v0_1/cases.jsonl \
  --agreement artifacts/blind_review_v0_1/agreement.json \
  --reproduction artifacts/independent_reproduction.json \
  --output artifacts/release_readiness.json
pytest
```

The commands write results beneath `artifacts/`. That directory is intentionally ignored by Git because generated runs should not be committed as source code. Benchmark version 0.4 creates 360 cases: clean and faulty variants for four fault families, three severity settings, three public scikit-learn datasets, and five seeds. The baseline report compares an always-clean baseline with simple operation-sequence and runtime-lineage rules. These are engineering-validation cases, not paper results. If the explicit rules solve them perfectly, that tells us the current benchmark is too transparent and must be made more realistic before training a detector. A paper-ready result will eventually be rebuilt from versioned configurations and a documented dataset manifest.

The separate source pilot contains 44 snippets, including twelve valid hard negatives
and helper-function cases that require interprocedural reasoning.
It reports both a naming-style holdout and a stricter structural-template holdout. The
latter is the meaningful development check; current results expose substantial
generalization failures and should guide the next feature and benchmark design.

## Research questions

The current focused questions and reproduction commands are in the
[September research report](docs/research_report_2026-09-13.md), with the
[experiment protocol](docs/selection_study_protocol.md) and
[working brief](docs/research_operating_brief.md). The original broader questions follow.

- **RQ1:** How accurately can different auditing methods identify methodological faults in executable ML pipelines?
- **RQ2:** Does combining source-code structure, data-lineage evidence, and counterfactual reruns outperform any single evidence source?
- **RQ3:** Can the system remain calibrated and useful on datasets, pipeline templates, and fault families that were not seen during detector development?
- **RQ4:** When ResearchProof recommends a repair, does executing the repaired pipeline remove the fault without silently changing the intended task?

## Research discipline

- Dataset and template families—not individual rows—will be separated across detector development and evaluation.
- Thresholds and model choices will be fixed using validation data only.
- Results will include false alarms, confidence calibration, failure cases, compute cost, and uncertainty—not only accuracy.
- Each main comparison will use repeated seeds and confidence intervals.
- We will not describe the system as novel or publishable until a closest-work review and experiments support that claim.

The maintained [closest-work map](docs/related_work.md) records what prior systems
already do and which claims are currently prohibited.

## Working together

Use an issue for every experiment or design decision. A pull request should state the hypothesis, changed files, exact reproduction command, and what evidence would disprove the claim. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Private research repository

This repository is private while the benchmark design is changing. Before public release, we will review dataset licenses, remove generated data that cannot be redistributed, write a model card/data card, and choose an appropriate software license.
