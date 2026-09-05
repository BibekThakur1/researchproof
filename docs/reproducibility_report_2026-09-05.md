# Clean-checkout reproducibility report — 5 September 2026

## Scope

This check used a new temporary clone of the private GitHub repository on the same
Apple Silicon computer. It verifies that the repository is self-contained and that
its pinned environment can regenerate the benchmark. It is not an independent-machine
replication.

## Procedure

1. Clone `https://github.com/BibekThakur1/researchproof.git` into a new empty directory.
2. Create a new Python virtual environment.
3. Install every dependency from `requirements-lock.txt`.
4. Install ResearchProof in editable mode without resolving additional dependencies.
5. Run Ruff.
6. Run the complete test suite with warnings treated as errors.
7. Generate benchmark version 0.3 from `configs/benchmark_pilot.yaml`.
8. Compare the original and new `runs.jsonl` files by content-addressed case ID.

## Evidence

- Ruff: passed.
- Tests: 60 passed.
- Original cases: 270.
- Clean-checkout cases: 270.
- Missing case IDs: 0.
- Unexpected case IDs: 0.
- Changed scientific records: 0.
- Comparison result: reproduced.

The comparator ignores only `runtime_seconds`, because elapsed time is expected to
change between executions. It requires dataset IDs, fault families, severity,
operation traces, row-split hashes, evidence, model-fit row counts, and predictive
metrics to match exactly.

## Remaining requirement

The second researcher must repeat this process on their own laptop. Differences must
be investigated rather than rounded away. The resulting comparison JSON and package
versions should be retained as research artifacts before the benchmark is frozen.

