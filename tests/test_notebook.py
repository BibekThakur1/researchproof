import ast
import json

import pytest

from researchproof.notebook import NotebookError, load_notebook, normalize_notebook


def notebook_payload():
    return {
        "cells": [
            {"cell_type": "markdown", "source": "Heading"},
            {"cell_type": "code", "execution_count": 2, "source": ["value = 2\n"]},
            {"cell_type": "code", "execution_count": 1, "source": "value = 1\n"},
            {"cell_type": "code", "execution_count": None, "source": "%matplotlib inline\n"},
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def test_document_and_execution_order_are_distinct() -> None:
    payload = notebook_payload()
    document = normalize_notebook(payload, "document")
    execution = normalize_notebook(payload, "execution")
    assert [cell.document_index for cell in document.cells] == [1, 2, 3]
    assert [cell.document_index for cell in execution.cells] == [2, 1, 3]


def test_notebook_commands_are_preserved_as_parseable_comments() -> None:
    program = normalize_notebook(notebook_payload(), "document")
    assert "researchproof-notebook-command" in program.source
    ast.parse(program.source)


def test_load_notebook_reads_json(tmp_path) -> None:
    path = tmp_path / "example.ipynb"
    path.write_text(json.dumps(notebook_payload()), encoding="utf-8")
    program = load_notebook(path, "execution")
    assert len(program.cells) == 3


def test_invalid_execution_count_is_rejected() -> None:
    payload = notebook_payload()
    payload["cells"][1]["execution_count"] = "second"
    with pytest.raises(NotebookError, match="execution_count"):
        normalize_notebook(payload, "execution")

