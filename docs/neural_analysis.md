# Analyze returned CodeBERT outputs

The existing private Kaggle ZIP remains usable; these analysis tools run locally
after the three output folders have been returned. No additional training is needed
merely to add this descriptive analysis.

Expected layout:

```text
artifacts/full_codebert/
  seed0/run.json, predictions.json, training.json, checkpoint/
  seed1/run.json, predictions.json, training.json, checkpoint/
  seed2/run.json, predictions.json, training.json, checkpoint/
  seed0.log, seed1.log, seed2.log
```

From the repository root:

```bash
.venv/bin/python scripts/analyze_codebert_study.py artifacts/full_codebert \
  --output results/codebert_three_seeds.json
```

The command requires all prespecified seeds, the full-training protocol and matching
source identities, labels, token-change flags, implementation and environment metadata.
It refuses existing output files. A failure means investigate and document the
difference, not edit metadata until the validator accepts it. Metadata consistency
does not by itself prove experimental integrity or annotation accuracy.

The report retains each seed's confusion counts and scores. Across-seed mean, sample
standard deviation and range summarize optimization variation, not uncertainty on
new projects. The 381 examples remain 381 distinct cases, not 1,143 independent cases.

For each edit, harmful/corrective rates use all eligible pairs as denominator.
The token-visible flip rate excludes unchanged token inputs; when no token input
changed, this rate is undefined (`null`), not zero. This prevents truncation from
being presented as evidence of learned invariance.

This is descriptive analysis of an already explored split. Repository-grouped
confirmation, appropriate paired uncertainty estimates, independent labels and
fair task-matched baseline comparison are still separate requirements. Test fixtures
are artificial software checks and must never be included in paper result tables.
