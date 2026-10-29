# Positive-label context gate (29 October 2026)

This is a **post-hoc provenance extension**, not independent validation or a
new detector experiment. The canonical 381-row PeerJ test split contains 25
published positives. The checksum-verified
[`positive_provenance.json`](../results/2026-10-29/positive_provenance.json)
matches their exact source text to a third-party Code4ML derivative, checks
candidate IDs against Code4ML's published notebook metadata, and verifies
whether an exact code cell occurs in the *current* public Kaggle notebook.
The script is [`audit_positive_provenance.py`](../scripts/audit_positive_provenance.py).

| Evidence tier | Count among 25 published positives |
| --- | ---: |
| Exact source match in the Code4ML derivative | 23 |
| Candidate notebook ID recovered | 15 |
| Exact cell present in a current public notebook | 15 |
| No source-verified notebook | 10 |

Among the 15 source-verified cases, nine were predicted positive by all three
CodeBERT seeds, one by two seeds, and five by no seed. The eight persistent
misses remain the [first blinded-review packet](HUMAN_NOTEBOOK_REVIEW_2026-10-27.md).
**Do not** treat the 15 available notebooks as a representative sample of all
positive cases: recoverability depends on a third-party matching process and
current Kaggle availability.

## Why context must be adjudicated

The [PeerJ paper](https://doi.org/10.7717/peerj-cs.2730) notes that its input
unit is an isolated code block and that cross-block leakage is out of scope.
Current notebook snapshots illustrate several distinct possibilities:

- Row 370's target cell fits hyperparameter search on named testing data and
  labels after a separate train/test load. That is an observable holdout-reuse
  candidate, but the historical revision and labeling rule still require review.
- Row 72's target cell fits an `AdditiveChi2Sampler` to `X` and transforms
  `X_test`; earlier cells impute a concatenation of training and competition
  test features. The target cell alone and the workflow context can therefore
  support **different** judgments depending on annotation unit and policy.
- Row 321's target cell fits a classifier to `X, y`; earlier cells define
  these from the competition training file and use cross-validation. The
  isolated target cell does not itself show evaluation-to-training flow.
- Row 373's target cell refits on all labeled training data *after* a
  train/validation experiment and before competition-test prediction. Whether
  that is improper depends on the precise evaluation claim. It is not safe to
  classify the line by the phrase “entire data” alone.
- Rows 60 and 207, both missed by all seeds, locally apply statistics derived
  from training data to test data. Their published positive status may reflect
  other cells, a different definition, or a labeling error; this audit does
  not decide which.

These observations are AI-assisted reading of current snapshots. They are
**hypotheses for review**, not corrected labels. In particular, a published
positive may label a whole workflow even if the extracted cell is benign;
we cannot infer the original annotator's intent from the CSV alone. The
published CSV has only `code_block` and `has_data_leakage`, with no notebook
ID, leakage type, or supporting span. The raw published labels remain intact.

## Submission decision rule

If two blinded reviewers agree that multiple target snippets are not
decidable without external cells, the paper's research question should become
**benchmark construct validity and context sufficiency**, not simply model
false negatives. That would still need (a) a *prespecified* review of a broader
sample including negative labels, (b) adjudication with uncertainty and the
historical source revision where recoverable, and (c) an independent corpus or
clearly bounded venue claim. It must be compared with the 2026 notebook-level
manifestation study and FSE slicing work before claiming novelty.

If reviewers instead confirm the original snippet-level labels and find a
coherent persistent-error mechanism, proceed with the reliability paper but
still obtain a separate confirmation set. If agreement is low, or source
versions cannot be reconstructed, report an exploratory audit/replication
and do not manufacture a submission-ready methods result.
