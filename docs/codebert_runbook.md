# CodeBERT neural baseline: what works and how to finish the full run

## Status (September 29)

The optional neural environment is separate from the core project. PyTorch 2.8.0
and Transformers 4.57.1 installed successfully. A tiny random RoBERTa completed a
training/save/reload smoke test. The actual pinned CodeBERT checkpoint also loaded
and completed a two-training-example, 128-token forward/backward preflight on CPU.
Neither run is a research result. Full four-epoch training is still outstanding.

A further MPS preflight completed on two 512-token examples at micro-batch 1.
The complete command took 138.34 seconds, including startup, loading, training and
inference. This is not a throughput benchmark or an estimate of full-run time.
It establishes small-batch feasibility on this machine, not sustained-run stability.
Metadata and hashes are recorded in `results/2026-09-29/neural_validation.json`.

Four optional tests cover dataset-integrity rejection and gradient accumulation
equivalence at micro-batches 1, 2 and 7 versus a logical batch of 16, including a
short final batch. Dropout is disabled in that equivalence test: it does not promise
bit-identical training across different real dropout draws or devices.

The machine has 8 GiB physical memory. MPS GPU availability was confirmed outside
the restricted shell; a negative availability check inside it was not a hardware
limitation. Full-model CPU training could take substantial
time and compete with normal laptop use. A CUDA GPU run on your own Kaggle account
is the recommended next execution step; no Kaggle session or credits were accessed.
Your two review packets currently have zero completed verdicts and were not altered.

## Exact scope of the implementation

This is a **modern fixed-budget, full-training-set, no-augmentation CodeBERT baseline**
based on settings in the released AL4Code source. It is not the active-learning or
GPT-augmentation reproduction and must not be described as recreating published
headline scores.

- Model: `microsoft/codebert-base`, revision
  `3b0952feddeffad0063f274080e3c23d75e7eb39`.
- 1,523 original training snippets; text lowercased as in the released code.
- 512-token truncation/padding; four fixed epochs; learning rate 5e-5.
- Logical batch size 16; weighted micro-batch accumulation; gradient clipping 1.0.
- AdamW with epsilon 1e-8 and weight decay zero; linear decay without warmup.
- Random binary classification head is trained. Pretrained encoder weights alone
  are not a trained leakage detector.
- Only the final fixed-budget checkpoint is evaluated. No test-based early stopping,
  tuning, threshold choice, or choosing the best seed is permitted.
- Modern PyTorch AdamW replaces the old Transformers optimizer. Device, dependencies,
  randomization and micro-batching can differ from historical runs; report deviations.

Each original test snippet and its AST-preserving variants are evaluated after
training. The file records whether the model's token input actually changed: an
appended comment may be truncated out at 512 tokens. Such cases must not be treated
as evidence of learned invariance. Scope-safe renaming, authored fault pairs and
ASE notebook neural evaluation are not yet included in this runner.

## Local smoke and preflight commands

From the repository root (choose unused output paths on repeats):

```bash
.venv/bin/python -m venv artifacts/neural_env
artifacts/neural_env/bin/python -m pip install -r requirements-neural.txt
artifacts/neural_env/bin/python -m pytest neural_tests -q
PYTHONPATH=src artifacts/neural_env/bin/python scripts/train_codebert.py \
  --smoke --output artifacts/codebert_smoke_new
HF_XET_CACHE=artifacts/hf_cache/xet PYTHONPATH=src \
  artifacts/neural_env/bin/python scripts/train_codebert.py \
  --preflight --output artifacts/codebert_preflight_new
# Optional full-length capacity check when macOS GPU access is available:
HF_XET_CACHE=artifacts/hf_cache/xet HF_HUB_OFFLINE=1 PYTHONPATH=src \
  artifacts/neural_env/bin/python scripts/train_codebert.py \
  --preflight --preflight-length 512 --device mps --micro-batch 1 \
  --output artifacts/codebert_mps_preflight_new
```

The offline MPS command assumes the CPU preflight already cached the model.
The cache uses the repository's ignored artifacts directory. Preflight trains on
two rows only and does not read the test set or save a full checkpoint. Smoke uses
random synthetic token sequences. The summary tool explicitly rejects both modes.
Only public model/data downloads are performed; no model API key is required.

## Full GPU execution: what you need to do

1. Open a private Kaggle notebook with an available GPU and internet enabled, subject
   to your account's permissions and quotas. Do not make the research repository public
   just to transfer files. Do not paste access tokens into notebook code or output.
2. Transfer this repository's tracked code/config files using your chosen private
   method. Exclude `.git`, virtual environments, secrets, cached datasets and model
   weights. Work in the uploaded repository root. Do not redistribute source datasets
   inside a public notebook or dataset.
3. Install `requirements-neural.txt`. This pinned stack was tested on macOS/Python
   3.13; Linux/CUDA wheel and notebook compatibility still need checking. Record the
   resolved versions instead of claiming the Mac and Kaggle environments are identical.
4. Run the public artifact fetcher and optional neural tests, then a full run:

```bash
python -m pip install -r requirements-neural.txt
python scripts/fetch_peerj_materials.py
python -m pytest neural_tests -q
HF_XET_CACHE=artifacts/hf_cache/xet PYTHONPATH=src python scripts/train_codebert.py \
  --device cuda --seed 0 --micro-batch 2 --output artifacts/codebert_seed0
```

The script checks CUDA availability and refuses to overwrite an existing run folder.
Training progress is emitted after each epoch. Interrupted runs do not count as
completed evidence. Resume-from-mid-epoch is not implemented; retain partial logs
and use a fresh output directory if restarting.

5. Keep `run.json`, `training.json`, `predictions.json`, and the checkpoint folder.
   Download these privately before ending the notebook session. Do not upload large
   checkpoints to Git. Send back the run metadata and prediction files for validation.
6. After the first full run succeeds, repeat predeclared seeds 1 and 2 with unchanged
   settings. Report every seed, not whichever produces the best result.

## Summarize on the existing research environment

```bash
.venv/bin/python scripts/summarize_codebert.py artifacts/codebert_seed0 \
  --output results/codebert_seed0_summary.json
```

This checks completed status, the fixed training protocol, expected test counts,
the pinned model and dataset versions, unique pairs, label consistency and
transformation coverage. It rejects changed predictions for identical token inputs.
Both harmful and corrective flips are counted separately. It cannot prove the
training metadata is honest by itself; retain full logs and checkpoint provenance.

The test suite also exercises these gates with fabricated fixtures. Those fixtures
exist solely to test validation logic and must never be reported as detector scores.

## Still required for a paper

Full neural results; a fair comparison with task-matched static outputs; independent
human review; repository-grouped confirmation data; interpretation of truncation and
lowercasing; and an updated literature/novelty assessment. These are not satisfied
by successful smoke tests. The existing manuscript must keep neural results blank
until valid full-run outputs exist.

References: [official CodeBERT model](https://huggingface.co/microsoft/codebert-base),
[versioned RoBERTa API](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/roberta),
[released AL4Code](https://doi.org/10.6084/m9.figshare.24893832.v1).
