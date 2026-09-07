# Evidence-to-claim ledger

Every empirical statement in the manuscript must have an evidence owner and a release
gate. “Current status” refers to development evidence and may change.

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
