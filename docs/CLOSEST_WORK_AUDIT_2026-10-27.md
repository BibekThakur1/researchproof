# Closest-work audit: what ResearchProof can and cannot claim

Checked 27 October 2026. This is a bounded literature audit, not a systematic
review or proof of novelty. I read the complete 2025 PeerJ article through its
[Europe PMC full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11935776/fullTextXML),
the full [2025 metamorphic-testing review](https://arxiv.org/pdf/2507.22610),
and the full [2026 CodeBERT embedding-drift preprint](https://arxiv.org/pdf/2609.21203).
For the FSE 2026 notebook paper, only the published abstract was accessible;
the ACM full-text link returned 403. The IST 2026 article's indexed publisher
text was available in search, but direct full-text access returned 403. Claims
about uninspected methods are therefore explicitly **unknown**.

| Closest work | Verified overlap | Difference that remains possible | Boundary / uncertainty |
| --- | --- | --- | --- |
| [Alturayeif & Hassine, PeerJ CS 2025](https://doi.org/10.7717/peerj-cs.2730) | Already fine-tunes CodeBERT for leakage detection on the same 1,904 snippets, uses the same 1,523/381 split, and repeats experiments across five seeds. Its limitations explicitly acknowledge that isolated blocks cannot capture cross-cell leakage. | ResearchProof archives per-case predictions, controlled source edits, actual tokenizer exposure, and a provenance trace for persistent errors. | A new CodeBERT run or the general statement “context matters” is **not** novel. Our classifier protocol is not an exact reproduction of theirs. |
| [Code4ML corpus paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10280557/) and [Code4ML 2.0 archive](https://zenodo.org/records/12700065) | Existing code-cell-to-notebook identifiers and metadata enable provenance recovery. | We apply these links to audited false negatives in this downstream leakage benchmark. | Reusing the links is an analysis method, not a new dataset or algorithm. Current Kaggle snapshots may differ from historical versions. |
| [Yang et al., ASE 2022](https://arxiv.org/abs/2209.03345) | Static data-flow analysis of leakage in notebooks, including cross-cell context. | ResearchProof studies a learned snippet detector's stability and input visibility. | Their notebook-level labels are not directly comparable with our isolated-snippet labels. |
| [Applis et al., ASE 2021/LAMPION](https://doi.org/10.1109/ASE51524.2021.9678706) | Applies semantics-preserving code transformations to CodeBERT and measures changed behavior. | Different task (code-to-text), specific leakage detector, and tokenizer-exposure accounting. | Metamorphic testing of CodeBERT is established; edits alone cannot support novelty. |
| [Asgari et al., 2025 review](https://arxiv.org/pdf/2507.22610) | Reviews 45 studies; explicitly discusses comment/whitespace edits, reproducible prediction data, dataset hashes, and uncertainty reporting. | A leakage-specific empirical case study with original-notebook provenance may still add value. | Most of our evaluation ingredients are already recommended or practiced. |
| [Draoui et al., FSE 2026](https://doi.org/10.1145/3808199) | Published abstract describes provenance-aware notebook slices and structured LLM reasoning for leakage detection on Kaggle/GitHub notebooks. | Our current study evaluates a smaller fine-tuned encoder's failure modes rather than proposing their detector architecture. | Full text unavailable in this audit. Do **not** claim they omit robustness, exposure, or label-quality tests. A context-recovery algorithm would face this direct competitor. |
| [Draoui et al., IST 2026](https://doi.org/10.1016/j.infsof.2026.108336) | Publisher-indexed article describes 614 manually annotated model pairs and manifestation-level analysis; its abstract compares three detector paradigms. | ResearchProof examines one snippet benchmark's provenance and perturbation visibility. | Article says it releases a curated dataset, but I could not verify an artifact URL, license, downloadable files, or task-compatible extraction. No external confirmation set can be assumed. |
| [Ghaneshirazi et al., 2026 preprint](https://arxiv.org/pdf/2609.21203) | Uses CodeBERT on a safety-related classification task, controlled behavior-preserving changes, directional flips, grouped bootstrap, and a defense. | Different task and input pipeline; our distinctive part would need to be leakage-specific provenance and edit visibility, not bidirectional flip counting. | This is a close methodological competitor. It substantially weakens a stand-alone “directional robustness audit” novelty claim. |
| [Nam et al., ReDef/FSE 2026](https://arxiv.org/abs/2509.09192) | Studies code-model inputs, high-confidence labels, and counterfactual perturbations for defect prediction. | Different code task and labeling unit. | Another example that input representation and counterfactual tests are established research directions. |

## Current novelty decision

The strongest defensible present description is **a reproducible, exploratory
audit of a published snippet benchmark and one CodeBERT implementation**. It
is not a novel detector, invention, or established top-conference contribution.
The provenance work is a useful new lead: five persistent misses have exact
public-notebook cells, and their contexts suggest different mechanisms and
possibly disputed labels. That lead could become a publishable empirical
finding only if independent reviewers validate the cases under an explicit
policy, a broader sample shows the issue is not anecdotal, and an independent
corpus tests whether the resulting conclusion generalizes. A full-text check
of FSE 2026 and the IST 2026 artifact is also still necessary.

**Do not** state that this is the first exposure-aware audit or that the 2026
papers did not do these analyses. The accessible evidence does not support
either claim. If the confirmation gate fails, the honest outcome is a
well-documented replication/benchmark-validity note, possibly suited to a
workshop or artifact track after external feedback, not an inflated method
paper.
