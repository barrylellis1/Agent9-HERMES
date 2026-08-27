"""Severity-token lint — prevents the hardcoded-color drift the Aug 2026 UI
audit found and fixed (ui_refinement_plan.md Tier 2; 742 sites swept in one
pass, 2026-08-27).

DESIGN_SYSTEM.md §1 calls this "the single most important design-system
rule": never hardcode red-400/amber-400/emerald-400/green-400 (or any other
shade of those four hues) for semantic meaning on screen — always use the
severity-* token group, so a future palette change is one CSS variable edit
instead of a grep-and-pray across 56 files.

This lint enforces that GOING FORWARD. It does not re-flag the codebase's
existing, deliberately-deferred exceptions (see EXEMPT_FILES and
_is_exempt_line below) — those were evaluated individually during the sweep
and are pre-existing debt, not new drift. Re-flagging all of them here would
make this hook permanently red and train reviewers to ignore it.

Escape hatch for a genuinely new, reviewed exception: append
`// severity-lint-allow: <reason>` to the line.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_SRC = REPO_ROOT / "decision-studio-ui" / "src"

# Persuade-mode marketing/pitch surfaces. ui_brand_guidelines.md §5 requires
# these to SHARE THE STYLE (dark slate, Aperture logo, typography) with the
# app — it does not require them to share the severity CSS variables, which
# exist to govern KPI/situation status in Operate-mode screens. Coupling a
# landing page's accent color to "what counts as a critical KPI" would make
# a future rebrand of either one break the other. Evaluated file-by-file
# during the 2026-08-27 sweep; see ui_refinement_plan.md Tier 2.
EXEMPT_FILES = {
    UI_SRC / "pages" / "LandingPage.tsx",
    UI_SRC / "pages" / "LandingPageAlternate.tsx",
    UI_SRC / "pages" / "HowItWorks.tsx",
    UI_SRC / "pages" / "InsightsBIModernization.tsx",
}

COLOR_MAP = {"red": "critical", "amber": "warning", "emerald": "opportunity", "green": "healthy"}
PREFIXES = ["text", "bg", "border-l", "border-t", "border-r", "border-b", "border",
            "ring", "divide", "from", "via", "to", "fill", "stroke"]
PATTERN = re.compile(
    r"\b(" + "|".join(PREFIXES) + r")-(red|amber|emerald|green)-(\d{2,3})(/\d+)?\b"
)
LIGHT_BG = re.compile(r"bg-(red|amber|emerald|green)-(50|100|200)\b")
DARK_TEXT = re.compile(r"text-(red|amber|emerald|green)-(600|700|800|900)\b")
SUPPRESS = re.compile(r"severity-lint-allow\s*:")


def _is_exempt_line(line: str, match: "re.Match") -> bool:
    # Print media needs different literal shades for contrast on white paper
    # (severity-* tokens are a single fixed value, not print-safe at every
    # background). A screen/print pair on one line gets only the screen half
    # converted; the print half is a deliberate, permanent exception.
    pre = line[max(0, match.start() - 6):match.start()]
    if pre.endswith("print:"):
        return True
    # Light badge idiom (`bg-X-100 text-X-800`) needs two DIFFERENT shades for
    # contrast; severity-* tokens only define one shade per meaning, so a
    # blind swap collapses background and text to the same color. This is
    # tracked as a real, separate defect (a dark-first violation, not just a
    # token-naming one) rather than silently declared compliant — see
    # ui_refinement_plan.md Tier 2 follow-up.
    if LIGHT_BG.search(line) and DARK_TEXT.search(line):
        return True
    if SUPPRESS.search(line):
        return True
    return False


def lint() -> list[str]:
    violations: list[str] = []
    if not UI_SRC.exists():
        return violations
    for path in UI_SRC.rglob("*.tsx"):
        if path in EXEMPT_FILES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            for m in PATTERN.finditer(line):
                if _is_exempt_line(line, m):
                    continue
                prefix, color, shade, alpha = m.groups()
                rel = path.relative_to(REPO_ROOT)
                violations.append(
                    f"{rel}:{i}: hardcoded `{m.group(0)}` — use "
                    f"`{prefix}-severity-{COLOR_MAP[color]}{alpha or ''}` "
                    f"(DESIGN_SYSTEM.md §1). Suppress with "
                    f"`// severity-lint-allow: <reason>` if this is a genuine, "
                    f"reviewed exception (print variant or a light-on-dark badge "
                    f"needing two shades)."
                )
    return violations


def main() -> int:
    violations = lint()
    if violations:
        print(f"severity_token_lint: {len(violations)} new hardcoded severity color(s) found\n")
        for v in violations:
            print(f"  {v}")
        print(
            "\nSee decision-studio-ui/DESIGN_SYSTEM.md §1 and "
            "docs/architecture/ui_refinement_plan.md Tier 2."
        )
        return 1
    print("severity_token_lint: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
