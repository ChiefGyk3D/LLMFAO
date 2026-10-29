# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""The documented module layout exists, and the repo honors the hypeman availability rule."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

SEAMS = ["events", "pipeline", "queue", "gate", "actions", "persona"]
SRC = Path(__file__).resolve().parent.parent / "src" / "llmfao"


@pytest.mark.parametrize("name", SEAMS)
def test_seam_module_is_documented(name: str) -> None:
    mod = importlib.import_module(f"llmfao.{name}")
    assert mod.__doc__ and len(mod.__doc__.strip()) > 40


def test_package_doc_lists_every_seam() -> None:
    import llmfao

    assert llmfao.__doc__
    for name in SEAMS:
        assert f"llmfao.{name}" in llmfao.__doc__


def test_source_never_reads_dot_enabled() -> None:
    files = list(SRC.glob("*.py"))
    assert files, "nothing collected"
    pattern = re.compile(r"\.enabled\b")
    offenders = [f.name for f in files if pattern.search(f.read_text(encoding="utf-8"))]
    assert offenders == []


def test_enabled_guard_bites() -> None:
    assert re.search(r"\.enabled\b", "if provider.enabled:")
