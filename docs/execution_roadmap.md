# Execution roadmap

This schedule assumes two researchers working roughly 10–15 hours each per week. It is a planning document, not a promise that every stage will succeed. Each phase ends with a decision gate so that weak assumptions are corrected early.

## Week 1 — reproduce the smallest valid case

- Both researchers set up the repository independently.
- Run the clean and faulty preprocessing pilot on both laptops.
- Compare configuration, split hashes, result schema, and software versions.
- Read the benchmark specification together and record disagreements as issues.
- Write the first experiment-log entry.

**Exit condition:** both machines pass the tests and generate the same split hashes for all five seeds.

## Week 2 — manifest and provenance

- Define a JSON schema for benchmark cases and runtime evidence.
- Record dataset fingerprint, source, split policy, transformer fit scope, and model-selection scope.
- Add schema validation and deterministic case identifiers.
- Test that modifying a split, seed, or injector version changes the identifier.

**Exit condition:** a benchmark case can be regenerated and independently checked from its manifest.

## Weeks 3–4 — first three fault injectors

- Implement exact split overlap.
- Implement preprocessing-before-split.
- Implement target-informed feature selection.
- For every injector, create a paired clean pipeline and tests proving that only the intended methodological decision changed.
- Manually review at least ten cases per family.

**Exit condition:** three stable fault families pass Gate 1 in the research plan.

## Week 5 — annotation pilot

- Remove filenames and obvious injector markers from a sample.
- Have both researchers label validity, evidence, and minimal repair independently.
- Measure agreement and discuss every disagreement.
- Refine definitions rather than forcing agreement.

**Exit condition:** at least 90% agreement on a clearly defined pilot, or a written decision to narrow the taxonomy.

## Weeks 6–7 — baseline auditors

- Implement a majority baseline.
- Implement explicit API/order rules.
- Implement a bag-of-code-token logistic-regression baseline.
- Implement a structural baseline using AST and simple lineage features.
- Freeze dataset- and template-level train/validation/test partitions.

**Exit condition:** baseline performance and failure cases are reproducible. If rules solve the benchmark almost perfectly, redesign the benchmark before adding a complicated model.

## Weeks 8–9 — runtime lineage

- Instrument transformer `fit`, resampling, feature selection, and model-selection calls.
- Record which row identifiers and labels each operation observes.
- Add dynamic-only and static-plus-dynamic auditors.
- Measure added accuracy, false alarms, calibration, and runtime cost.

**Exit condition:** runtime evidence adds measurable value on held-out datasets or templates.

## Week 10 — counterfactual repair

- Define minimal repairs for the first three fault families.
- Execute each repair in a restricted environment.
- Check that the intended task, split, and model family remain unchanged.
- Record whether the fault disappears and how reported performance changes.

**Exit condition:** repairs are executable and verifiable; otherwise present the system as detection-only.

## Week 11 — generalization and robustness

- Hold out complete datasets and template families.
- Run leave-one-fault-family-out evaluation.
- Rename variables and refactor equivalent pipelines to test superficial sensitivity.
- Introduce missing values, class imbalance, and noisy labels without changing the fault definition.

**Exit condition:** the detector shows evidence of generalization beyond author-specific templates.

## Week 12 — ablation and statistics

- Remove structural, lineage, calibration, and counterfactual components one at a time.
- Run at least five fixed seeds for stochastic comparisons.
- Compute bootstrap confidence intervals and paired comparisons.
- Report effect sizes, not only p-values.

## Week 13 — paper draft and reproducibility audit

- Freeze a versioned benchmark release candidate.
- Generate tables and figures directly from validated artifacts.
- Ask a third person to follow the reproduction instructions without verbal help.
- Write limitations and negative findings before the conclusion.

## Week 14 — submission decision

- Repeat the closest-work search.
- Decide whether the evidence supports a benchmark paper, systems paper, workshop paper, or technical report.
- Select a venue only after matching its recent scope and formatting requirements.
- Make the repository public only after license, data, privacy, and artifact checks.

## Weekly meeting format

Keep the meeting to 45 minutes:

1. What evidence was produced?
2. What failed or contradicted the hypothesis?
3. Is the current result trustworthy?
4. Which single issue is the next priority?
5. Who owns it, and what is its acceptance criterion?

