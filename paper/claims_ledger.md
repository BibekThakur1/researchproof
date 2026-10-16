# Evidence-to-claim ledger

Every empirical statement in the manuscript must have an evidence owner and a release
gate. “Current status” refers to development evidence and may change.

## October 3: active robustness study

October 16 addition: `results/2026-10-16/token_visibility.json` establishes that
9/340 appended-comment pairs have identical tokenized model inputs at a 512-token
limit. This permits a preprocessing-exposure statement only; it does not establish
detector performance, prevalence outside this corpus, novel algorithms or invention.
See `docs/research_direction_2026-10-16.md` for the new measured diagnostic and
falsifiable contribution hypothesis.

| Claim | Evidence or missing artifact | Current permitted interpretation |
| --- | --- | --- |
| Lexical models show surface sensitivity | `results/2026-09-20/robustness_pilot.json` | Exploratory finding about two local models; count corrective as well as harmful flips. |
| Current MLScent has coverage limits and a specific warning failure | `results/2026-09-26/mlscent.json`, executable control and replication report | Pinned current implementation only; not historical replication or population prevalence. |
| CodeBERT training code executes | `results/2026-09-29/neural_validation.json` | Engineering checks on tiny samples, not held-out detector performance. |
| Full neural results exist | Three completed validated seed runs missing | Not permitted. |
| Human labels agree | `results/2026-10-03/review_readiness.json`: 0/20 verdicts per reviewer | Not permitted; agreement remains undefined until review completes. |
| The study provides a new evaluation contribution | `docs/literature_update_2026-10-03.md`, full-paper comparison and confirmation still needed | Candidate hypothesis only; broad metamorphic testing is established. |
| Generalization or submission readiness | Frozen separate corpus, reviewed labels, independent reproduction and final author review missing | Not permitted. |

## September 13 evidence update

The [current report](../docs/research_report_2026-09-13.md) supersedes broad
interpretations of the earlier engineering findings. Supported development statements:

- Boolean runtime features impose a measured 87.5% accuracy ceiling on the 360-case
  finite dataset; log-count encoding improves dataset-holdout F1 but unseen-fault F1
  remains zero for the runtime model.
- A constructed score-provenance study yields the expected API behavior and
  counterexamples to the local count heuristic. It is not a published-tool comparison.
- On published external notebook labels, the old symbolic analyzer has poor recall.
  The synthetic-trained AST model's F1 of 0.8125 accompanies 94.7% false positives.
- External published labels are now available; they are not a new human review of
  our constructed score-provenance cases, nor evidence of independent-machine reproduction.

Novelty, automatic instrumentation, arbitrary-code repair, and publication readiness
remain unestablished. The original ledger below is retained as development history.

| Candidate claim | Required evidence | Current status | Allowed now? |
| --- | --- | --- | --- |
| The benchmark is reproducible | Pinned clean checkout plus second-machine semantic comparison | Same-machine comparison passes; second machine missing | No |
| Labels are reliable | Two complete blinded reviews, agreement statistics, and written adjudication | Review forms missing | No |
| Source evaluation generalizes across authors | At least two independent authors and author-level holdout | One source author | No |
| Static analysis handles direct and simple helper flows | Frozen external source set and comparison with strong static baseline | Self-authored pilot passes | Development statement only |
| Learned detector generalizes across datasets | Frozen dataset-level holdout with confidence intervals | Engineering holdout passes on transparent traces | No |
| Learned detector generalizes to unseen fault mechanisms | Leave-one-fault-family-out evaluation | Runtime F1 is 0.000; static/hybrid aggregate F1 is 0.333 with three of four held-out families at F1 0.000 | May report only as a negative development result |
| Confidence enables safe abstention | Risk decreases materially as coverage falls under shift | Ordinary and support-aware confidence fail | No |
| Counterfactual repair is reliable | Executable repairs plus independent semantic-preservation review | Mechanical checks pass; semantic review missing | No |
| Hybrid evidence improves over static analysis | Preregistered paired comparison against credible static, runtime, and learned baselines | Not yet established | No |
| ResearchProof is novel | Updated systematic closest-work and patent search plus defensible difference | Preliminary closest-work map only | No |

## Rule for changing status

A claim moves to “allowed” only when the generating command, configuration, immutable
artifact, statistical analysis, and limitation text are linked in the same pull
request. A higher score alone is insufficient.
