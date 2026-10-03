# Focused closest-work update — October 3, 2026

This is a focused search update, not a systematic review or novelty clearance.
Primary-source material is distinguished from unresolved search leads. Queries
included `data leakage detection metamorphic code robustness`,
`data leakage detection in machine learning code robustness CodeBERT`, and
`metamorphic testing neural code classifiers semantic preserving robustness`.

| Work and verified source | Inspection depth | Consequence for our claim |
| --- | --- | --- |
| Alturayeif and Hassine, [Data leakage detection in machine learning code](https://pmc.ncbi.nlm.nih.gov/articles/PMC11935776/) (2025) | Full article text available; checked model, dataset and evaluation sections | Learned code-level leakage detection and CodeBERT training are established. Our modern no-augmentation run is a baseline, not an invention or exact reproduction of all reported experiments. |
| Asgari et al., [Metamorphic Testing of Deep Code Models: A Systematic Literature Review](https://arxiv.org/abs/2507.22610) (2025) | Abstract/metadata inspected, not all reviewed papers | Reports a review of 45 primary studies. Applying semantic-preserving edits to test code-model stability is established. Read its taxonomy and closest primary studies before claiming evaluation novelty. |
| Samsonau, [scicode-lint](https://arxiv.org/abs/2603.17893) (2026) | Current abstract/metadata checked; earlier project notes inspect v2 | Pattern-based scientific-code methodology checking already combines model assistance with controlled and external evaluation. Do not claim the general task or two-stage architecture is new. |
| Draoui, Mkaouer and Newman, *Improving Data Leakage Detection in Machine Learning Notebooks through Static Slicing and Structured LLM Prompts* | Title/authors/paper-track presence verified in the [official FSE 2026 program](https://conf.researchr.org/track/fse-2026/fse-2026-research-papers); ACM full-text access failed during this check | A directly relevant baseline/literature lead. Obtain and inspect the paper before asserting which robustness or coverage experiments it lacks. Do not copy search-result performance numbers into our paper. |

The FSE lead's reported DOI is [10.1145/3808199](https://doi.org/10.1145/3808199).
The publisher request did not provide usable full text here. No code reproduction,
score verification or finding about its limitations is claimed.

## Decision

The broad ideas of leakage detection and metamorphic code testing are not new.
Our possible contribution is narrower: an empirical analysis jointly considering
coverage, token-visible surface edits, harmful versus corrective changes, and
fault-pair discrimination on independently checked workflows. This remains a
candidate contribution, not verified novelty. Existing pilot results alone do not
establish a publishable advance.

Before submission: inspect the review's relevant primary studies and the FSE paper,
compare their exact protocols with ours, and document any unavailable baseline or
artifact. Separate title-level relevance from demonstrated methodological overlap.
Do not claim that a search failing to return an identical title proves originality.
