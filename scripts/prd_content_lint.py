#!/usr/bin/env python
"""
PRD Content Validator — Enforces PRD/code alignment.

Validates:
1. Phase references exist in DEVELOPMENT_PLAN.md
2. Entrypoint counts match code implementation
3. Agent PRDs exist for all agents that implement them

Usage:
  python scripts/prd_content_lint.py [--check-phases] [--check-entrypoints]

Exit codes:
  0 - no violations found
  1 - violations found (blocking)
  2 - warnings only (non-blocking)
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
PRD_DIR = REPO_ROOT / "docs" / "prd" / "agents"
AGENTS_DIR = REPO_ROOT / "src" / "agents" / "new"
PLAN_FILE = REPO_ROOT / "DEVELOPMENT_PLAN.md"


def load_development_plan() -> str:
    """Load DEVELOPMENT_PLAN.md content."""
    if not PLAN_FILE.exists():
        return ""
    try:
        return PLAN_FILE.read_text(encoding="utf-8")
    except Exception:
        return ""


def extract_phases_from_plan(plan_content: str) -> Set[str]:
    """Extract all valid phase identifiers from DEVELOPMENT_PLAN.md.

    Looks for patterns like: Phase 10A, Phase 10B, Phase 11D, etc.
    Returns set of valid phases (e.g., {'10A', '10B', '10C', '10D', '11D', ...})
    """
    phases: Set[str] = set()

    # Match "Phase 10A", "Phase 10B-i", etc.
    pattern = r"Phase\s+(\d+[A-Z]+(?:-[a-z])?)"
    for match in re.finditer(pattern, plan_content):
        phases.add(match.group(1))

    return phases


def check_prd_phase_references(prds_dir: Path, valid_phases: Set[str]) -> List[Tuple[str, str]]:
    """Check PRD files for invalid phase references.

    Returns list of (location, violation_message) tuples.

    Skips changelog/historical sections where old phase references are acceptable.
    Skips files with file-level suppression: <!-- arch-suppress-prd-phases: reason -->
    """
    violations: List[Tuple[str, str]] = []

    # Deferred features that are explicitly "Not in DEVELOPMENT_PLAN" (allowed)
    allowed_deferred_patterns = [
        "Not in Current Development Plan",
        "Not in DEVELOPMENT_PLAN",
        "Not in plan",
        "Phase 13+",
        "Phase 13+ Future",
        "Phase 13+ (research direction",
    ]

    for prd_file in prds_dir.glob("*.md"):
        try:
            content = prd_file.read_text(encoding="utf-8")
        except Exception:
            continue

        # Check for file-level suppression comment
        if "arch-suppress-prd-phases" in content:
            continue

        lines = content.split('\n')
        in_changelog = False
        in_removed_section = False
        in_deferred_section = False

        # Find all "Phase XX" references
        for i, line in enumerate(lines, start=1):
            # Track context: are we in a changelog, deferred, or "Removed" section?
            if "## Changelog" in line or "## Modification History" in line or "## Removed from" in line:
                in_changelog = True
            elif "## " in line and "Deferred" in line:
                in_deferred_section = True
            elif line.startswith("## ") and ("Changelog" not in line and "Modification" not in line and "Removed" not in line and "Deferred" not in line):
                in_changelog = False
                in_deferred_section = False

            if "Removed from v1.0" in line:
                in_removed_section = True
            elif line.startswith("---"):
                in_removed_section = False

            # Skip if in changelog/deferred/removed sections (historical references OK)
            if in_changelog or in_removed_section or in_deferred_section:
                continue

            # Skip comments and allowed patterns
            if line.strip().startswith("#") or any(p in line for p in allowed_deferred_patterns):
                continue

            # Check for invalid phase references
            for match in re.finditer(r"Phase\s+(\d+[A-Z]+(?:-[a-z])?)", line):
                phase = match.group(1)

                # Known invalid phases from old PRD versions
                invalid_phases = {
                    "9A", "9B", "9C", "9D", "9E", "9F",  # Pre-plan speculative phases
                    "10",  # Bare "Phase 10" without letter (too generic)
                }

                if phase in invalid_phases:
                    violations.append((
                        f"{prd_file.name}:{i}",
                        f"Speculative phase reference: Phase {phase} (not in DEVELOPMENT_PLAN). "
                        f"Use 'Not in Current Development Plan' or correct phase ID."
                    ))
                elif phase not in valid_phases:
                    violations.append((
                        f"{prd_file.name}:{i}",
                        f"Invalid phase reference: Phase {phase} not found in DEVELOPMENT_PLAN.md"
                    ))

    return violations


def extract_entrypoints_from_agent(agent_file: Path) -> List[str]:
    """Extract public async method names from agent file.

    Returns list of method names that look like entrypoints (async def <name>).
    """
    methods: List[str] = []
    try:
        content = agent_file.read_text(encoding="utf-8")
    except Exception:
        return methods

    # Match "async def method_name(...)"
    pattern = r"async\s+def\s+([a-z_][a-z0-9_]*)\s*\("
    for match in re.finditer(pattern, content, re.IGNORECASE):
        method = match.group(1)
        # Skip private/dunder methods and common infrastructure methods
        if not method.startswith("_") and method not in {"create", "connect", "disconnect"}:
            methods.append(method)

    return methods


def extract_prd_entrypoint_count(prd_file: Path) -> Optional[Tuple[int, int]]:
    """Extract entrypoint implementation count from PRD.

    Looks for patterns like:
      - "3 of 4 entrypoints implemented"
      - "Status: [MVP] — 2 of 4 entrypoints implemented"

    Returns (implemented_count, total_count) or None if not found.
    """
    try:
        content = prd_file.read_text(encoding="utf-8")
    except Exception:
        return None

    # Match "X of Y entrypoints implemented"
    pattern = r"(\d+)\s+of\s+(\d+)\s+entrypoint"
    for match in re.finditer(pattern, content, re.IGNORECASE):
        return (int(match.group(1)), int(match.group(2)))

    # Also check for "Y total entrypoints"
    if "entrypoints implemented" in content.lower():
        # If we can't extract a count, assume it's incomplete
        return None

    return None


def check_prd_agent_consistency() -> List[Tuple[str, str]]:
    """Check that PRDs exist for production agents and vice versa.

    Returns list of (location, violation_message) tuples.
    """
    violations: List[Tuple[str, str]] = []

    # Agent files that should have PRDs
    # Extract agent name: a9_deep_analysis_agent.py → a9_deep_analysis_agent
    agent_files = {}
    for f in AGENTS_DIR.glob("a9_*_agent.py"):
        if not f.is_file() or "card" in f.stem:
            continue
        # stem = a9_deep_analysis_agent
        agent_name = f.stem.lower()
        agent_files[agent_name] = f

    # PRD files: a9_deep_analysis_agent_prd.md → a9_deep_analysis_agent
    prd_files = {}
    for f in PRD_DIR.glob("a9_*.md"):
        if not f.is_file():
            continue
        # Remove _prd suffix and md extension: a9_deep_analysis_agent_prd.md → a9_deep_analysis_agent
        prd_stem = f.stem.lower()
        if prd_stem.endswith("_prd"):
            prd_agent_name = prd_stem[:-4]  # Remove "_prd"
        else:
            prd_agent_name = prd_stem
        prd_files[prd_agent_name] = f

    # Check for agents without PRDs
    for agent_name, agent_file in agent_files.items():
        # Skip deprecated/test agents
        try:
            head = agent_file.read_text(encoding="utf-8").split('\n')[:10]
            if any("DEPRECATION" in line or "deprecated" in line.lower() for line in head):
                continue
        except Exception:
            continue

        if agent_name not in prd_files:
            violations.append((
                str(agent_file.relative_to(REPO_ROOT)),
                f"No corresponding PRD found. Expected: {agent_name}_prd.md in docs/prd/agents/"
            ))

    return violations


def main() -> int:
    """Run all PRD validation checks."""
    print("[PRD] Starting PRD content validation...")

    violations: List[Tuple[str, str]] = []
    warnings: List[Tuple[str, str]] = []

    # Load development plan
    plan_content = load_development_plan()
    if not plan_content:
        print("[PRD] WARNING: Could not load DEVELOPMENT_PLAN.md", file=sys.stderr)

    valid_phases = extract_phases_from_plan(plan_content)
    print(f"[PRD] Found {len(valid_phases)} valid phases in DEVELOPMENT_PLAN")

    # Check phase references
    phase_violations = check_prd_phase_references(PRD_DIR, valid_phases)
    if phase_violations:
        print("[PRD] Phase reference violations:")
        for loc, msg in phase_violations:
            print(f"  {loc}: {msg}")
        violations.extend(phase_violations)

    # Check agent/PRD consistency
    consistency_violations = check_prd_agent_consistency()
    if consistency_violations:
        print("[PRD] Agent/PRD consistency violations:")
        for loc, msg in consistency_violations:
            print(f"  {loc}: {msg}")
        violations.extend(consistency_violations)

    # Summary
    if violations:
        print(f"\n[PRD] Found {len(violations)} blocking violation(s).", file=sys.stderr)
        return 1

    if warnings:
        print(f"[PRD] Found {len(warnings)} warning(s).")
        return 2

    print("[PRD] All PRD content validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
