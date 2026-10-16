# Research decision and new measured evidence — October 16

## Bottom line

The project is not yet a demonstrated new invention. A stronger, testable direction
is **Exposure-Validated Robustness Testing of ML Leakage Detectors**: distinguish
unsupported inputs, edits erased before inference, valid visible edits, and changes
that accidentally remove relevant context. Then assess useful fault discrimination,
not stability alone. This is a proposed empirical contribution, not a verified novel
algorithm. More infrastructure or a more elaborate name would not establish novelty.

## New experiment actually completed

We used the cached, pinned `microsoft/codebert-base` tokenizer, revision
`3b0952feddeffad0063f274080e3c23d75e7eb39`, with Transformers 4.57.1 and the existing
lowercasing protocol. No detector was trained, no predictions were generated and no
downloaded dataset code was executed. Tokenization alone permits this diagnostic.

Inputs: the checksum-verified 381-row published test partition. As before, 340 inputs
parse and permit the existing four AST-preserving transformations; 41 are excluded.
Each pair was checked at total sequence limits 128, 256 and 512, including two special
tokens. We compared both complete content-token sequences and actual padded/truncated
tokenizer outputs, including attention masks. All 4,080 pair/budget checks agreed
with the shortcut comparison. They represent 340 underlying snippets, not 4,080
independent examples. Lower budgets are diagnostics, not new training configurations.

| Total token limit | Appended-comment changes erased | Fraction of 340 pairs | Visible comment changes |
| --- | ---: | ---: | ---: |
| 128 | 88 | 25.88% | 252 |
| 256 | 28 | 8.24% | 312 |
| 512 | 9 | 2.65% | 331 |

All three appended comment types have these same exposure counts. For AST-unparsing,
334/340 pairs change full token sequences; six already have identical tokenized
representations. Truncation erases another 8 changes at 128 and 2 at 256, but none
at 512. An unchanged full token sequence is not a truncation failure.

The tokenizer warns when measuring untruncated sequences longer than its model limit.
Those sequences are only counted and compared here; they are never passed to a model.

Saved evidence: `results/2026-10-16/token_visibility.json`. A second run produced
byte-identical output. This is same-machine repeatability, not independent reproduction.
Regression validation: 192 core tests pass with warnings as errors; lint passes.

Reproduce with a fresh output path:

```bash
HF_HUB_OFFLINE=1 PYTHONPATH=src artifacts/neural_env/bin/python \
  scripts/evaluate_token_visibility.py --output artifacts/token_visibility_new.json
```

## What this establishes—and does not

Under deterministic inference, identical model inputs cannot test a response to an
edit the model never received. Report both source-level eligibility and visible-token
eligibility. Do not count these invisible edits as evidence of learned invariance.

This is a property of our preprocessing and these data. It does not measure accuracy,
prove a trained detector fails, or show that previous papers misreported results.
At the intended 512-token setting, the comment effect concerns only 2.65% of eligible
snippets. That is a useful validity correction, not a large performance breakthrough.
The smaller-budget results must not be advertised as results of the planned full model.

## Literature update and novelty boundary

The [2025 deep-code metamorphic-testing review](https://arxiv.org/abs/2507.22610)
describes 45 primary studies. Its abstract was rechecked; broad transformation-based
robustness testing is established, not our invention. A [2026 survey](https://arxiv.org/abs/2605.13898)
is another relevant primary-source lead; its existence does not establish a gap for us.

The [official FSE 2026 paper abstract](https://conf.researchr.org/details/fse-2026/fse-2026-research-papers/177/Improving-Data-Leakage-Detection-in-Machine-Learning-Notebooks-through-Static-Slicing)
now confirms that Draoui et al. combine Datalog-based slices of training/evaluation
code with structured LLM prompts for leakage detection. This upgrades the earlier
title-only inspection to abstract inspection, not full-paper review. Combining
program structure with an LLM is therefore not a defensible novelty claim here.

Searches also included code-model metamorphic testing with truncation, visible
perturbations and witness-preserving leakage detection. No search result is treated
as proof that an idea is unpublished. Full comparison with relevant primary methods
remains required. We did not reproduce new published systems in this checkpoint.

## Specific contribution hypothesis to investigate next

Question: Do conclusions about detector robustness change when evaluation requires
both supported inputs and an observable edit, while preserving the relevant leakage
evidence? A possible mechanism is an eligibility gate that records why each pair
qualifies or fails, rather than silently treating every generated edit as a test.

Three distinct checks are needed:

1. Input/task support: does the detector meaningfully answer this fault category?
2. Exposure: do actual model inputs change after preprocessing and truncation?
3. Evidence preservation: is the relevant clean/fault distinction still present,
   rather than pushed outside the context window or changed by the transformation?

The current implementation measures the second and already records parts of the
first. It does **not** prove the third. AST identity alone is insufficient for
source-sensitive behavior and cannot certify which evidence survives truncation.
Putting a comment at the beginning is not automatically a solution: it can displace
useful code. Such alternatives require controlled comparisons, not immediate adoption.

Falsification: if these checks rarely exclude cases, do not change defensible conclusions,
or duplicate existing protocols, they do not justify a new methods paper. In that case,
retain an honest replication/diagnostic report rather than inventing a contribution.

## Remaining evidence before claiming a research result beyond this pilot

- Full three-seed CodeBERT outputs: still missing; earlier tests are preflights only.
- Independent human labels and fault-witness review: still needed, not replaceable
  by AI-generated annotations presented as human work.
- A separately sampled, frozen confirmation corpus with repository-level grouping.
- Matched-task static/neural comparisons and correct uncertainty analysis.
- Full-paper novelty review, independent reproduction and author approval.

There is no patentability conclusion, no claim of a first system and no promise of
publication. The supported outcome of this checkpoint is a reproducible tokenizer
exposure diagnostic and a more precise hypothesis—not a completed invention.
