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


MEANINGS = ["critical", "warning", "opportunity", "healthy", "info"]

# A severity token is ONE fixed shade — that has two structural consequences a
# raw-color linter can't catch, and both shipped as real bugs the same day
# this lint was written (see ui_refinement_plan.md "Severity token sweep"):
#
# 1. `bg-severity-X` + `text-severity-X`, both solid (no alpha), on one
#    element: background and text render as the IDENTICAL color — invisible
#    text. Shipped on Portfolio.tsx's verdict pills (blank pills where
#    "Validated"/"Failed" should read).
# 2. `{prefix}-severity-X` + `hover:{prefix}-severity-X` with the same alpha
#    (most commonly no alpha at all): the hover state is pixel-identical to
#    the base state — no hover feedback. Shipped on the Executive Briefing's
#    own Approve button among 13 others, all from buttons that used two
#    ADJACENT Tailwind shades before the sweep (e.g. emerald-700/emerald-600)
#    and collapsed to the token's single value.
#
# Neither is a hardcoded-color problem — both sides are already correctly
# tokenized — so PATTERN/lint() above can't see them. Checked separately here.
BG_SOLID = {m: re.compile(rf"(?<!hover:)bg-severity-{m}(?!/)\b") for m in MEANINGS}
TEXT_SOLID = {m: re.compile(rf"(?<!hover:)text-severity-{m}(?!/)\b") for m in MEANINGS}
HOVER_MATCH = {
    prefix: {m: re.compile(rf"\bhover:{prefix}-severity-{m}(/\d+)?\b") for m in MEANINGS}
    for prefix in ("bg", "text", "border")
}
BASE_MATCH = {
    prefix: {m: re.compile(rf"(?<!hover:){prefix}-severity-{m}(/\d+)?\b") for m in MEANINGS}
    for prefix in ("bg", "text", "border")
}


def _same_shade_collisions(line: str) -> list[str]:
    if SUPPRESS.search(line):
        return []
    out = []
    for m in MEANINGS:
        if BG_SOLID[m].search(line) and TEXT_SOLID[m].search(line):
            out.append(
                f"`bg-severity-{m}` + `text-severity-{m}`, both solid — text is "
                f"invisible. Tint the background instead: `bg-severity-{m}/20`."
            )
    for prefix in ("bg", "text", "border"):
        for m in MEANINGS:
            base_hit = BASE_MATCH[prefix][m].search(line)
            hov_hit = HOVER_MATCH[prefix][m].search(line)
            if base_hit and hov_hit and base_hit.group(1) == hov_hit.group(1):
                out.append(
                    f"`{prefix}-severity-{m}` + identical `hover:` variant — no "
                    f"hover feedback. Use `hover:brightness-110` (backgrounds) or "
                    f"`hover:brightness-125` (text/borders) instead of repeating "
                    f"the token."
                )
    return out


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
            rel = path.relative_to(REPO_ROOT)
            for msg in _same_shade_collisions(line):
                violations.append(f"{rel}:{i}: {msg}")
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
