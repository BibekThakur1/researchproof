# ResearchProof benchmark card

## Version

Development version 0.3. This is not a frozen public release.

## Purpose

The benchmark supports controlled research on detecting methodological faults in
tabular machine-learning experiments. Each executable case has a clean counterpart,
a faulty counterpart, a content-addressed manifest, runtime evidence, and an intended
repair. The present version validates infrastructure and experimental protocols; it
does not represent the diversity of real notebooks.

## Current composition

- Three datasets bundled with scikit-learn: breast cancer, wine, and digits.
- Three fault families: preprocessing before splitting, train/test overlap, and
  target-informed feature selection.
- Three contamination levels: low (about 2% of test rows), medium (about 10%), and
  high (100%).
- Five fixed train/test seeds.
- 270 executable runs: 135 clean controls and 135 faulty variants.
- 36 static source snippets: 24 paired examples and twelve valid hard negatives.

The clean run is repeated across related severity contrasts. Analyses must recognize
that these controls are correlated and must not count them as independent evidence.

## Label meaning

`expected_fault=true` means that a predefined methodological validity rule was
intentionally violated by the injector. It does not mean that predictive accuracy
must increase. A faulty pipeline may show little or negative score change on a
particular dataset and split.

## Generation

The executable cases are generated from `configs/benchmark_pilot.yaml`. Case IDs are
derived from canonical manifests containing the dataset checksum, template version,
fault family, severity, injector version, split policy, model configuration, and
expected evidence. Generated artifacts can be sealed with SHA-256 checksums.

## Evaluation partitions

Current executable learned baselines leave one complete dataset out. The source pilot
reports two protocols:

- leave one naming style out;
- leave one complete structural template out.

The structural holdout is the more meaningful test. Future releases must additionally
hold out authors and fault families.

## Intended uses

- Developing static and runtime auditing methods.
- Testing whether counterfactual repair verification adds useful evidence.
- Studying calibration, abstention, and false alarms under controlled faults.
- Teaching rigorous ML evaluation when the limitations are explained.

## Uses that are not supported

- Claiming real-world leakage prevalence.
- Judging the quality or intent of individual developers.
- Certifying that an arbitrary experiment is scientifically valid.
- Training a production detector without broader independently labeled data.
- Claiming that high pilot accuracy establishes novelty or publication readiness.

## Known limitations

- The source templates have one author and share substantial structure. Helper-function
  cases expose the current analyzers' lack of interprocedural reasoning.
- Operation traces in the executable benchmark expose the injected mechanism.
- Only scikit-learn tabular classification is represented.
- Current datasets are small and bundled for convenience rather than chosen through a
  preregistered sampling plan.
- Several validity failures, including group leakage, temporal leakage, repeated test
  tuning, and seed cherry-picking, are not implemented.
- No independent human annotation or independent-machine reproduction is complete.
- The AST baseline uses shallow call features rather than program semantics.

## Development observations

The explicit trace-based baselines solve the executable pilot, demonstrating that it
is too transparent. In the source pilot, naming-style holdout is also solved, while
structural-template holdout performs substantially worse. Severity-controlled score
differences increase on average, but remain small in the current datasets. These are
development observations and are not frozen research findings.

## Release gate

A public benchmark release requires:

1. two independent blinded reviewers;
2. documented adjudication and agreement;
3. independently authored source templates;
4. dataset and source-code license review;
5. author-, dataset-, template-, and fault-family-level partitions;
6. a second-machine reproduction report;
7. a changelog and immutable version identifier;
8. a completed closest-work update.
