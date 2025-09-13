import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "src" / "agents"
TESTS_DIR = REPO_ROOT / "tests"

# Banned patterns for agent code (line-scanned with optional inline suppression tokens)
# Note: MCP service is deprecated; CSV ingestion via pandas is permitted in agents.
BANNED_AGENT_PATTERNS = [
    (re.compile(r"duckdb\s*\.\s*connect\s*\("), None, "Use database manager abstraction instead of direct duckdb.connect in agents."),
    (re.compile(r"sqlite3\s*\.\s*connect\s*\("), None, "Avoid direct sqlite3.connect in agents; use centralized data access abstraction."),
    (re.compile(r"\bexecute\s*\("), "arch-allow-execute", "Direct execute() calls are not allowed in agents; use database manager abstraction."),
]

# Tests may not directly instantiate agents (use orchestrator/registry-driven creation)
DIRECT_AGENT_CTOR = re.compile(r"(?<!\.)\bA9_[A-Za-z0-9_]+\s*\(")


def scan_files(base: Path):
    for path in base.rglob("*.py"):
        if any(part in {".venv", "_build", "node_modules", "dist", "build"} for part in path.parts):
            continue
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(errors="ignore")

def lint_agents() -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for py in scan_files(AGENTS_DIR):
        text = read_text(py)
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for regex, allow_token, message in BANNED_AGENT_PATTERNS:
                if regex.search(line):
                    if allow_token and allow_token in line:
                        continue
                    violations.append((f"{py}:{i}", f"{message} :: {stripped}"))
    return violations


def lint_tests() -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for py in scan_files(TESTS_DIR):
        text = read_text(py)
        # File-level suppression token (align with tests/architecture/test_architecture_compliance.py)
        if "arch-allow-direct-agent-construction" in text:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("class "):
                continue
            # Skip obvious comments-only lines
            if stripped.startswith("#"):
                continue
            if re.search(r"(?<!\.)\bA9_[A-Za-z0-9_]+\s*\(", line):
                # Line-level suppression token
                if "arch-allow-agent-ctor" in line:
                    continue
                violations.append((f"{py}:{i}", f"Direct agent construction is not allowed in tests :: {line.strip()}"))
    return violations


def main() -> int:
    violations = []
    agent_violations = lint_agents()
    test_violations = lint_tests()
    if agent_violations:
        print("[ARCH] Agent violations:")
        for loc, msg in agent_violations:
            print(f" - {loc} -> {msg}")
        violations.extend(agent_violations)
    if test_violations:
        print("[ARCH] Test violations:")
        for loc, msg in test_violations:
            print(f" - {loc} -> {msg}")
        violations.extend(test_violations)
    if violations:
        print(f"\n[ARCH] Found {len(violations)} architecture violation(s).", file=sys.stderr)
        return 1
    print("[ARCH] No architecture violations detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
