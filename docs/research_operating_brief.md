# ResearchProof working brief

Current direction (2026-09-21): detector robustness pilot. Read
`docs/research_handoff_2026-09-21.md` and `paper/robustness_pilot_draft.md` first.
The provenance objective below is historical supporting work, not the active paper claim.

Objective: determine whether evaluation-score provenance supports useful selection-
leakage auditing beyond existing notebook analyses, with evidence suitable for a
research report and a later submission decision.

Work from the measured evidence in `results/2026-09-13/evidence.json`. Preserve the
original benchmark and its failures. Keep implementation, experiments, literature
claims and external evaluation independently inspectable in Git.

For each next experiment, state the research question, closest work, input provenance,
comparison, expected falsification and measurement before running. Record post-hoc
changes explicitly. Train detectors only on declared training partitions. Repeated
cases generated from the same code are not independent authors or environments.

Prefer investigating a failed prediction over adding another synthetic template.
Report coverage, false alarms and missing evidence with aggregate scores. Check
whether a trivial baseline explains apparently good performance. Test instrumentation
loss explicitly; unknown execution history must not be treated as verified clean.

Do not claim automatic arbitrary-code repair: the current repair suite substitutes a
predefined clean counterpart. Do not claim human review or second-machine reproduction
without those records. Do not claim a new algorithm from ordinary set propagation.

Versioned JSON persistence, separate-process checks, and restricted GridSearchCV
capture are implemented; see `docs/progress_2026-09-18.md`. The single-search pilot
shows no advantage over a split-role baseline. The next task is evaluating whether
external multi-stage workflows actually need more report-specific dependencies,
then measuring capture loss and overhead. Do not assume a richer graph is necessary.
Use newly selected, independently authored
workflows for confirmation; the ASE 2022 sample is now an exploratory development set.

Before pushing, run relevant tests and lint, generate small evidence files, check the
diff for source/data redistribution and unverifiable claims, and verify the remote
commit. A future paper may report negative results. Publication and professor interest
depend on the quality of the contribution and evidence, not the repository's size.
