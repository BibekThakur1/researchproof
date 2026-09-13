# Evaluation-score provenance study protocol

Status: development experiment designed before its first run. The implementation and
cases share an AI-assisted author; results are exploratory, not external validation.

## Question and scope

Can explicit propagation of evaluation-row identities through model-selection
decisions distinguish test-driven selection from repeated reporting? The output is
limited to observed selection reuse. It does not certify preprocessing, training,
independence of people, or unseen execution paths.

## Predictions

1. A count-only rule will falsely flag repeated reporting and predeclared comparisons.
2. A count-only rule can miss selection after a single test score when that score is
   reused for reporting without an additional model evaluation.
3. Explicit decision provenance will distinguish these constructed cases and identify
   a fresh disjoint final evaluation as unexposed to the observed selection decision.
4. Removing decision propagation will eliminate recall; removing row identity will
   create false positives for validation and fresh-final-test evaluation.
5. Converting all runtime counts to Boolean presence destroys the distinction between
   one and several evaluations in the earlier learned baseline. A log-count encoding
   may recover dataset-holdout accuracy but does not establish unseen-fault recognition.

## Design

Use breast cancer, wine, and digits data bundled with scikit-learn; five fixed seeds
7, 19, 43, 71, 101; logistic regression and decision trees; candidate budgets 2, 3, 5.
Train only on a stratified 60% partition. Divide the remainder into validation (20%),
selection-test (10%), and fresh-test (10%). The small wine partitions are a limitation.
Retain exact partition IDs and data checksums. Use scaled pipelines for logistic
regression. Candidate values are fixed before running and are never tuned to produce
a desired score inflation. Training is shared across the different process scenarios.

Scenarios: fixed single reporting; repeated fixed reporting; predeclared candidate
reporting without selecting a winner; validation selection and test reporting;
test selection and cached winner reporting; test selection and fresh test reporting;
single-test-score threshold selecting between models with a cached score when the
initial model is retained and a new evaluation otherwise;
selection using a pooled validation/test score; missing selection provenance.

Gold labels follow the construction and need human review. Missing-provenance cases
have unknown labels. Count rules and provenance rules receive no scenario labels.
Report per-scenario confusion counts and abstentions. Do not convert unknown outputs
to clean predictions or claim perfect accuracy by dropping unknown cases silently.

## Comparators and analysis

Compare the local evaluation-count heuristic, explicit selection provenance, an
ablation dropping decision provenance, and an ablation dropping evaluation row identity.
These are our implementations; none is presented as a reproduction of another paper.
Compare presence and log-count runtime features on the unchanged v0.4 input artifacts.
Commit result summaries, exact commands, versions, configuration and input hashes.

The scenarios are correlated transformations of shared model fits. Aggregate counts
describe this constructed population; repeated seeds do not make code templates
independent. Do not attach population-level confidence claims to synthetic detection
accuracy. This pilot establishes falsifying examples and mechanism behavior. A future
confirmatory experiment must hold out source authors/projects and compare a published
detector on its supported input format.

## External corpus audit

Apply the unchanged local `static_analysis.py` to the ASE 2022 authors' public sample
at GitHubAPI-Crawler revision `3aec5fa09788d6659c6e1eac79cdc503340d9694`.
Use all 100 ground-truth rows without choosing examples based on results. Normalize
notebooks in document order; do not execute them. Treat blank labels as unknown and
parse failures as unanswered. Map supervised-selection findings to preprocessing.
Report per-category coverage and confusion counts. The original saved predictions
are a contextual reference, not a rerun or fair identical-environment comparison.
Do not tune the analyzer on these labels before recording the result. This corpus
has been seen in prior research and cannot be called a new benchmark or untouched
future confirmation set after this audit.

Exploratory follow-up, added after observing the symbolic analyzer's external
failure: train the existing AST logistic baseline on the same 44 built-in snippets
and evaluate any-fault prediction against rows with all three external labels.
Keep the existing max_iter=1000, random_state=0, default regularization and threshold
0.5; fit the vectorizer on synthetic sources only. No external labels enter fitting.
This is an exploratory cross-corpus test; no external tuning is authorized by this
protocol and no comparison with the score-provenance API is valid on raw notebooks.

## Stop and continuation criteria

Reject the simple count rule as a conclusive selection detector if a matched valid
case triggers it. Revise the provenance mechanism if supported cases fail. Preserve
all failures. If results match predictions, freeze the artifact and seek independently
written selection workflows; perfect performance on this explicit API is not novelty.
