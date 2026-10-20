"""Small, hash-checked neural evidence transfers; consistency is not provenance proof."""

import hashlib
import json
import math
import zipfile
from pathlib import Path

from researchproof.neural_study import analyze_runs

MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
SCHEMA = "researchproof-codebert-evidence-v1"
RUN_FILES = ("run.json", "predictions.json", "training.json")
CONTEXT_FILES = ("environment.txt", "source_hashes.json", "startup.json", "isolated_cuda.log")
EXPECTED_FILES = (
    {f"seed{seed}/{name}" for seed in (0, 1, 2) for name in RUN_FILES}
    | {f"seed{seed}.log" for seed in (0, 1, 2)}
    | {"analysis.json", "tables.md"}
    | set(CONTEXT_FILES)
)


def _json(raw):
    return json.loads(raw)


def validate_files(files):
    if set(files) != EXPECTED_FILES:
        raise ValueError("unexpected or missing evidence files")
    if any(len(raw) > MAX_MEMBER_BYTES for raw in files.values()):
        raise ValueError("evidence member exceeds size limit")
    if sum(map(len, files.values())) > MAX_ARCHIVE_BYTES:
        raise ValueError("evidence archive exceeds size limit")
    hashes = _json(files["source_hashes.json"])
    startup = _json(files["startup.json"])
    check = startup.get("cuda_check", {})
    if check.get("exit_code") != 0 or _json(check.get("stdout", "{}")).get("cuda") is not True:
        raise ValueError("missing successful CUDA startup diagnostic")
    implementation = hashes.get("scripts/train_codebert.py")
    runs = []
    for seed in (0, 1, 2):
        run = _json(files[f"seed{seed}/run.json"])
        records = _json(files[f"seed{seed}/predictions.json"])
        losses = _json(files[f"seed{seed}/training.json"])
        if run.get("seed") != seed:
            raise ValueError("seed metadata differs from directory")
        if (
            not isinstance(losses, list)
            or len(losses) != 4
            or any(type(loss) not in (int, float) or not math.isfinite(loss) for loss in losses)
            or run.get("training_loss") != losses
        ):
            raise ValueError("missing, nonfinite or inconsistent training losses")
        if not implementation or run.get("implementation_sha256") != implementation:
            raise ValueError("training implementation differs from the packaged source manifest")
        if not files[f"seed{seed}.log"].strip():
            raise ValueError("missing training log")
        runs.append((run, records))
    report = analyze_runs(runs)
    if _json(files["analysis.json"]) != report:
        raise ValueError("saved analysis differs from recomputed results")
    if files["tables.md"].decode() != render_tables(report):
        raise ValueError("saved tables differ from recomputed results")
    return report


def render_tables(report):
    lines = [
        "# CodeBERT: completed-run descriptive results",
        "",
        "Generated from all three prespecified seeds. This is an explored test split.",
        "Seed variation does not estimate uncertainty on new repositories.",
        "",
        "| Seed | Precision | Recall | F1 | False-positive rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["per_seed"]:
        metrics = item["metrics"]
        values = " | ".join(
            f"{metrics[key]:.4f}" for key in ("precision", "recall", "f1", "false_positive_rate")
        )
        lines.append(f"| {item['seed']} | {values} |")
    lines += [
        "",
        "| Seed | Edit | Eligible pairs | Visible pairs | Flips | Harmful | Corrective |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report["per_seed"]:
        for variant, edit in item["edits"].items():
            values = " | ".join(
                str(edit[key])
                for key in (
                    "paired",
                    "token_changed",
                    "flips",
                    "correct_to_wrong",
                    "wrong_to_correct",
                )
            )
            lines.append(f"| {item['seed']} | {variant} | {values} |")
    return "\n".join(lines) + "\n"


def build_archive(study, context, output):
    """Requires complete runs; excludes checkpoints, caches and third-party source data."""
    study, context, output = Path(study), Path(context), Path(output)
    if output.exists():
        raise FileExistsError(output)
    files = {}
    runs = []
    for seed in (0, 1, 2):
        for name in RUN_FILES:
            files[f"seed{seed}/{name}"] = (study / f"seed{seed}" / name).read_bytes()
        files[f"seed{seed}.log"] = (study / f"seed{seed}.log").read_bytes()
        runs.append(
            (
                _json(files[f"seed{seed}/run.json"]),
                _json(files[f"seed{seed}/predictions.json"]),
            )
        )
    report = analyze_runs(runs)
    files["analysis.json"] = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode()
    files["tables.md"] = render_tables(report).encode()
    for name in CONTEXT_FILES:
        files[name] = (context / name).read_bytes()
    validate_files(files)
    manifest = {
        "schema": SCHEMA,
        "status": "three_complete_seeds_consistency_checked",
        "checkpoints_included": False,
        "files_sha256": {
            name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(files.items())
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            archive.writestr(name, raw)
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    return report


def inspect_archive(path, source_manifest=None):
    """Recompute results directly from ZIP; never extract or execute its contents."""
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(set(names)) != len(names) or set(names) != EXPECTED_FILES | {"MANIFEST.json"}:
            raise ValueError("duplicate, missing or unexpected archive paths")
        if any(item.file_size > MAX_MEMBER_BYTES for item in infos):
            raise ValueError("archive member exceeds size limit")
        if sum(item.file_size for item in infos) > MAX_ARCHIVE_BYTES:
            raise ValueError("archive exceeds size limit")
        files = {name: archive.read(name) for name in names}
    manifest = _json(files.pop("MANIFEST.json"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("unknown evidence archive schema")
    actual = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    if actual != manifest.get("files_sha256"):
        raise ValueError("evidence checksum mismatch")
    if source_manifest is not None:
        expected = _json(Path(source_manifest).read_bytes())
        if _json(files["source_hashes.json"]) != expected:
            raise ValueError("returned source manifest differs from the frozen job package")
    return validate_files(files)
