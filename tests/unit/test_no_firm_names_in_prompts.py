"""Phase 18 — real consultancies' names must not reach prompts or the screen.

Two distinct exposures, both closed here:

  STYLE_GUIDANCE  is INJECTED INTO PROMPT TEXT ("INTERVIEW STYLE: ...").
  PARTNER_RULES[*][*]["name"] is USER-FACING — DeepFocusView renders it as
                  "AI Recommends — <name> · <name>".

This is a regression guard, not a correctness proof. It pins that the strings
stay clean; whether the de-branded prompt produces equally good analysis is a
behavioural question a unit test cannot answer (see the card).

Containment-by-guardrail is specifically what this replaces: the backlog
records `"Bain" leaked` to a rendered briefing after firm names were verified
absent, and src/analysis/option_id_leak.py exists because `opt_1` reached
executive prose. A name that is never in the string cannot leak.
"""
import re

import pytest

from src.agents.new.a9_deep_analysis_agent import STYLE_GUIDANCE

# Legal names and the short forms that appear in practice. `Bain`, `EY` and
# `PwC` are word-bounded to avoid matching inside ordinary words.
FIRM_PATTERNS = [
    r"McKinsey", r"Boston Consulting", r"\bBCG\b", r"\bBain\b",
    r"Deloitte", r"Accenture", r"\bKPMG\b", r"\bPwC\b",
    r"Strategy&", r"EY-?Parthenon", r"\bEY\b",
]
_FIRM_RE = re.compile("|".join(FIRM_PATTERNS), re.IGNORECASE)


def _firms_in(text: str):
    return sorted({m.group(0) for m in _FIRM_RE.finditer(text or "")})


class TestStyleGuidance:
    """Goes into live prompt text — the words the model actually receives."""

    @pytest.mark.parametrize("style", sorted(STYLE_GUIDANCE))
    def test_no_firm_name_in_prompt_text(self, style):
        found = _firms_in(STYLE_GUIDANCE[style])
        assert not found, f"STYLE_GUIDANCE[{style!r}] still names {found}"

    @pytest.mark.parametrize("style", sorted(STYLE_GUIDANCE))
    def test_analytical_instruction_survived_the_rename(self, style):
        """De-branding must not have hollowed the guidance out. Every entry
        carried its content after the colon; that content has to still be
        there, or the prompt lost substance along with the brand."""
        text = STYLE_GUIDANCE[style]
        assert len(text.split()) >= 10, f"{style!r} looks gutted, not de-branded: {text!r}"
        assert "language" in text.lower(), f"{style!r} lost its language instruction"
        assert "focus on" in text.lower(), f"{style!r} lost its focus instruction"

    def test_the_three_styles_are_still_distinct(self):
        """Removing the brand must not collapse them into the same guidance."""
        vals = [STYLE_GUIDANCE[k] for k in sorted(STYLE_GUIDANCE)]
        assert len(set(vals)) == len(vals), "styles collapsed to identical text"


class TestPartnerRulesAreUserFacing:
    """`name` renders in DeepFocusView as "AI Recommends — <name>"."""

    def _partner_rules(self):
        """Read the literal out of the method's source. It is a local inside
        _recommend_diverse_council, so there is nothing to import — and
        asserting on the source is the point: this guards the string, not a
        runtime value some other path could substitute."""
        import inspect
        from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
        src = inspect.getsource(A9_Deep_Analysis_Agent._recommend_diverse_council)
        start = src.index("PARTNER_RULES = {")
        end = src.index("role = principal_ctx.get", start)
        return src[start:end]

    def test_no_firm_name_in_displayed_roster(self):
        """Checks the DISPLAYED field only.

        Scope, deliberately: the dict KEYS ("mckinsey", "bcg", ...) are still
        firm-derived and are NOT covered here. They are registry lookup
        identifiers — `persona_id` flows into `selectedPersonas` and keys into
        `consulting_personas_registry.yaml` — so renaming them is a data
        migration touching the registry, FIRM_COLORS and COUNCIL_PRESET_PERSONAS,
        which is Phase 18 step 4 and not this change.

        They are not displayed, but they DO travel in the API payload, so this
        is a reduction in exposure rather than its elimination. Stated plainly
        here so a green suite is not mistaken for a finished job.
        """
        block = self._partner_rules()
        names = re.findall(r'"name":\s*"([^"]*)"', block)
        assert names, "no display names found — did the literal move?"
        found = sorted({f for n in names for f in _firms_in(n)})
        assert not found, f"PARTNER_RULES still DISPLAYS firm names: {found}"

    def test_every_slot_still_has_a_label(self):
        """A blank or missing name would render as 'AI Recommends — ·'."""
        block = self._partner_rules()
        names = re.findall(r'"name":\s*"([^"]*)"', block)
        assert len(names) >= 8, f"expected the full roster, found {len(names)}"
        assert all(n.strip() for n in names), "a roster slot has an empty display name"

    def test_selection_keys_are_unchanged(self):
        """Keys drive keyword/role selection. Renaming them would change which
        slot gets picked — the display label was the only thing meant to move."""
        block = self._partner_rules()
        for key in ("mckinsey", "bcg", "bain", "deloitte", "ey_parthenon",
                    "kpmg", "pwc_strategy", "accenture"):
            assert f'"{key}"' in block, f"selection key {key!r} disappeared"
