# Run the prepared neural compute bundle

This is a private transfer of project-authored code, not an anonymous submission
artifact. The bundle contains no Git history, tokens, dataset rows or model weights.
`MANIFEST.json` records individual file hashes. No files have been uploaded for you.

## In a private GPU notebook/session

Upload the ZIP privately, extract it into an empty working directory, and change into
that directory. Enable available GPU/internet access. Do not paste credentials into
code. Account availability, quotas and Linux/CUDA compatibility remain unverified.

Run these shell commands (use notebook shell cells or a terminal):

```bash
python -m pip install -r requirements-neural.txt
python scripts/fetch_peerj_materials.py
python -m pytest neural_tests -q
PYTHONPATH=src python scripts/train_codebert.py --smoke --output artifacts/gpu_session_smoke
PYTHONPATH=src python scripts/run_codebert_seeds.py --device cuda --micro-batch 2 --output artifacts/full_codebert
```

The first smoke is an engineering check, not research evidence. The final command
runs seeds 0, 1 and 2 sequentially; all use the same prespecified training protocol.
Do not tune parameters using test scores. Retain failures as well as successes.

Keep the session active according to your provider's rules. This project does not
circumvent session time limits. Checkpointing within an epoch is not implemented.
The driver skips a completed seed only after validating its metadata/predictions;
it refuses partial existing runs. Diagnose a failure, preserve its logs, and start
an unused output directory. Do not delete unfavorable completed runs to retry them.

## Return these outputs privately

For each seed keep `run.json`, `training.json`, `predictions.json`, `checkpoint/`,
and the adjacent `seedN.log`. Save them before the GPU session expires. The final
checkpoint is large: do not commit it to Git. Small JSON/log files can be returned
for validation; retain checkpoint files separately for reproducibility.

```bash
PYTHONPATH=src python scripts/summarize_codebert.py artifacts/full_codebert/seed0 --output artifacts/seed0_summary.json
PYTHONPATH=src python scripts/summarize_codebert.py artifacts/full_codebert/seed1 --output artifacts/seed1_summary.json
PYTHONPATH=src python scripts/summarize_codebert.py artifacts/full_codebert/seed2 --output artifacts/seed2_summary.json
```

Completing these runs does not finish human review, independent confirmation,
statistical analysis or the manuscript. The driver validates file structure and
protocol declarations; it cannot independently prove their provenance or scientific
validity. CPU/MPS preflights passed locally; the full GPU job has not been run here.
