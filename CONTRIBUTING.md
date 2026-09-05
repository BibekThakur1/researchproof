# Contributing to ResearchProof

This is a research codebase, so a change is not complete merely because the code runs.

## Before starting

Create an issue that records:

- the question being tested;
- the expected observation;
- what outcome would count against the hypothesis;
- the dataset, split policy, metric, and baselines;
- the files or modules expected to change.

## Branches and commits

Use a short branch name such as `benchmark/duplicate-leakage` or `audit/runtime-lineage`. Keep commits focused. Commit messages should explain the research change, for example:

```text
Add paired split-overlap benchmark case
Record lineage evidence for transformer fit calls
Test manifest stability across repeated seeds
```

## Pull-request checklist

- [ ] The experiment has a fixed configuration.
- [ ] Random seeds and dataset versions are recorded.
- [ ] Tests pass locally.
- [ ] Generated artifacts and datasets are not committed accidentally.
- [ ] The change does not report invented or preliminary numbers as findings.
- [ ] Documentation states any new assumption or limitation.
- [ ] The pull request includes an exact reproduction command.

## Result handling

Never edit result JSON or tables by hand. If a run is invalid, preserve the log, mark the reason, and rerun under a new run identifier. Paper tables should eventually be generated from validated artifacts by script.

