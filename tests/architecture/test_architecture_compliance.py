import os
import re
from pathlib import Path

# Architecture compliance tests to prevent drift
# - Agents must not execute SQL or read CSVs directly
# - Tests must not directly instantiate agents (must use orchestrator/registry)
# - Data access in agents must go through the MCP client/service (enforced implicitly by banning direct DB patterns)

REPO_ROOT = Path(__file__).resolve().parents[2]

AGENTS_DIR = REPO_ROOT / "src" / "agents"
TESTS_DIR = REPO_ROOT / "tests"

# File-level allowance/deprecation tokens
DEPRECATION_TOKEN = "DEPRECATION WARNING"
ALLOW_DB_IN_AGENT_FILE_TOKEN = "arch-allow-db-in-agent file"

# Banned patterns in agent code (any file under src/agents/**)
# Keep simple and conservative; we can iterate as needed
BANNED_AGENT_PATTERNS = [
    (re.compile(r"duckdb\s*\.\s*connect\s*\("), None),
    # direct DB execute on any connection-like object; allow suppression with '# arch-allow-execute'
    (re.compile(r"\.\s*execute\s*\("), "arch-allow-execute"),
    # CSV ingestion must not occur in agents; allow suppression with '# arch-allow-read_csv'
    (re.compile(r"(pandas|pd)\s*\.\s*read_csv\s*\("), "arch-allow-read_csv"),
    (re.compile(r"sqlite3\s*\.\s*connect\s*\("), None),
]

# Tests may not directly instantiate agent classes (must use orchestrator/registry)
# Heuristic: a bare constructor call like `A9_Something_Agent(...)` is disallowed.
# We exclude `class A9_...(` lines (class declarations) and calls to `.create(` factories are allowed.
DIRECT_AGENT_CTOR_REGEX = re.compile(r"(?<!\.)\bA9_[A-Za-z0-9_]+\s*\(")


def _scan_files(base: Path):
    for path in base.rglob("*.py"):
        # Skip compiled/migrations if any, or generated folders if added later
        if any(part in {".venv", "_build", "node_modules", "dist", "build"} for part in path.parts):
            continue
        # Skip backup files
        if str(path).endswith(".bak"):
            continue
        yield path


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(errors="ignore")

def test_no_banned_db_patterns_in_agents():
    violations = []
    for py in _scan_files(AGENTS_DIR):
        text = _read_text(py)
        head = "\n".join(text.splitlines()[:20])
        # Skip deprecated files or explicitly allowed ones
        if (DEPRECATION_TOKEN in head) or (ALLOW_DB_IN_AGENT_FILE_TOKEN in text):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            # Skip obvious comments-only lines
            if stripped.startswith("#"):
                continue
            for regex, allow_token in BANNED_AGENT_PATTERNS:
                if regex.search(line):
                    if allow_token and allow_token in line:
                        continue  # suppressed intentionally
                    violations.append((str(py), i, stripped))
    assert not violations, (
        "Direct DB/CSV patterns are not allowed in agents. Use MCP client/service instead.\n"
        "Examples: duckdb.connect, .execute(), pandas.read_csv, sqlite3.connect\n"
        "Add '# arch-allow-execute' or '# arch-allow-read_csv' inline to suppress where appropriate.\n"
        "Violations:\n" + "\n".join(f"{p}:{ln} :: {src}" for p, ln, src in violations)
    )


def test_no_direct_agent_construction_in_tests():
    violations = []
    for py in _scan_files(TESTS_DIR):
        text = _read_text(py)
        # File-level suppression token
        if "arch-allow-direct-agent-construction" in text:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if line.strip().startswith("class "):
                continue
            # Disallow bare constructions like A9_Situation_Awareness_Agent(...)
            if re.search(r"(?<!\.)\bA9_[A-Za-z0-9_]+\s*\(", line):
                if "arch-allow-agent-ctor" in line:
                    continue
                violations.append((str(py), i, line.strip()))
    if violations:
        print(f"[ARCH][tests] Direct agent construction violations: {len(violations)}")
        for p, ln, src in violations:
            print(f" - {p}:{ln} :: {src}")
    assert not violations, (
        "Tests must not directly instantiate agents. Use orchestrator/registry-driven creation.\n" +
        "Add '# arch-allow-agent-ctor' on the line or '# arch-allow-direct-agent-construction' at top of file to temporarily suppress.\n" +
        "Violations listed above."
    )
