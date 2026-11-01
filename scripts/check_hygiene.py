#!/usr/bin/env python3
"""
Repository hygiene & secret gate for Quantum Anchored Memory.
Fails if any tracked file contains:
  1. Hardcoded personal paths (Windows C:\\Users\\..., /Users/..., drive paths)
  2. Committed IBM/IQM API keys or JSON credential blobs
  3. Insecure CLI `--token` argument definitions in Python/Docker entrypoints
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SELF_REL = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "hardcoded-user-path",
        re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]+|(?<![A-Za-z0-9_])/Users/[A-Za-z0-9._-]+/)"),
    ),
    (
        "hardcoded-windows-drive",
        re.compile(r"\b[D-Z]:[\\/]+[^\s\"']+"),
    ),
    (
        "committed-api-key-json",
        re.compile(r'"apikey"\s*:\s*"[A-Za-z0-9_\-]{25,}"'),
    ),
    (
        "committed-env-token",
        re.compile(r"IBM_QUANTUM_(?:API_)?TOKEN\s*=\s*['\"]?[A-Za-z0-9_\-]{30,}"),
    ),
    (
        "cli-token-flag",
        re.compile(r'add_argument\(\s*["\']--token["\']'),
    ),
]


def tracked_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        text=True,
    )
    return [REPO_ROOT / line for line in out.splitlines() if line.strip()]


def main() -> int:
    files = tracked_files()
    findings: list[str] = []

    for fpath in files:
        rel = fpath.relative_to(REPO_ROOT).as_posix()
        if rel == SELF_REL or not fpath.is_file():
            continue
        try:
            text = fpath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            for name, rx in PATTERNS:
                if rx.search(line):
                    findings.append(f"{rel}:{lineno}: [{name}] {line.strip()[:100]}")

    if findings:
        print(f"HYGIENE CHECK FAILED ({len(findings)} finding(s)):")
        for item in findings:
            print(f"  ! {item}")
        return 1

    print(f"HYGIENE CHECK PASSED: {len(files)} tracked file(s) clean (0 personal paths, 0 secrets, 0 --token flags).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
