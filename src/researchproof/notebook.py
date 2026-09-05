from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

CellOrdering = Literal["document", "execution"]


@dataclass(frozen=True)
class NotebookCell:
    document_index: int
    execution_count: int | None
    source: str


@dataclass(frozen=True)
class NotebookProgram:
    ordering: CellOrdering
    cells: tuple[NotebookCell, ...]
    source: str


class NotebookError(ValueError):
    """Raised when a notebook cannot be normalized safely."""


def _source_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "".join(value)
    raise NotebookError("code cell source must be a string or a list of strings")


def _comment_notebook_commands(source: str) -> str:
    normalized: list[str] = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("%", "!")):
            indentation = line[: len(line) - len(stripped)]
            normalized.append(f"{indentation}# researchproof-notebook-command: {stripped}")
        else:
            normalized.append(line)
    return "\n".join(normalized)


def normalize_notebook(payload: dict[str, Any], ordering: CellOrdering) -> NotebookProgram:
    if ordering not in {"document", "execution"}:
        raise NotebookError("ordering must be 'document' or 'execution'")
    raw_cells = payload.get("cells")
    if not isinstance(raw_cells, list):
        raise NotebookError("notebook must contain a cells list")
    cells: list[NotebookCell] = []
    for index, raw in enumerate(raw_cells):
        if not isinstance(raw, dict) or raw.get("cell_type") != "code":
            continue
        execution_count = raw.get("execution_count")
        if execution_count is not None and (
            isinstance(execution_count, bool) or not isinstance(execution_count, int)
        ):
            raise NotebookError(f"cell {index} has an invalid execution_count")
        cells.append(
            NotebookCell(
                document_index=index,
                execution_count=execution_count,
                source=_comment_notebook_commands(_source_text(raw.get("source", ""))),
            )
        )
    if ordering == "execution":
        cells.sort(
            key=lambda cell: (
                cell.execution_count is None,
                cell.execution_count if cell.execution_count is not None else cell.document_index,
                cell.document_index,
            )
        )
    sections = [
        (
            f"# --- cell {cell.document_index}; execution_count="
            f"{cell.execution_count if cell.execution_count is not None else 'none'} ---\n"
            f"{cell.source.rstrip()}"
        )
        for cell in cells
    ]
    source = "\n\n".join(sections).rstrip() + "\n" if sections else ""
    return NotebookProgram(ordering=ordering, cells=tuple(cells), source=source)


def load_notebook(path: Path, ordering: CellOrdering = "document") -> NotebookProgram:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise NotebookError(f"cannot read notebook {path}: {error}") from error
    if not isinstance(payload, dict):
        raise NotebookError("notebook root must be a JSON object")
    return normalize_notebook(payload, ordering)

