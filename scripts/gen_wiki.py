#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate the GitHub wiki from docs/wiki/.

The wiki is a mirror, never a place to write. Every page is a Markdown file under
`docs/wiki/`; `.github/workflows/wiki.yml` replaces the wiki's contents with this
script's output on every push to main. A wiki typed by hand would be a copy that
drifts, and one with a stray secret in it is public the moment it is saved.

Written into the directory named by `--out`, a flat tree as a wiki stores it:

* one `<Name>.md` per source page, with a comment at the top saying it is generated
  from `docs/wiki/<Name>.md` at `--commit`, so nobody edits the wiki by hand;
* `_Sidebar.md`, in the order of SIDEBAR_ORDER below;
* `_Footer.md`.

Links between pages are written as relative `Other-Page.md` links in the source and
become wiki links (`Other-Page`) in the output. Output is a function of the sources
and the commit: no clock, no hostname.

The script exits nonzero, writing nothing, when the tree is empty, a link points at a
page that does not exist, a page is missing from the sidebar order (or the order names
a page that does not exist), or a source file contains a forbidden string.

Usage:
    python scripts/gen_wiki.py --out wiki-out --commit "$SOURCE_SHA"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "docs" / "wiki"
REPO_URL = "https://github.com/Renegade-Penguin/LLMFAO"

# The sidebar order, and the complete list of pages. A page not listed here fails the build.
SIDEBAR_ORDER = [
    "Home",
    "Architecture",
    "Safety-Model",
    "Twitch-Bot-Account",
    "Events-and-Live-State",
    "Queue-and-Rate-Limits",
    "Deployment",
    "Persona",
    "Roadmap",
    "How-We-Build",
    "FAQ",
]

# Forbidden strings. A wiki is public the moment it is published, and the maintainer's
# amateur radio callsign and grid square, machine identifiers and credentials must never
# reach it. Each rule is (label, compiled pattern); any match in any source file fails
# the build. Keep this table at the top: it is the thing a reviewer should read first.
GRID_SQUARE_PLACEHOLDERS = {"FN31pr"}
FORBIDDEN: list[tuple[str, re.Pattern[str]]] = [
    ("callsign", re.compile(r"callsign", re.IGNORECASE)),
    # two letters, two digits, two letters: a Maidenhead grid square such as FN31pr
    ("grid square", re.compile(r"\b[A-Za-z]{2}[0-9]{2}[A-Za-z]{2}\b")),
    ("hostname", re.compile(r"hostname", re.IGNORECASE)),
    ("serial", re.compile(r"serial", re.IGNORECASE)),
    ("GitHub personal access token", re.compile(r"ghp_")),
    ("GitHub OAuth token", re.compile(r"gho_")),
    ("Slack bot token", re.compile(r"xoxb-")),
    ("AWS access key id", re.compile(r"AKIA")),
    ("private key block", re.compile(r"BEGIN PRIVATE KEY")),
    ("bearer token", re.compile(r"Bearer [^\s]{20,}")),
]

FENCE = re.compile(r"^\s*(```|~~~)")
PAGE_LINK = re.compile(r"(\]\()([^)\s#:]+)\.md(#[^)\s]*)?(\))")


class WikiError(Exception):
    """A tree the wiki cannot be generated from. Carries every problem found."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def load_pages(src: Path) -> dict[str, str]:
    """Page name -> source text, for every Markdown file directly under `src`."""
    if not src.is_dir():
        return {}
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(src.glob("*.md"))}


def forbidden_in(name: str, text: str) -> list[str]:
    """One problem line per forbidden match in a page."""
    problems: list[str] = []
    for label, pattern in FORBIDDEN:
        for match in pattern.finditer(text):
            if label == "grid square" and match.group(0) in GRID_SQUARE_PLACEHOLDERS:
                continue
            line = text.count("\n", 0, match.start()) + 1
            problems.append(f"{name}.md:{line}: forbidden string ({label})")
    return problems


def rewrite_links(name: str, text: str, pages: set[str]) -> tuple[str, list[str]]:
    """Turn `Page.md` / `Page.md#a` links into wiki links. Report links to missing pages."""
    problems: list[str] = []
    out: list[str] = []
    in_fence = False
    for number, line in enumerate(text.split("\n"), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
        if in_fence:
            out.append(line)
            continue

        def fix(m: re.Match[str], number: int = number) -> str:
            target = m.group(2)
            if "/" in target or target not in pages:
                problems.append(f"{name}.md:{number}: link to missing page {target}.md")
                return m.group(0)
            return m.group(1) + target + (m.group(3) or "") + m.group(4)

        out.append(PAGE_LINK.sub(fix, line))
    return "\n".join(out), problems


def sidebar() -> str:
    lines = [f"- [{n.replace('-', ' ')}]({n})" for n in SIDEBAR_ORDER]
    return "\n".join(lines) + "\n"


def footer(commit: str) -> str:
    if re.fullmatch(r"[0-9a-f]{7,40}", commit):
        source = f"[`{commit[:12]}`]({REPO_URL}/commit/{commit})"
    else:
        source = f"`{commit}`"
    return (
        f"Generated from `docs/wiki/` at commit {source}. "
        f"Edit the files in the repository ({REPO_URL}), not this wiki.\n"
    )


def header(name: str, commit: str) -> str:
    return (
        f"<!-- Generated from docs/wiki/{name}.md at {commit}. "
        "Do not edit this page in the wiki: the next publish replaces it. -->\n\n"
    )


def render(src: Path, commit: str) -> dict[str, str]:
    """Every wiki file, filename -> content. Raises WikiError listing all problems."""
    pages = load_pages(src)
    problems: list[str] = []
    if not pages:
        raise WikiError([f"no pages found in {src}: refusing to produce an empty wiki"])

    for name in sorted(set(pages) - set(SIDEBAR_ORDER)):
        problems.append(f"{name}.md is not listed in SIDEBAR_ORDER")
    for name in SIDEBAR_ORDER:
        if name not in pages:
            problems.append(f"SIDEBAR_ORDER names {name}, which has no file in {src}")
    names = set(pages)
    files: dict[str, str] = {}
    for name, text in pages.items():
        problems.extend(forbidden_in(name, text))
        body, link_problems = rewrite_links(name, text, names)
        problems.extend(link_problems)
        if not body.strip():
            problems.append(f"{name}.md is empty")
        files[f"{name}.md"] = header(name, commit) + body.rstrip("\n") + "\n"
    if problems:
        raise WikiError(problems)
    files["_Sidebar.md"] = sidebar()
    files["_Footer.md"] = footer(commit)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the GitHub wiki from docs/wiki/.")
    parser.add_argument("--out", type=Path, required=True, help="directory to write the wiki into")
    parser.add_argument("--commit", default="unknown", help="source commit, for the headers")
    parser.add_argument(
        "--src", type=Path, default=SRC_DIR, help="source pages (default docs/wiki)"
    )
    args = parser.parse_args(argv)

    try:
        files = render(args.src, args.commit)
    except WikiError as e:
        for problem in e.problems:
            print(f"gen_wiki: {problem}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (args.out / filename).write_text(content, encoding="utf-8")
    print(f"wrote {len(files)} wiki files to {args.out}")
    for filename in sorted(files):
        print(f"  {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
