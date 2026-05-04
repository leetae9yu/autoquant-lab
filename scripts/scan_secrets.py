#!/usr/bin/env python3
"""Scan Python and text files for likely hardcoded secrets."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCLUDED_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
DEFAULT_EXCLUDED_FILES = {".env"}
SCANNED_SUFFIXES = {".py", ".txt"}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "assignment_secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*=\s*['\"]([^'\"]{8,})['\"]"
        ),
    ),
    ("hex_32_plus", re.compile(r"\b[a-fA-F0-9]{32,}\b")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan .py and .txt files for likely hardcoded secrets.")
    parser.add_argument("root", nargs="?", type=Path, default=PROJECT_ROOT, help="Workspace root to scan.")
    return parser.parse_args()


def should_scan_file(path: Path) -> bool:
    return path.suffix in SCANNED_SUFFIXES and path.name not in DEFAULT_EXCLUDED_FILES


def iter_candidate_files(root: Path):
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in DEFAULT_EXCLUDED_DIRS]
        for filename in filenames:
            path = Path(current_root) / filename
            if should_scan_file(path):
                yield path


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        print(f"Warning: could not read {path}: {exc}")
        return findings

    for line_number, line in enumerate(lines, start=1):
        for pattern_name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((line_number, pattern_name, line.strip()))
    return findings


def redact(line: str) -> str:
    redacted = re.sub(r"(['\"])([^'\"]{4})[^'\"]{4,}([^'\"]{4})(['\"])", r"\1\2...\3\4", line)
    return re.sub(r"\b([a-fA-F0-9]{8})[a-fA-F0-9]{16,}([a-fA-F0-9]{8})\b", r"\1...\2", redacted)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    all_findings: list[tuple[Path, int, str, str]] = []

    for path in iter_candidate_files(root):
        for line_number, pattern_name, line in scan_file(path):
            all_findings.append((path, line_number, pattern_name, line))

    if not all_findings:
        print(f"No potential secrets found in .py/.txt files under {root}")
        return

    print(f"Potential secrets found: {len(all_findings)}")
    for path, line_number, pattern_name, line in all_findings:
        rel_path = path.relative_to(root)
        print(f"{rel_path}:{line_number}: {pattern_name}: {redact(line)}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
