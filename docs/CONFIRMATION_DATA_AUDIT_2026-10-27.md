# External confirmation data: feasibility audit

This note separates *available source files* from a genuinely independent,
task-compatible confirmation benchmark. No listed corpus has yet passed the
full confirmation gate. The existing PeerJ split and ASE materials have been
explored during development and cannot be relabeled as untouched.

| Candidate | What is verified | Why it cannot yet validate the current claim |
| --- | --- | --- |
| [PeerJ/Figshare leakage snippets](https://figshare.com/articles/dataset/Dataset_for_Data_Leakage_Detection_in_Machine_Learning_Code/24893799) | Canonical 1,523/381 split cached and checksum-verified; 12 test snippets have nonempty training AST matches. | This is the development dataset already used to shape the study. |
| [ASE 2022 notebook materials](https://arxiv.org/abs/2209.03345) | Pinned public artifacts are locally cached; the local audit has 100 notebooks, 66 with explicit preprocessing labels. | Labels are at notebook/workflow level and do not map automatically to a single CodeBERT snippet. The corpus was already explored locally. A task-matched adaptation requires new human annotation and a frozen extraction rule. |
| [2026 manifestation-level notebook study](https://www.sciencedirect.com/science/article/abs/pii/S0950584926003253) | Publisher-indexed text describes 614 manually annotated model-pair pipelines, three evaluated detection paradigms, and says the authors release a curated dataset. | I did not verify the release URL, downloadable files, license, notebook identifiers, or a compatible snippet extraction. Treat this as a data lead, not an available confirmation set. |
| [LeakCheckLLM FSE 2026 replication record](https://zenodo.org/records/17128972) | Zenodo describes a package containing datasets, prompts, and code. On 29 October the public record explicitly marked its files **restricted**; the API returned no public file entries. | A citation and CC BY metadata do not grant access to restricted files. This cannot presently supply a confirmation corpus or a reproducible baseline. The similarly titled [companion record](https://zenodo.org/records/17128799) is also restricted. |
| [Urban et al. 2025 notebook corpus](https://caterinaurban.github.io/pdf/scp2025.pdf) | The full paper reports analysis of 2,111 Kaggle notebooks, with four data scientists checking raised alarms and 25 true-positive alarm instances. | The paper does not provide a balanced, independently labeled snippet test set. Treat unexamined notebooks as unlabeled, not negative; do not turn detector alarms into ground truth. |

The 2026 article's stated release is worth pursuing, but an indexed claim of
release is not an artifact audit. Direct publisher access returned 403 during
the 27 October check, and title/author searches did not yield a verifiable
archive. The available [Code4ML 2.0 archive](https://zenodo.org/records/12700065)
helps recover *context for existing PeerJ examples*, not an independent
confirmation set. See the [five source-verified persistent misses](PERSISTENT_MISS_PROVENANCE_2026-10-27.md).

## Confirmation protocol to freeze before any new scores

The unit should be one independently authored workflow/model pair with a
human-reviewed leakage label and sufficient surrounding code for the claimed
fault type. Record source URL/revision/license, notebook and repository IDs,
collection date, exclusions, and any adaptation from a notebook to a model
input. Exclude overlap with PeerJ training and test material by exact text,
AST fingerprint when parseable, and repository identity where known. Freeze
the sample and labels before running model predictions. Keep all variants of
one workflow together in analysis and bootstrap by workflow/repository, not
by seeds or edits. Report abstentions or unsupported inputs separately from
negative predictions. A paper should not claim external generalization if
the external corpus cannot be constructed and independently checked.

## Current decision

No new corpus is ready to score. The independent contribution must remain
provisional. The next autonomous work is to obtain a *verifiable* released
artifact or build a new source inventory; the next human work is annotation
and adjudication. Neither a synthetic dataset nor a copied subset of the
current split would satisfy this gate.
