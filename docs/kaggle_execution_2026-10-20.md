# Private Kaggle execution — 20 October 2026

Account: `bibekthakur1` (official CLI browser login completed).

Kernel: https://www.kaggle.com/code/bibekthakur1/researchproof-codebert-20261020

Remote metadata confirmed `is_private: true`, GPU enabled, internet enabled,
and `machine_shape: NvidiaTeslaT4`. Initial quota: 30 GPU hours remaining.
Authentication credentials are outside the repository; never commit them.

## Protocol

`scripts/prepare_kaggle_kernel.py` packages only the existing 12-file compute
allowlist. No credentials, Git history, dataset rows, or weights are embedded.
Source hashes are checked on Kaggle. Data and model downloads happen there.
The script refuses to run outside `/kaggle/working` and requires CUDA for training.
All three prespecified seeds run sequentially with the existing fixed protocol;
no test-based tuning or selection is added. The submitted session limit is
39,600 seconds (11 hours), subject to Kaggle's own limits.

An isolated environment and model cache live under `/tmp`; research code,
environment inventory, logs, predictions, and checkpoints live under
`/kaggle/working/researchproof` for saved outputs. Preserve failed runs as well as
successful ones. There is no mid-epoch resume; inspect failures before restarting.

## Attempts

- Version 1 uploaded successfully but failed before training: `nvidia-smi` was
  absent. This utility is diagnostic, not a prerequisite for PyTorch CUDA.
  Original local package retained at `artifacts/kaggle_job_2026-10-20`.
- Version 2 makes that utility optional, explicitly requests `NvidiaTeslaT4`,
  and retains the mandatory PyTorch CUDA check. Failed before training: no NVIDIA
  device nodes exposed and Python `venv` could not bootstrap `ensurepip`. Package
  and failure log retained under `artifacts/kaggle_job_2026-10-20_v2` and
  `artifacts/kaggle_v2_startup_log.json`.
- Version 3 switches to notebook format, requests the same T4 accelerator,
  checks NVIDIA device availability before dependency installation, and uses
  the host pip to install into a `venv --without-pip` environment. This avoids
  relying on the runtime's broken `ensurepip`. Source package:
  `artifacts/kaggle_job_2026-10-20_v3`.

Upload acceptance is not evidence of completed training. Check the live status
and logs before making any scientific claims.

## Check and retrieve

From the repository, using the isolated CLI:

```bash
artifacts/kaggle_cli_env/bin/kaggle kernels status bibekthakur1/researchproof-codebert-20261020
artifacts/kaggle_cli_env/bin/kaggle kernels logs bibekthakur1/researchproof-codebert-20261020
artifacts/kaggle_cli_env/bin/kaggle kernels output bibekthakur1/researchproof-codebert-20261020 -p artifacts/kaggle_return_2026-10-20
```

Retrieve outputs after completion; check available local disk space before
downloading large checkpoints. Validate all three seed directories using the
existing evidence validators and `scripts/analyze_codebert_study.py` before
interpreting results. Human review and independent scientific confirmation remain
separate unfinished requirements. No full model training was executed on the M1.

Local packaging/regression verification: all 194 core tests passed, including
private metadata, source integrity, overwrite refusal, and local-execution guard.
