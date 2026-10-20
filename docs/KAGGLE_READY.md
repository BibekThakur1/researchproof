# ResearchProof: ready for the next Kaggle session

The experiment asks whether a trained code model changes its leakage prediction
when harmless comments or formatting change, and whether the model actually sees
those edits after tokenization and truncation. A detector that always says “clean”
can look stable, so we also measure classification quality and distinguish harmful
prediction changes from corrections.

Full GPU training is still pending. The latest remote attempt, version 4, failed
before training because its runtime exposed no NVIDIA device nodes. The reason for
that allocation failure has not been established. This preparation does not resolve
account verification, GPU availability or Internet permissions.

## What is prepared locally

- A private notebook with separate preflight, setup, training and export cells.
- Direct CUDA, Internet and disk checks before large downloads or training.
- An isolated pinned Python environment and source/data fingerprint checks.
- GPU smoke and two-row, full-length capacity checks, marked as engineering checks.
- The unchanged scientific training settings: CodeBERT revision
  `3b0952feddeffad0063f274080e3c23d75e7eb39`, seeds 0/1/2, four epochs,
  512 tokens, effective batch 16, micro-batch 2, learning rate 5e-5.
- External temporary model caches so downloads do not inflate saved outputs.
- Compact result export, checksums and independent local recomputation of tables.

Successful local software tests do not establish Linux/CUDA compatibility. That
will be checked by the notebook. No new scientific measurements are produced by
this preparation, and the Mac does not perform full model training.

Local verification completed: 207 core tests pass with warnings treated as errors;
Ruff checks pass. An artificial-data integration test runs the actual export and
inspection commands, rejects altered reports, and checks overwrite refusal.
All 15 source hashes in the frozen notebook match the current source files.
No artificial test predictions have been saved as project research results.

## Once Kaggle access works

The prepared folder is `artifacts/kaggle_ready_2026-10-20`. It is a local build,
not the older notebook already visible on Kaggle. Upload this new version before
starting the next experiment. Never silently rerun an old package and call it the
new one. Do not modify test thresholds or select successful seeds after looking
at results.

Generated artifacts are intentionally ignored by Git. On a fresh checkout, create
the package locally with:

```bash
.venv/bin/python scripts/prepare_kaggle_kernel.py \
  --output artifacts/kaggle_ready_2026-10-20
```

If that folder already exists, keep it; use a new folder name for a new build and
update the upload/source-manifest paths together. Do not overwrite a frozen package.

From this repository, the operator can upload and launch the prepared version:

```bash
artifacts/kaggle_cli_env/bin/kaggle kernels push \
  -p artifacts/kaggle_ready_2026-10-20 \
  --accelerator NvidiaTeslaT4 -t 39600
```

The metadata requests a private notebook, GPU T4 and Internet. The 39,600-second
limit is a session cap, not a runtime estimate. The implementation uses one GPU;
two listed T4 devices do not imply twice the speed or combined GPU memory.
Actual quota and allocation must be available. No paid compute is requested.

If uploading through the website, import `job.ipynb`, keep it private, choose
GPU T4 and enable Internet. Use **Save Version → Save & Run All** for a saved batch
run rather than relying on unsaved interactive output. If Kaggle requests account
or phone verification, the account owner must complete that step.

The notebook runs these steps in order:

1. **Preflight:** confirm PyTorch can access CUDA, available disk, and access to
   Figshare and Hugging Face. Startup failures produce `researchproof_startup.json`
   and `researchproof_status.json` rather than false training results.
2. **Setup:** verify code hashes, build the environment, fetch pinned data, run
   neural unit tests, a tiny GPU smoke and a two-row capacity check.
3. **Training:** run all three fixed seeds. Each seed trains before its evaluation.
   Loss is printed at epoch boundaries; lack of per-batch output alone does not
   establish a stall. Keep failure logs and completed seeds.
4. **Export:** require all three completed runs and consistent settings, then save
   `researchproof_evidence.zip`. If validation fails, investigate the original files.
   Do not edit metadata or labels until a validator passes.

The job refuses existing run/setup directories. It does not implement mid-epoch
resume. After a failure, preserve outputs before starting a fresh session. Do not
automatically retrain an unfavorable completed seed. A failure during export can
be diagnosed and the exporter rerun separately without training the models again.

## What to save

The small `researchproof_evidence.zip` includes all three seed configurations,
loss histories, predictions and logs, environment and CUDA diagnostics, source
hashes, descriptive analysis and generated tables. Its manifest checks every member.
It excludes raw datasets, model caches and checkpoint weights.

The three final checkpoints remain at:

```text
/kaggle/working/researchproof/artifacts/full_codebert/seed0/checkpoint/
/kaggle/working/researchproof/artifacts/full_codebert/seed1/checkpoint/
/kaggle/working/researchproof/artifacts/full_codebert/seed2/checkpoint/
```

Retain them privately in Kaggle's saved version and verify the version actually
retains those files. Keep an additional copy where storage allows. Do not commit
weights to Git. Preserve startup and setup logs if a job fails before export.
Temporary caches under `/tmp` need not be saved.

After a successful saved run, download only the small package to the Mac:

```bash
artifacts/kaggle_cli_env/bin/kaggle kernels output \
  bibekthakur1/researchproof-codebert-20261020 \
  --file-pattern '(^|/)researchproof_evidence[.]zip$' \
  -p artifacts/kaggle_return_2026-10-20 --page-size 200
```

Use a specific version suffix, such as `/5`, once its actual version is known.
If Kaggle returns a pagination token, continue listing/downloading that page until
the package is found; absence on one page does not mean it was never generated.
Downloading all outputs would also download large checkpoints and is unnecessary
for this initial analysis.

## After the results return

Use the actual downloaded path if Kaggle preserves an extra directory level:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_codebert_results.py \
  artifacts/kaggle_return_2026-10-20/researchproof_evidence.zip \
  --source-manifest artifacts/kaggle_ready_2026-10-20/source_hashes.json \
  --output artifacts/codebert_return_analysis_2026-10-20
```

This reads the ZIP without extracting or executing it. It verifies file hashes,
the frozen source manifest, three complete seeds, four consistent loss values per
seed, training protocol, prediction counts and pairing, and consistency of the
saved report. It recomputes results instead of trusting the saved tables. It does
not load model weights or require GPU training on the Mac.

The report keeps 381 distinct test snippets; three seeds do not turn them into
1,143 independent cases. Seed standard deviations describe optimization variation,
not confidence intervals for future repositories. The software can check internal
consistency but cannot prove who performed a run, verify human authorship, or
establish ground truth from hashes alone.

## Work that can proceed while Kaggle is unavailable

You and your friend can independently complete the existing 20-case review packets.
Follow [the review guide](HUMAN_REVIEW_NEXT.md). Do not train models just to fill
the waiting time or invent labels/results. After GPU results return, human review,
independent confirmation, task-matched baseline comparisons and a full-paper
novelty assessment still determine whether a defensible manuscript can be submitted.
