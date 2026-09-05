from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(ValueError):
    """Raised when a benchmark manifest is incomplete or internally inconsistent."""


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{name} must be a non-empty string")


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class BenchmarkManifest:
    dataset_id: str
    dataset_checksum: str
    template_id: str
    template_version: str
    fault_family: str
    fault_severity: str
    injector_version: str
    seed: int
    split_policy: str
    model_name: str
    model_parameters: dict[str, Any]
    expected_fault: bool
    expected_evidence: tuple[str, ...]
    expected_repair: str
    environment_lock: str

    def __post_init__(self) -> None:
        for name in (
            "dataset_id",
            "template_id",
            "template_version",
            "fault_family",
            "fault_severity",
            "injector_version",
            "split_policy",
            "model_name",
            "expected_repair",
            "environment_lock",
        ):
            _require_text(name, getattr(self, name))

        if not _SHA256_PATTERN.fullmatch(self.dataset_checksum):
            raise ManifestError("dataset_checksum must be a lowercase SHA-256 digest")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ManifestError("seed must be a non-negative integer")
        if not isinstance(self.model_parameters, dict):
            raise ManifestError("model_parameters must be a dictionary")
        if not isinstance(self.expected_fault, bool):
            raise ManifestError("expected_fault must be a boolean")
        if not self.expected_evidence:
            raise ManifestError("expected_evidence must contain at least one observable item")
        if any(not isinstance(item, str) or not item.strip() for item in self.expected_evidence):
            raise ManifestError("expected_evidence entries must be non-empty strings")

    @property
    def case_id(self) -> str:
        digest = hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()
        return f"rp-{digest[:16]}"

    def to_dict(self, *, include_case_id: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_evidence"] = list(self.expected_evidence)
        if include_case_id:
            payload = {"case_id": self.case_id, **payload}
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BenchmarkManifest:
        values = dict(payload)
        supplied_case_id = values.pop("case_id", None)
        values["expected_evidence"] = tuple(values.get("expected_evidence", ()))
        try:
            manifest = cls(**values)
        except TypeError as error:
            raise ManifestError(f"manifest fields are invalid: {error}") from error
        if supplied_case_id is not None and supplied_case_id != manifest.case_id:
            raise ManifestError("case_id does not match the manifest contents")
        return manifest

    def write(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(include_case_id=True), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def read(cls, source: Path) -> BenchmarkManifest:
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ManifestError(f"cannot read manifest {source}: {error}") from error
        if not isinstance(payload, dict):
            raise ManifestError("manifest root must be a JSON object")
        return cls.from_dict(payload)


def dataset_checksum(features: np.ndarray, target: np.ndarray) -> str:
    """Return a stable checksum that includes array shape, dtype, and content."""

    hasher = hashlib.sha256()
    for name, values in (("features", features), ("target", target)):
        array = np.ascontiguousarray(values)
        hasher.update(name.encode("utf-8"))
        hasher.update(str(array.shape).encode("ascii"))
        hasher.update(array.dtype.str.encode("ascii"))
        hasher.update(array.tobytes(order="C"))
    return hasher.hexdigest()
