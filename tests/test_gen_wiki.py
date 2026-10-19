# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
"""The wiki generator: it works on the real docs, and refuses every bad tree."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_wiki  # noqa: E402  # reason: scripts/ is not a package, so the path is set first

REAL_DOCS = ROOT / "docs" / "wiki"


def make_tree(root: Path, extra: dict[str, str] | None = None) -> Path:
    """A minimal valid source tree: every sidebar page, trivially filled."""
    src = root / "src"
    src.mkdir()
    for name in gen_wiki.SIDEBAR_ORDER:
        (src / f"{name}.md").write_text(f"# {name}\n\nbody\n", encoding="utf-8")
    for name, text in (extra or {}).items():
        (src / f"{name}.md").write_text(text, encoding="utf-8")
    return src


def run(src: Path, out: Path) -> int:
    return gen_wiki.main(["--src", str(src), "--out", str(out), "--commit", "abc1234"])


def test_real_docs_generate(tmp_path: Path) -> None:
    out = tmp_path / "out"
    assert gen_wiki.main(["--out", str(out), "--commit", "abc1234"]) == 0
    written = {p.name for p in out.iterdir()}
    assert "Home.md" in written
    assert {"_Sidebar.md", "_Footer.md"} <= written
    assert len(written) == len(gen_wiki.SIDEBAR_ORDER) + 2


def test_every_real_page_is_listed() -> None:
    on_disk = {p.stem for p in REAL_DOCS.glob("*.md")}
    assert on_disk == set(gen_wiki.SIDEBAR_ORDER)


def test_sidebar_follows_the_order(tmp_path: Path) -> None:
    out = tmp_path / "out"
    assert run(make_tree(tmp_path), out) == 0
    links = [
        line.split("](")[1].rstrip(")")
        for line in (out / "_Sidebar.md").read_text().splitlines()
        if line
    ]
    assert links == gen_wiki.SIDEBAR_ORDER


def test_header_names_source_and_commit(tmp_path: Path) -> None:
    out = tmp_path / "out"
    assert run(make_tree(tmp_path), out) == 0
    first = (out / "Architecture.md").read_text().splitlines()[0]
    assert "docs/wiki/Architecture.md" in first
    assert "abc1234" in first
    assert "abc1234" in (out / "_Footer.md").read_text()


def test_links_are_rewritten(tmp_path: Path) -> None:
    src = make_tree(
        tmp_path,
        {
            "Home": (
                "# Home\n\nSee [a](Safety-Model.md) and [b](FAQ.md#why) and "
                "[ext](https://example.com/x.md).\n\n```\n[code](Safety-Model.md)\n```\n"
            )
        },
    )
    out = tmp_path / "out"
    assert run(src, out) == 0
    text = (out / "Home.md").read_text()
    assert "[a](Safety-Model)" in text
    assert "[b](FAQ#why)" in text
    assert "(https://example.com/x.md)" in text
    assert "[code](Safety-Model.md)" in text


def test_empty_tree_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    assert run(src, out) != 0
    assert not out.exists()
    assert "empty wiki" in capsys.readouterr().err


def test_missing_link_target_fails(tmp_path: Path) -> None:
    src = make_tree(tmp_path, {"Home": "# Home\n\n[x](No-Such-Page.md)\n"})
    assert run(src, tmp_path / "out") != 0


def test_page_not_in_sidebar_fails(tmp_path: Path) -> None:
    src = make_tree(tmp_path, {"Orphan": "# Orphan\n\ntext\n"})
    assert run(src, tmp_path / "out") != 0


def test_sidebar_entry_without_page_fails(tmp_path: Path) -> None:
    src = make_tree(tmp_path)
    (src / "FAQ.md").unlink()
    assert run(src, tmp_path / "out") != 0


FORBIDDEN_SAMPLES = [
    "my callsign is here",
    "CALLSIGN",
    "grid is AB12cd",
    "the hostname of the box",
    "the Serial number",
    "token ghp_" + "a" * 20,
    "token gho_" + "a" * 20,
    "token xoxb-" + "1" * 12,
    "key AKIA" + "A" * 16,
    "-----BEGIN PRIVATE KEY-----",
    "Authorization: Bearer " + "a" * 24,
]


@pytest.mark.parametrize("sample", FORBIDDEN_SAMPLES)
def test_forbidden_string_fails(tmp_path: Path, sample: str) -> None:
    src = make_tree(tmp_path, {"FAQ": f"# FAQ\n\n{sample}\n"})
    out = tmp_path / "out"
    assert run(src, out) != 0
    assert not out.exists()


@pytest.mark.parametrize("placeholder", ["FN31pr", "N0CALL", "N0TST"])
def test_placeholders_are_allowed(tmp_path: Path, placeholder: str) -> None:
    src = make_tree(tmp_path, {"FAQ": f"# FAQ\n\nuse {placeholder} here\n"})
    assert run(src, tmp_path / "out") == 0


def test_short_bearer_is_not_a_token(tmp_path: Path) -> None:
    src = make_tree(tmp_path, {"FAQ": "# FAQ\n\nsend a Bearer header\n"})
    assert run(src, tmp_path / "out") == 0
