#!/usr/bin/env python3
"""Ensure visible site changes also update changelog.html."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = "changelog.html"
WATCHED_EXTENSIONS = (".html", ".css", ".js")
IGNORED_PREFIXES = (
    ".github/",
    "scripts/",
)


def git(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files() -> set[str]:
    files: set[str] = set()
    for args in (
        ("diff", "--name-only", "--cached"),
        ("diff", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    ):
        files.update(git(*args))
    return files


def needs_changelog(path: str) -> bool:
    if path == CHANGELOG:
        return False
    if any(path.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return False
    return path.endswith(WATCHED_EXTENSIONS)


def main() -> int:
    files = changed_files()
    watched = sorted(path for path in files if needs_changelog(path))

    if watched and CHANGELOG not in files:
        print("Changelog update is required.")
        print("Changed public files:")
        for path in watched:
            print(f"- {path}")
        print(f"Add this change to {CHANGELOG}.")
        return 1

    print("Changelog check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
