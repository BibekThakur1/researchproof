# Two-person research workflow

Both researchers should understand the complete system. Ownership below prevents duplicated effort, but neither person should become the only one able to reproduce a result.

## Suggested starting ownership

### Researcher A — benchmark and reproducibility

- dataset manifests and checksums;
- clean pipeline templates;
- fault injectors and invariant tests;
- experiment configurations;
- artifact validation and result-table generation.

### Researcher B — auditing and evaluation

- static rules and AST features;
- runtime-lineage instrumentation;
- baseline detector implementations;
- calibration and statistical evaluation;
- error analysis and counterfactual repair checks.

Switch reviewer roles for each pull request. The author of an injector must not be the only person who validates its expected label.

## First working session

1. Clone the private repository.
2. Create a virtual environment and install the project.
3. Run the pilot and tests independently.
4. Compare the five clean/faulty run pairs without treating their score difference as a research result.
5. Each person writes what they believe the fault is and what evidence an auditor would need.
6. Open one GitHub issue for the benchmark manifest and assign an owner.
7. Agree on two fixed weekly meeting times.

## Evidence rule

No statement enters the paper as a finding unless it is linked to:

- a commit;
- a versioned configuration;
- a dataset manifest;
- an immutable run artifact;
- a script that generates the reported number or figure;
- an experiment-log entry describing unexpected behavior.

## Communication rule

Use GitHub issues for technical decisions. Chat is useful for discussion but is not the research record. Summarize the final decision and its reasoning in the relevant issue before closing it.

