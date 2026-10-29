# Blinded notebook-context review: eight persistent misses

The local, ignored packet is
`artifacts/blind_miss_review_2026-10-27/packet.jsonl`; two blank independent
forms are beside it as `reviewer_a.csv` and `reviewer_b.csv`. The packet gives
the evaluated snippet, a public notebook URL when source-verified, and a
zero-based cell index. It deliberately omits published labels, model outputs,
and this project's preliminary AI-assisted interpretation. The separate
`review_key_keep_private.csv` must stay with a coordinator, not either reviewer.
**Do not commit or publish the packet without checking third-party data rights.**
The frozen packet SHA-256 is
`bf9486c329fc79e686165db1fd8b4ca58973b261168477f73394fcc1d4b8fe11`.
A more readable, equally blinded local rendering is
`artifacts/blind_miss_review_2026-10-27/packet_readable.md`. It contains the
same eight code blocks and notebook pointers, but no labels or predictions.
Each reviewer should read this file and fill only their own CSV.

Run `scripts/build_blind_miss_review.py` to rebuild the packet from the
canonical PeerJ test CSV and the [provenance audit](../results/2026-10-27/persistent_false_negative_audit.csv).
The script refuses to overwrite an existing packet. Its random review IDs
will differ on a fresh run; the stored key preserves this run's mapping.

## Frozen decision rule for this review

The question is whether information from a held-out evaluation set influences
model fitting, preprocessing parameters used in fitting, feature selection,
hyperparameter selection, or repeated selection of a reported result. Review
the entire relevant notebook data flow, not variable names or the target cell
alone. Distinguish held-out labels, held-out feature values/statistics, and
genuinely training-only information. An unsupervised transform fit on both
training and unlabeled competition test features is recorded as
`transductive_feature_use` **separately**; reviewers should explain whether it
violates the evaluation protocol rather than force it into the same category
as use of test labels. Execution order or missing input files may prevent a
conclusion.

Allowed `judgment` values:

- `confirmed_leakage`: the reviewed code shows evaluation information affecting
  training or model selection under the rule above.
- `no_leakage_in_recovered_workflow`: the relevant data path is present and
  respects the boundary.
- `insufficient_context`: source, split, execution order, or input provenance is
  missing.
- `ambiguous_or_disputed`: multiple defensible interpretations remain even
  with the available context.

For every case, record mechanism (including `transductive_feature_use` if
relevant), exact notebook cell indices or code lines, confidence
(`low`/`medium`/`high`), and a short rationale. If there is no recovered
notebook, **do not** infer a whole-workflow label from the snippet; mark
insufficient context unless the snippet alone unmistakably shows a boundary
crossing. Each reviewer completes all eight independently before viewing the
other form, published label, predictions, or the AI trace note. A coordinator
then preserves both initial forms, calculates raw agreement, and records
adjudication separately. Eight targeted positives are too small and selected
post hoc for a population label-quality estimate.

Human work remains genuinely required: the blank forms and my preliminary
trace cannot be represented as independent human validation.

## After both reviewers finish

Keep both original CSVs unchanged and run the comparison before discussing
disagreements. It checks the frozen packet hash, exactly eight distinct IDs,
allowed values, and that completed answers have evidence and rationale. It
reports coverage even when forms are incomplete; agreement is computed only
when both are complete. The report does not certify that the reviews were
independent or performed by humans.

```bash
PYTHONPATH=src .venv/bin/python scripts/compare_blind_miss_reviews.py \
  --packet artifacts/blind_miss_review_2026-10-27/packet.jsonl \
  --expected-packet-sha256 bf9486c329fc79e686165db1fd8b4ca58973b261168477f73394fcc1d4b8fe11 \
  --first artifacts/blind_miss_review_2026-10-27/reviewer_a.csv \
  --second artifacts/blind_miss_review_2026-10-27/reviewer_b.csv \
  --output artifacts/blind_miss_review_2026-10-27/agreement_after_review.json
```

Do not use the private review key or model outputs in this step. Only after
both original forms are frozen should a coordinator unblind case IDs and
record adjudication in a **separate** file. Cohen's kappa is reported for
completeness, but eight selected cases make it unstable; focus on the actual
case-level disagreements and explanations.
