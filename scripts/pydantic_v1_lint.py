#!/usr/bin/env python
"""
Simple linter to flag Pydantic v1 API usage in the repository.

Usage:
  python scripts/pydantic_v1_lint.py [--paths src tests]

Ignore rules:
  - File-level: add a top-level comment 'pydantic-lint: ignore file' to skip the file
  - Line-level: add trailing comment '# pydantic-lint: allow' to allow a specific occurrence

Exit codes:
  0 - no violations found
  1 - violations found

This is a lightweight regex-based scanner intended for pre-commit. Keep patterns conservative
and easy to maintain. Prefer replacing flagged usages with Pydantic v2 equivalents.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Iterable, List, Tuple

# Directories to skip
SKIP_DIRS = {".git", ".hg", ".svn", ".tox", ".venv", "venv", "node_modules", "__pycache__"}

# File extensions to scan
PY_EXT = {".py"}

# Pydantic v1 -> v2 migration flags:
# Keep patterns specific and anchored to reduce false positives.
PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("BaseModel.dict() -> model_dump()", re.compile(r"\.dict\s*\(", re.IGNORECASE | re.ASCII)),
    ("BaseModel.json() -> model_dump_json()", re.compile(r"\.json\s*\(", re.IGNORECASE | re.ASCII)),
    ("update_forward_refs() -> model_rebuild()", re.compile(r"update_forward_refs\s*\(", re.IGNORECASE | re.ASCII)),
    ("parse_obj/parse_raw -> model_validate", re.compile(r"parse_(obj|raw)\s*\(", re.IGNORECASE | re.ASCII)),
    ("parse_obj_as -> TypeAdapter[T].validate_python", re.compile(r"parse_obj_as\s*\(", re.IGNORECASE | re.ASCII)),
    # Restrict copy detection to cases where deep=True is specified to avoid false positives
    ("BaseModel.copy(deep=True) -> model_copy(deep=True)", re.compile(r"\.copy\s*\([^)]*deep\s*=\s*True", re.IGNORECASE | re.ASCII)),
    ("@validator -> @field_validator", re.compile(r"@validator\b", re.IGNORECASE | re.ASCII)),
    ("@root_validator -> @model_validator", re.compile(r"@root_validator\b", re.IGNORECASE | re.ASCII)),
    ("schema()/schema_json() -> model_json_schema()", re.compile(r"\.(schema|schema_json)\s*\(", re.IGNORECASE | re.ASCII)),
]

FILE_IGNORE_TOKEN = "pydantic-lint: ignore file"
LINE_ALLOW_TOKEN = "pydantic-lint: allow"


def should_skip_dir(dirname: str) -> bool:
    base = os.path.basename(dirname)
    return base in SKIP_DIRS


def iter_python_files(paths: Iterable[str]) -> Iterable[str]:
    for root in paths:
        if not os.path.exists(root):
            continue
        if os.path.isfile(root):
            _, ext = os.path.splitext(root)
            if ext in PY_EXT:
                yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune dirs
            dirnames[:] = [d for d in dirnames if not should_skip_dir(os.path.join(dirpath, d))]
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                if ext in PY_EXT:
                    yield os.path.join(dirpath, fname)


def scan_file(path: str) -> List[str]:
    """Return list of violation messages for a file."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return [f"ERROR reading {path}: {e}"]

    # File-level ignore
    if any(FILE_IGNORE_TOKEN in (ln or "") for ln in lines[:5]):
        return []

    violations: List[str] = []
    for i, line in enumerate(lines, start=1):
        # Line-level allow
        if LINE_ALLOW_TOKEN in line:
            continue
        for desc, pattern in PATTERNS:
            if pattern.search(line):
                snippet = line.strip()
                violations.append(f"{path}:{i}: {desc}: {snippet}")
    return violations


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Lint for Pydantic v1 API usage")
    parser.add_argument("--paths", nargs="*", default=["src", "tests"], help="Paths to scan")
    args = parser.parse_args(argv)

    files = list(iter_python_files(args.paths))
    all_violations: List[str] = []
    for fpath in files:
        all_violations.extend(scan_file(fpath))

    if all_violations:
        print("Pydantic v1 API usage detected (please migrate to v2):", file=sys.stderr)
        for msg in all_violations:
            print(msg, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
