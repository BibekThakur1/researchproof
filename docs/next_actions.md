# Next actions for a credible ResearchProof study

Update, 13 September 2026: read [the research report](research_report_2026-09-13.md)
first. The external ASE 2022 audit and score-provenance experiment are complete as
exploratory studies. The next method-development priority is capturing decision
provenance across a real callback or persisted-score boundary. The human review and
second-laptop tasks below remain necessary for newly authored workflows.

Do these in order. Do not begin paper-result writing until steps 1–4 are complete.

## 1. Independent source contribution

The second researcher must independently write at least one clean/faulty pair for
each of the four registered fault families. They should not copy or rename the
built-in templates. Follow `docs/external_template_protocol.md` and place the `.py`
and `.json` files in `artifacts/contributions/`.

Acceptance criteria:

- a different `author_id`;
- eight or more valid contributions;
- every file parses;
- authorship and research-reuse statements are present;
- `build_source_index.py` succeeds;
- failures of current analyzers are retained, not rewritten away.

## 2. Independent blinded review

Generate a new blind-review package using a private random salt. Make two copies of
the review CSV. Each researcher labels every case alone, without opening the
adjudication key or discussing individual cases.

Acceptance criteria:

- both CSV files cover every source case;
- `compare_reviews.py` completes;
- raw agreement is reported even when below 0.90;
- every disagreement receives written adjudication after the comparison.

## 3. Independent-machine reproduction

The friend clones the exact commit on a different laptop, creates a fresh virtual
environment from `requirements-lock.txt`, runs the tests, generates benchmark v0.4,
and sends back the generated `runs.jsonl` plus environment details.

Acceptance criteria:

- all tests pass with warnings as errors;
- semantic benchmark fields match the reference output;
- the report explicitly records `independent_machine: true`;
- expected runtime differences are excluded from semantic equality.

## 4. External-validity experiment

Freeze the combined source index before inspecting detector results. Evaluate the
shallow AST and symbolic baselines using author-, template-, and fault-family-level
holdouts. Do not tune on the held-out author.

Acceptance criteria:

- per-fold confusion matrices and false-positive rates;
- calibration and abstention curves where probabilities exist;
- a failure taxonomy with concrete source examples;
- an ablation of helper summaries and repeated-test reasoning;
- no claim based only on aggregate accuracy.

## 5. Submission decision

Update the closest-work search, record exactly what external evidence changed, and
run the release-readiness command. If the external set is still small, target a
student workshop, artifact/benchmark workshop, or technical report rather than a
full research conference. A stronger venue becomes realistic only if hybrid evidence
adds measurable value over credible static baselines on genuinely held-out authors
or projects.
