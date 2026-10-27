# Human review for the completed CodeBERT experiment

The 24-case packet is **post-hoc targeted error analysis**, not an unbiased
confirmation set. It includes eight examples missed by all three seeds and
16 examples with at least one edit-induced prediction flip. Which anonymous
case belongs to which group is stored in a separate local selection file.
The packet contains no model predictions or published labels. The original
20-case random pilot in `docs/HUMAN_REVIEW_NEXT.md` remains separate and
must not be replaced by these targeted cases.

Local files, deliberately excluded from Git because they contain third-party
source snippets and private human judgments:

- `artifacts/targeted_review_v1/reviewer_a.json`
- `artifacts/targeted_review_v1/reviewer_b.json`
- `artifacts/targeted_review_v1/selection_private.json` — **do not send to reviewers**

You and your friend should each complete one packet independently. Do not
inspect the selection key, published labels, model outputs, or each other's
answers first. Put your actual reviewer identity and review time in each
completed row. Valid verdicts are `leakage`, `no_observed_leakage`, and
`insufficient_context`; explain each decision in your own words. Record
1-based supporting lines for a `leakage` verdict. Use `insufficient_context`
when the code snippet does not show enough of the pipeline to decide. A human
review cannot be replaced with AI-generated verdicts while claiming independent
human annotation.

After **both** reviewers finish, run:

```bash
PYTHONPATH=src .venv/bin/python scripts/compare_targeted_reviews.py \
  --first artifacts/targeted_review_v1/reviewer_a.json \
  --second artifacts/targeted_review_v1/reviewer_b.json \
  --selection artifacts/targeted_review_v1/selection_private.json \
  --data artifacts/peerj2025/test_annotated.csv \
  --output artifacts/targeted_review_v1/agreement_after_review.json
```

The comparison validates source integrity and reports coverage before it
computes agreement. Its report does not certify human independence. Retain
both original packets, then discuss disagreements and record adjudication
separately. Only after both reviews may the selection key and model outputs be
examined to characterize failure mechanisms. Do not revise the paper's labels
silently. The manuscript still requires an untouched external corpus.
