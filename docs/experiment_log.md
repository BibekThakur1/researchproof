# Experiment log

Use one entry per decision-changing experiment. Do not replace old entries when a run fails.

## Template

**Date:**  
**Researchers:**  
**Commit:**  
**Question:**  
**Hypothesis:**  
**What would falsify it:**  
**Dataset and version:**  
**Configuration:**  
**Command:**  
**Environment:**  
**Result artifact:**  
**Observations:**  
**Unexpected behavior:**  
**Decision and next step:**  

---

## 5 September 2026 — benchmark v0.2 engineering run

**Researchers:** Initial automated run; second-person reproduction pending  
**Question:** Does the end-to-end benchmark, auditing, repair, and held-out-dataset evaluation machinery work?  
**Hypothesis:** Explicitly injected faults should be recoverable from the current engineered evidence.  
**What would falsify it:** Mismatched paired splits, unstable case identifiers, undetected injected faults, false alarms on clean pairs, failed repair checks, or different test results on repetition.  
**Dataset and version:** scikit-learn breast cancer, wine, and digits loaders under benchmark configuration v0.2  
**Configuration:** `configs/benchmark_pilot.yaml`  
**Command:** Follow the complete command sequence in `README.md`.  
**Environment:** Local Apple Silicon; exact package versions remain in the generated artifact and installed environment.  
**Result artifact:** `artifacts/benchmark_v0_2/` (ignored by Git and regenerated locally)  
**Observations:** 90 cases generated; all 36 tests passed with warnings treated as errors. Current rules and learned baselines classified all cases correctly. Calibration remained imperfect. All 45 mechanical repair checks passed.  
**Unexpected behavior:** Earlier runs exposed optimizer and constant-feature warnings; preprocessing and feature scoring were corrected before the recorded run.  
**Decision and next step:** Treat this solely as machinery validation. Build realistic, blinded source templates and remove label-revealing feature names before making any scientific claim. See `docs/progress_2026-09-05.md`.  
