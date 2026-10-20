"""Runtime template embedded into the private Kaggle notebook by its local builder."""

import base64
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# The builder supplies these dictionaries. This template contains no data or keys.
PAYLOAD = {}
HASHES = {}
ROOT = Path("/kaggle/working/researchproof")
RUNTIME = Path("/tmp/researchproof_runtime")
CACHE = Path("/tmp/researchproof_hf")
EVIDENCE = Path("/kaggle/working/researchproof_evidence.zip")
DIAGNOSTICS = Path("/kaggle/working/researchproof_startup.json")
STATE = Path("/kaggle/working/researchproof_status.json")


def record(stage, status, **details):
    event = {
        "stage": stage,
        "status": status,
        "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **details,
    }
    STATE.write_text(json.dumps(event, indent=2) + "\n")
    print(json.dumps(event), flush=True)


def require_kaggle():
    if not Path("/kaggle/working").is_dir():
        raise RuntimeError("This job must run on Kaggle, not a local laptop.")


def preflight():
    require_kaggle()
    record("preflight", "running")
    diagnostic = {
        "python": sys.version,
        "platform": platform.platform(),
        "gpu_device_nodes": [str(path) for path in Path("/dev").glob("nvidia*")],
        "free_working_bytes": shutil.disk_usage("/kaggle/working").free,
    }
    DIAGNOSTICS.write_text(json.dumps(diagnostic, indent=2) + "\n")
    # PyTorch's actual CUDA result is authoritative; node names are diagnostic.
    check = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json,torch; ok=torch.cuda.is_available(); "
            "print(json.dumps({'cuda':ok,'torch':torch.__version__,"
            "'devices':[torch.cuda.get_device_name(i) "
            "for i in range(torch.cuda.device_count())]})); "
            "raise SystemExit(0 if ok else 2)",
        ],
        capture_output=True,
        text=True,
    )
    diagnostic["cuda_check"] = {
        "exit_code": check.returncode,
        "stdout": check.stdout[-4000:],
        "stderr": check.stderr[-4000:],
    }
    DIAGNOSTICS.write_text(json.dumps(diagnostic, indent=2) + "\n")
    if check.returncode:
        record("preflight", "failed", reason="host_pytorch_cuda_unavailable")
        raise RuntimeError(
            "Kaggle CUDA check failed. Inspect researchproof_startup.json and GPU settings. "
            "Training has not started."
        )
    if diagnostic["free_working_bytes"] < 10 * 1024**3:
        record("preflight", "failed", reason="less_than_10_GiB_free")
        raise RuntimeError("At least 10 GiB free working space is required for this job.")
    urls = {
        "figshare": "https://ndownloader.figshare.com/files/43808766",
        "huggingface": "https://huggingface.co/microsoft/codebert-base/resolve/"
        "3b0952feddeffad0063f274080e3c23d75e7eb39/config.json",
    }
    for name, url in urls.items():
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                response.read(1)
                diagnostic[name] = {"reachable": True, "http_status": response.status}
        except Exception as error:
            diagnostic[name] = {"reachable": False, "error_type": type(error).__name__}
            DIAGNOSTICS.write_text(json.dumps(diagnostic, indent=2) + "\n")
            record("preflight", "failed", reason=f"{name}_unreachable")
            raise RuntimeError(
                f"Cannot reach {name}; enable notebook Internet and retry."
            ) from error
    DIAGNOSTICS.write_text(json.dumps(diagnostic, indent=2) + "\n")
    record("preflight", "passed", cuda=json.loads(check.stdout))


def environment():
    return dict(
        os.environ,
        PYTHONPATH=str(ROOT / "src"),
        PYTHONUNBUFFERED="1",
        HF_HOME=str(CACHE),
        HF_XET_CACHE=str(CACHE / "xet"),
    )


def run(arguments, log_name):
    """Save output as it arrives; never log the inherited environment."""
    command = [str(RUNTIME / "bin/python"), *arguments]
    with (ROOT / log_name).open("x") as log:
        with subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ) as process:
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
            if process.wait():
                raise RuntimeError(f"Command failed; preserve {log_name} and inspect its error.")


