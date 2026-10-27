# Blinded notebook-context review: eight persistent misses

The local, ignored packet is
`artifacts/blind_miss_review_2026-10-27/packet.jsonl`; two blank independent
forms are beside it as `reviewer_a.csv` and `reviewer_b.csv`. The packet gives
the evaluated snippet, a public notebook URL when source-verified, and a
zero-based cell index. It deliberately omits published labels, model outputs,
and this project's preliminary AI-assisted interpretation. The separate
`review_key_keep_private.csv` must stay with a coordinator, not either reviewer.
**Do not commit or publish the packet without checking third-party data rights.**

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
