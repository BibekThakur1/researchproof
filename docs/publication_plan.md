# ResearchProof: path to a defensible submission

Historical provenance plan. For the current robustness pilot and outstanding
submission requirements, use `docs/research_handoff_2026-09-21.md` instead.

Status: development plan, not a promise of publication. Written 2026-09-16 before
running the new persistence pilot. Historical experiments remain exploratory.

## Proposed paper

Working title: **Auditing Model Selection Across Persisted Evaluation Results:
Score Provenance and Incomplete Evidence**.

Question: under which workflow conditions does explicit score-dependency evidence
improve report-specific selection-reuse auditing, and when must an auditor abstain?

The candidate contribution is a supported workflow boundary plus an evaluation of
its coverage and failure modes. JSON storage, checksums, set union, and the familiar
problem of test-set reuse are not novel contributions. A reuse witness does not
quantify score inflation or prove that the entire experiment is invalid.

## Closest work and unresolved comparisons

- [Yang et al., ASE 2022](https://arxiv.org/abs/2209.03345): static analysis of
  preprocessing, overlap, and multi-test leakage. Run the released tool on matched
  inputs before making comparative claims; counting calls is not its reproduction.
- [LeakageDetector 2.0](https://arxiv.org/abs/2509.15971): notebook leakage detection
  and correction support. Detection plus suggested repairs is not our novelty.
- [Automated Provenance-Based Screening of ML Data Preparation Pipelines, 2024](https://link.springer.com/article/10.1007/s13222-024-00483-4): provenance-based
  screening already detects data preparation issues including overlapping records.
  Compare the exact tracked dependencies; do not claim provenance auditing is new.

These sources were checked during this checkpoint. This is a focused update, not an
exhaustive novelty clearance. Read implementation details and trace representative
examples through each available tool before finalizing the novelty table.

## Stage 1: real-fitting development pilot

Run `scripts/run_persistence_pilot.py --output artifacts/persistence_pilot_v1`.
It uses three local public datasets, three seeds, three decision-tree depths, and
disjoint training/selection/fresh partitions. Evaluate complete, scalar-only, and
missing-history exports against reused and fresh report partitions in another Python
process. Expected status is fixed by API semantics, not inferred from model accuracy.

Report mismatches, abstentions, bytes, and observed timings. Do not interpret shared
fits as independent workflows or interpreter startup as monitor overhead. This pilot
can falsify implementation correctness; it cannot establish external usefulness.

Observed after running the pilot: 27 fitted models, 54 checks, zero mismatches.
The repeated run also had zero mismatches. Machine-readable records and environment
versions are in `results/2026-09-16/persistence_pilot.json`. These runs are not two
independent replications. All 108 regression tests and repository lint passed.

Reproduction command (from the repository root):

```bash
.venv/bin/python scripts/run_persistence_pilot.py \
  --output artifacts/persistence_pilot_v1 \
  --summary results/2026-09-16/persistence_pilot.json
```

Timing values vary on rerun. The current dataset fingerprint and recorded software
versions identify the inputs and environment; the executable script is versioned in Git.

## Stage 2: evidence required before submission

1. Define supported operations: manual search with explicit callbacks, persisted
   selection, nested selection, and unsupported/offline human decisions. Demonstrate
   capture without users manually labeling the final fault.
2. Assemble a development set and a separately frozen confirmation set of independently
   authored workflows. Start with 20--30 diverse eligible workflows, not a magic
   publication threshold. Log source URL, revision, license, exclusions, and adaptations.
   Freeze a sampling rule before screening; do not select only easy positive cases.
3. Two reviewers label score-to-decision-to-report dependencies independently, before
   seeing detector output. Record disagreements and adjudication. Your friend can be
   a reviewer, but coauthor review is not independent external validation. Neither
   person should claim blindness to examples they created.
4. Compare the published ASE detector where executable, an explicit split-role
   baseline, evaluation-count rules, and always-flag/always-abstain controls. Record
   unsupported inputs and environment failures. Compare matched tasks, not unrelated
   fault categories. Do not treat abstention as a correct negative.
5. Remove decision propagation, row identity, and completeness tracking separately.
   Test shuffled scores, ties, partial overlap, reused IDs across dataset versions,
   nested selection, missing files/fields, and off-code choices.
6. Report precision/recall/FPR on answered cases alongside answer coverage and unknown
   cases. Bootstrap paired differences at original-workflow level, not seed or mutation
   level. Publish intervals and per-workflow outcomes; small samples limit conclusions.
7. Measure paired wall time and storage with/without capture, identical fitted-workflow
   settings, warmups and repeated runs. Separate startup, fitting, I/O, and auditing.
8. Have your friend reproduce the frozen artifact on their M1, retaining commands,
   versions, failures, and hashes. Another AI process on this machine does not count.

## Go/no-go criteria

Proceed with a methods/system claim only if the supported boundary works on external
workflows, adds useful evidence over simpler baselines, and has measured tolerable
cost. Tolerable cost must be defined for the use case before confirmation results.
If a split-role checker performs equally well, simplify the method and reconsider
the contribution. If capture requires users to supply the answer, stop claiming
automated detection. If the original static tool already covers the boundary, narrow
to an empirical replication/failure analysis only if evidence makes that worthwhile.

Perfect constructed-case scores and more unit tests cannot satisfy these gates.

## Manuscript and release package

Write introduction/related work/problem definition now; leave confirmation results
empty. Final sections: supported semantics; capture implementation; corpus and label
protocol; baselines; results and confidence intervals; failures; threats; artifact.
Generate result tables from frozen logs. Retain negative results and exclusions.
Publish code only with appropriate licensing and remove secrets/private source/data.
Prepare an anonymized artifact when required. Agree author contributions and order
with your friend, and follow the venue's AI-assistance disclosure policy.

## Venue and submission route

[CAIN](https://conf.researchr.org/track/cain-2027/cain-2027-call-for-papers) is a
scope-compatible research target for software engineering of AI systems, not an
acceptance prediction. Read the live track rules before selecting a deadline. A
relevant peer-reviewed workshop/tool track may fit a narrower validated contribution;
do not assume any track is an easy acceptance. A preprint is not peer-reviewed publication.

Sequence: pass evidence gates -> choose current suitable call -> format/anonymize ->
obtain critical technical review -> author approval -> submit -> address reviews.
No automatic submission, registration payment, or public release is authorized here.

## Work allocation and realistic schedule

- Weeks 1--2: finish supported capture boundary, closest-work comparison, corpus rules.
- Weeks 3--4: source workflow review, labeling, baseline environment reproduction.
- Weeks 5--6: freeze confirmation set; run comparisons, ablations, overhead studies.
- Weeks 7--8: analyze failures and uncertainty; second-machine reproduction.
- Weeks 9--10: manuscript, independent feedback, artifact audit and submission decision.

This is a planning estimate for two part-time researchers, not a deadline guarantee.
The user owns capture implementation understanding and methods; the friend can lead
corpus curation and baseline reproduction. Both must understand and verify the claims.
AI can assist implementation and writing, but cannot substitute for human review,
authorship accountability, or experimental evidence.
