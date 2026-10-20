# What you and your friend can do before Kaggle works

We need to know whether short code snippets contain enough information for a
person to judge data leakage. Leakage means that information from evaluation data
influences fitting, feature selection, preprocessing or model selection in a way
that makes the reported evaluation unreliable.

Twenty cases are already frozen. Their original sources must stay unchanged.
This is a label-feasibility pilot on an explored split, not a new confirmation
dataset or proof that the published labels are wrong.

## Review independently

- You complete `artifacts/pilot_review_v1/reviewer_a.json`.
- Your friend completes `artifacts/pilot_review_v1/reviewer_b.json`.
- Read the code and form your own judgment before discussing individual cases.
  Do not inspect model predictions or the other person's verdicts first.
- Do not replace the human judgments with AI-generated answers. Assistance with
  learning Python is different from claiming an AI-generated verdict is independent
  human annotation. Record assistance in your research notes if you use it.

Each JSON packet contains `cases`. For each case, edit only its answer fields:

| Field | What to enter |
| --- | --- |
| `verdict` | `leakage`, `no_observed_leakage`, or `insufficient_context` |
| `fault_lines` | A list of 1-based source line numbers supporting observed leakage |
| `reason` | Your own concise explanation of the decision |
| `missing_context` | What you need to inspect when the verdict is `insufficient_context` |
| `reviewer` | Your stable name or identifier, different for the two packets |
| `reviewed_at` | The actual review time in ISO format with timezone, e.g. `2026-10-20T15:30:00+05:45` |

Leave a verdict `null` until you actually review it. Do not change `case_id`,
`source`, source fingerprints or the selected cases. For `leakage`, at least one
valid supporting line is required. Every completed verdict requires a reason,
reviewer and timezone-aware timestamp.

`no_observed_leakage` means you did not observe leakage in the supplied snippet;
it does not certify the whole notebook. Use `insufficient_context` when a missing
split, variable definition or earlier preprocessing step prevents a sound decision.
An unfamiliar library or a suggestive variable name alone is not enough evidence.
Do not execute downloaded code to decide the answer.

After both packets are completed, run this read-only comparison from the repository:

```bash
PYTHONPATH=src .venv/bin/python scripts/compare_pilot_reviews.py \
  --first artifacts/pilot_review_v1/reviewer_a.json \
  --second artifacts/pilot_review_v1/reviewer_b.json \
  --output artifacts/pilot_review_v1/agreement_after_human_review.json
```

The validator reports coverage even if work is incomplete. It reports agreement
only once both packets are complete. Discuss disagreements afterward and preserve
the two original decisions; record any later adjudication separately. Agreement
between two people is useful evidence, not automatic proof of correct labels.

For this paper, these reviews help determine whether snippet-level decisions are
well supported. A separately sampled confirmation corpus remains future work.
