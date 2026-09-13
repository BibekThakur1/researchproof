# Generated pilot results

These are measured exploratory results.

## Constructed selection-provenance experiment

| Method | Known cases | F1 | False positives | False negatives | Decisions on unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| count_rule | 720 | 0.5366 | 270 | 72 | 90 |
| selection_provenance | 720 | 1.0000 | 0 | 0 | 0 |
| without_decision_edges | 720 | 0.0000 | 0 | 270 | 0 |
| without_row_identity | 720 | 0.7500 | 180 | 0 | 0 |

810 constructed cases share model fits; 90 have unknown labels. Perfect explicit-API behavior is a mechanism check, not external detection accuracy.

## External corpus, unchanged symbolic analyzer

| Category | Eligible | Answered | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| pre | 66 | 58 | 0.2500 | 0.1053 | 0.1481 |
| overlap | 66 | 58 | 0.0000 | 0.0000 | 0.0000 |
| multi | 66 | 58 | 1.0000 | 0.0357 | 0.0690 |

The corpus contains 100 ground-truth rows, 66 with explicit category labels; 86 notebooks parse and 58 have both labels and parsable source.

## Learned feature representation

| Mode | Encoding | Holdout | Accuracy | F1 |
| --- | --- | --- | ---: | ---: |
| static | presence | dataset_id | 1.0000 | 1.0000 |
| runtime | presence | dataset_id | 0.8750 | 0.8571 |
| hybrid | presence | dataset_id | 1.0000 | 1.0000 |
| static | presence | fault_family | 0.5000 | 0.3333 |
| runtime | presence | fault_family | 0.5000 | 0.0000 |
| hybrid | presence | fault_family | 0.5000 | 0.3333 |
| runtime | log_count | dataset_id | 0.9583 | 0.9565 |
| runtime | log_count | fault_family | 0.5000 | 0.0000 |
| hybrid | log_count | dataset_id | 1.0000 | 1.0000 |
| hybrid | log_count | fault_family | 0.3750 | 0.0000 |

## Feature collision bound

- presence: empirical deterministic accuracy ceiling 0.8750.
- log_count: empirical deterministic accuracy ceiling 1.0000.

Reproduce with the commands in docs/research_report_2026-09-13.md. Full metrics, provenance and hashes are in evidence.json.
