# ResearchProof submission-readiness decision — 29 October 2026

**Decision: not ready for peer-reviewed submission.** This is a factual gate
assessment, not a judgment that the research direction must be abandoned.
The within-corpus CodeBERT experiment and reproducible case-level analysis
are complete; the evidence needed to interpret and generalize them is not.

| Gate | Current evidence | Status |
| --- | --- | --- |
| Fixed neural experiment and archive integrity | Three CodeBERT seeds, 381 published test snippets, four edits on 340 parseable cases; ZIP and source hashes independently checked by repository tools. | Complete for this *explored split*. |
| Original-code context | 23/25 published positives match exact text in a Code4ML derivative; 15/25 occur as exact cells in current public notebooks. Five of those 15 were missed by all seeds. [Report](POSITIVE_CONTEXT_GATE_2026-10-29.md). | Useful exploratory provenance; historical revisions and label meaning unresolved. |
| Independent label/semantic review | The eight-case blind packet exists, but `reviewer_a.csv` and `reviewer_b.csv` each have **0/8** judgments as of this check. | Blocking. AI-assisted notes cannot fill this gate. |
| Independent confirmation corpus | No newly sampled, compatible, human-labeled corpus is frozen. The [2026 FSE replication record](https://zenodo.org/records/17128972) restricts its files; the 614-model-pair study's stated dataset was not located as an accessible, task-compatible artifact. [Audit](CONFIRMATION_DATA_AUDIT_2026-10-27.md). | Blocking for a generalization claim. |
| Closest-work novelty | PeerJ 2025 already uses CodeBERT on this split; FSE 2026 uses notebook slices; prior CodeBERT metamorphic studies cover edits and directional flips. [Matrix](CLOSEST_WORK_AUDIT_2026-10-27.md). | A broad new-detector or generic robustness claim is not defensible. Full text of the FSE/IST papers remains to be checked. |
| Baseline fairness | Same-case lexical comparisons and archived predictions exist, but training protocols differ. No task-compatible external dataset has been scored. | Descriptive only. |
| Manuscript and author release | Draft has methods, observed results, threats, and explicit release gates. No agreed authorship, independent technical review, final venue fit, or rights audit. | Incomplete. |

## Minimum viable next decision

1. Two humans independently complete the [eight-case blind-review protocol](HUMAN_NOTEBOOK_REVIEW_2026-10-27.md). Do not show either reviewer model predictions, published labels, or the AI case notes before locking both forms. A coordinator preserves initial responses and adjudication separately.
2. If reviewers find a recurrent context/label-scope problem, freeze a larger *balanced* review sample that includes negatives and source-verified positives. State the sampling and inclusion rule before reading their model outcomes. The research contribution may then be a benchmark-construct-validity study; the current eight-case audit alone is too selected for that claim.
3. If they instead validate the original snippet labels, use the case explanations to formulate a narrow reliability hypothesis, then seek a separately sourced confirmation corpus. Do not retune on the explored PeerJ test set.
4. Obtain the restricted FSE/IST full papers or clearly state that those comparisons are incomplete. A claim of novelty cannot depend on asserting what inaccessible papers did *not* do.
5. Recompute all reported tables from frozen files, secure rights for any redistributed code or notebooks, obtain a critical human read of the draft, agree authorship and disclosure, and only then choose a current venue and formatting rules.

If no qualified human reviewers or compatible external labels are available,
the honest near-term product is a reproducible exploratory report or preprint,
**not** a manuscript advertised as independently validated or submission-ready.
No further seed tuning or cosmetic paper writing substitutes for these gates.