def setup():
    require_kaggle()
    status = json.loads(STATE.read_text())
    if status["stage"] != "preflight" or status["status"] != "passed":
        raise RuntimeError("A successful preflight is required before setup.")
    record("setup", "running")
    ROOT.mkdir(exist_ok=False)
    for name, encoded in PAYLOAD.items():
        raw = base64.b64decode(encoded, validate=True)
        if hashlib.sha256(raw).hexdigest() != HASHES[name]:
            raise ValueError(f"Source integrity failure: {name}")
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (ROOT / "source_hashes.json").write_text(json.dumps(HASHES, indent=2) + "\n")
    (ROOT / "startup.json").write_bytes(DIAGNOSTICS.read_bytes())
    if RUNTIME.exists():
        raise FileExistsError(
            "Runtime exists; use a fresh Kaggle session after preserving outputs."
        )
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(RUNTIME)], check=True)
    install = [
        sys.executable,
        "-m",
        "pip",
        "--python",
        str(RUNTIME / "bin/python"),
        "install",
        "--no-cache-dir",
        "pip",
        "-r",
        "requirements-neural.txt",
    ]
    # Host pip bootstraps the isolated runtime without relying on ensurepip.
    with (ROOT / "setup_install.log").open("x") as log:
        with subprocess.Popen(
            install,
            cwd=ROOT,
            env=environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ) as process:
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
            if process.wait():
                raise RuntimeError("Dependency installation failed; inspect setup_install.log.")
    run(
        [
            "-c",
            "import torch; assert torch.cuda.is_available(), 'CUDA required'; "
            "print(torch.__version__, torch.cuda.get_device_name(0))",
        ],
        "isolated_cuda.log",
    )
    freeze = subprocess.check_output(
        [str(RUNTIME / "bin/python"), "-m", "pip", "freeze"], text=True
    )
    (ROOT / "environment.txt").write_text(freeze)
    run(["scripts/fetch_peerj_materials.py"], "fetch.log")
    run(["-m", "pytest", "neural_tests", "-q"], "neural_tests.log")
    run(
        [
            "scripts/train_codebert.py",
            "--smoke",
            "--device",
            "cuda",
            "--output",
            "artifacts/gpu_session_smoke",
        ],
        "smoke.log",
    )
    run(
        [
            "scripts/train_codebert.py",
            "--preflight",
            "--preflight-length",
            "512",
            "--device",
            "cuda",
            "--micro-batch",
            "2",
            "--cache",
            str(CACHE),
            "--output",
            "artifacts/gpu_capacity_check",
        ],
        "capacity_check.log",
    )
    record("setup", "passed", note="Smoke/capacity checks are engineering checks only.")


def train():
    require_kaggle()
    status = json.loads(STATE.read_text())
    if status["stage"] != "setup" or status["status"] != "passed":
        raise RuntimeError("Successful setup is required before training.")
    record("training", "running", seeds=[0, 1, 2])
    run(
        [
            "scripts/run_codebert_seeds.py",
            "--device",
            "cuda",
            "--micro-batch",
            "2",
            "--cache",
            str(CACHE),
            "--output",
            "artifacts/full_codebert",
        ],
        "training_driver.log",
    )
    record("training", "completed")


def export():
    require_kaggle()
    status = json.loads(STATE.read_text())
    if status["stage"] != "training" or status["status"] != "completed":
        raise RuntimeError("All three training seeds must complete before export.")
    record("export", "running")
    run(
        [
            "scripts/export_codebert_results.py",
            "--study",
            "artifacts/full_codebert",
            "--context",
            str(ROOT),
            "--output",
            str(EVIDENCE),
        ],
        "export.log",
    )
    record(
        "export",
        "completed",
        evidence=str(EVIDENCE),
        note=(
            "Consistency checks passed. Human review and scientific confirmation remain required."
        ),
    )


def stage(function):
    try:
        function()
    except Exception as error:
        if Path("/kaggle/working").is_dir():
            record(function.__name__, "failed", error_type=type(error).__name__, error=str(error))
        raise


def main():
    for function in (preflight, setup, train, export):
        stage(function)
