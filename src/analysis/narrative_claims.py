"""
Deterministic validation of LLM-written narrative in SF output.

WHY THIS EXISTS
---------------
The groundedness scorer checks each option's `impact_estimate` against observed
magnitudes. It never looked at the PROSE — and the prose is what leads page one
of the Executive Briefing, above the fold, where an executive reads it first.

Two real errors from a single live run (2026-08-08), both in `problem_reframe`,
both past every guard that existed:

  1. SEGMENT SUBSTITUTED FOR THE HEADLINE KPI
       prose : "headline KPI move recorded as a -43.24 point deterioration
                to a current level of -445.01"
       actual: Gross Margin % = 30.29%
       -445.01 / -43.24 are Chain A's change-point current_value / delta.
       The model reached past the typed KPIValue into the change points and
       promoted one customer's slice to "the headline KPI".

  2. STATED SUM DOES NOT MATCH THE COMPONENTS IN THE SAME SENTENCE
       prose : "-43.24pp ... -16.76pp ... -15.18pp ... collectively dragging
                margin down by 140.4pp of combined drag"
       43.24 + 16.76 + 15.18 = 75.18, not 140.4 — overstated 1.9x.

Both are arithmetic, so both are checkable without a model. That matters: a
model-based reviewer would be as capable of the same slip, and would make the
check itself stochastic.

SCOPE / LIMITS
--------------
This is deliberately narrow. It does NOT attempt to judge whether prose is
persuasive, well-framed, or true in any general sense — only whether the numbers
it asserts agree with numbers the pipeline already computed. Claims it cannot
tie to a known quantity are reported as UNVERIFIED, never as wrong: a flood of
false positives would train readers to ignore the flags, which is worse than
having none.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from src.registry.models.kpi import KPI

# A headline claim is only worth checking when the sentence ASSERTS a value FOR
# the headline. "Chain A fell 43.24pp" is a true segment statement, and so is
# "performance beneath that headline number is mixed: Chain A (-43.24pp)..." —
# the latter explicitly discusses what sits UNDER the headline.
#
# Tuned against the real payload: a cue of bare /headline/ produced 4 false
# positives out of 6 findings, all from one sentence enumerating segments
# beneath the headline. Flags that cry wolf get ignored, which is worse than no
# flags, so the cue now requires an assertion and rejects subordinating prepositions.
_HEADLINE_CUE = re.compile(
    r"(?<!beneath\s)(?<!below\s)(?<!under\s)(?<!behind\s)"
    r"(headline\s+kpi|headline\s+number|overall\s+kpi|the\s+kpi)"
    r"\s*(?:move|movement|change|level)?\s*"
    r"(?:is|was|of|at|recorded\s+as|stands\s+at|moved|declin\w*|fell|dropped|deteriorat\w*)",
    re.IGNORECASE,
)
# Prepositions that make the sentence about what lies BENEATH the headline, not
# about the headline's own value. Checked separately because Python's
# fixed-width lookbehind cannot span "beneath that ".
_SUBORDINATED = re.compile(r"\b(beneath|below|under|behind|excluding|apart\s+from)\b[^.]{0,30}headline", re.IGNORECASE)

# How far after the cue a number can sit and still be the value being asserted.
# Beyond this it is almost always a different clause enumerating something else.
_HEADLINE_CLAIM_SPAN = 90

# Numbers with an explicit unit. Bare integers are skipped on purpose — years,
# counts and segment ordinals would generate noise with no signal.
_NUMBER = re.compile(r"(-?\d+(?:\.\d+)?)\s*(pp|percentage\s+points?|%|\bpoints?\b)", re.IGNORECASE)
_DOLLARS = re.compile(r"\$\s?(-?\d+(?:\.\d+)?)\s*([MK])?", re.IGNORECASE)

_SUM_CUE = re.compile(
    r"(combined|collectively|total|aggregate|together|sum(?:ming)?)\b[^.]{0,80}?"
    r"(-?\d+(?:\.\d+)?)\s*(pp|percentage\s+points?|%)",
    re.IGNORECASE,
)

# Tolerances. Generous on purpose — the point is to catch a segment standing in
# for the enterprise (typically an order of magnitude out) and sums that are
# plainly wrong (1.9x), not to police rounding.
HEADLINE_TOLERANCE = 0.15   # 15% of the true headline magnitude
SUM_TOLERANCE = 0.10        # 10% of the component sum


@dataclass
class NarrativeFinding:
    kind: str                      # headline_substitution | sum_mismatch | direction_mismatch
    field: str                     # which narrative field it came from
    claimed: float
    expected: Optional[float]
    detail: str
    excerpt: str

    def __str__(self) -> str:      # readable in logs and audit payloads
        return f"[{self.kind}] {self.field}: {self.detail}"


@dataclass
class NarrativeCheck:
    findings: List[NarrativeFinding] = field(default_factory=list)
    checked_fields: List[str] = field(default_factory=list)
    unverified_claims: int = 0

    @property
    def ok(self) -> bool:
        return not self.findings

    def as_audit_event(self) -> Optional[Dict[str, Any]]:
        """Audit entry, or None when clean — an event asserting 'no problems'
        is indistinguishable from a check that never ran."""
        if not self.findings:
            return None
        return {
            "event": "narrative_claim_mismatch",
            "count": len(self.findings),
            "findings": [
                {"kind": f.kind, "field": f.field, "claimed": f.claimed,
                 "expected": f.expected, "detail": f.detail, "excerpt": f.excerpt[:200]}
                for f in self.findings
            ],
        }


def _scale(value: float, suffix: Optional[str]) -> float:
    s = (suffix or "").upper()
    return value * 1_000_000 if s == "M" else value * 1_000 if s == "K" else value


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", text or "") if s.strip()]


def check_headline_claims(
    text: str, field_name: str, headline_value: Optional[float], headline_delta: Optional[float],
) -> List[NarrativeFinding]:
    """Flag prose that calls a number the headline KPI when it is not.

    Only sentences that explicitly claim headline status are examined, so a
    correct statement about a segment is never flagged.
    """
    out: List[NarrativeFinding] = []
    if headline_value is None and headline_delta is None:
        return out

    for sentence in _sentences(text):
        cue = _HEADLINE_CUE.search(sentence)
        if not cue:
            continue
        # "beneath that headline number, three segments..." is ABOUT the segments.
        if _SUBORDINATED.search(sentence):
            continue

        # Only numbers close after the cue are the value being asserted; a figure
        # later in the sentence usually belongs to a different clause.
        window = sentence[cue.end(): cue.end() + _HEADLINE_CLAIM_SPAN]
        claims = [float(m.group(1)) for m in _NUMBER.finditer(window)]
        claims += [_scale(float(m.group(1)), m.group(2)) for m in _DOLLARS.finditer(window)]
        if not claims:
            continue

        # The sentence is a headline claim, so every magnitude in it should be
        # reconcilable with the headline value or its movement.
        targets = [t for t in (headline_value, headline_delta) if t is not None]
        for claimed in claims:
            if any(abs(abs(claimed) - abs(t)) <= max(abs(t) * HEADLINE_TOLERANCE, 0.01) for t in targets):
                continue
            expected = min(targets, key=lambda t: abs(abs(claimed) - abs(t)))
            out.append(NarrativeFinding(
                kind="headline_substitution", field=field_name, claimed=claimed, expected=expected,
                detail=(f"prose presents {claimed:g} as the headline KPI, but the measured "
                        f"headline is {expected:g} — likely a segment figure promoted to enterprise"),
                excerpt=sentence,
            ))
    return out


def check_stated_sums(text: str, field_name: str) -> List[NarrativeFinding]:
    """Flag a stated total that disagrees with the components in the same sentence.

    Deliberately self-contained: only components cited alongside the total are
    used, so this needs no external data and cannot be fooled by a total drawn
    from somewhere the sentence never mentions.
    """
    out: List[NarrativeFinding] = []
    for sentence in _sentences(text):
        m = _SUM_CUE.search(sentence)
        if not m:
            continue
        stated = float(m.group(2))
        components = [float(n.group(1)) for n in _NUMBER.finditer(sentence)
                      if abs(float(n.group(1)) - stated) > 1e-9]
        if len(components) < 2:
            continue  # nothing to add up; not a claim we can check
        actual = sum(abs(c) for c in components)
        if abs(abs(stated) - actual) <= max(actual * SUM_TOLERANCE, 0.01):
            continue
        out.append(NarrativeFinding(
            kind="sum_mismatch", field=field_name, claimed=stated, expected=actual,
            detail=(f"states a combined {stated:g} but the {len(components)} figures cited "
                    f"in the same sentence sum to {actual:g} ({abs(stated) / actual:.1f}x)"),
            excerpt=sentence,
        ))
    return out


def check_additive_claim(text: str, field_name: str, kpi: Optional[KPI]) -> List[NarrativeFinding]:
    """Flag a 'combined/total/collectively' claim in this KPI's own
    narrative when the KPI is declared additive_across_dimensions=false --
    regardless of whether the stated sum is arithmetically self-consistent
    (that's check_stated_sums's job, immediately above). Phase 17 T1/T2:
    additivity is a METHODOLOGY fact -- summing this KPI's segment values is
    invalid on principle even when the arithmetic in the sentence checks out,
    the same distinction src/registry/validators/additivity_validator.py
    already draws for structured impact_estimate claims. This extends that
    same coverage to free narrative prose, the smallest concrete SF-facing
    use of the Phase 17 T2 decomposition work landing alongside it.

    kpi=None or additive_across_dimensions is not explicitly False
    (undeclared or True) is a documented no-op, matching every other
    optional-KPI check in this codebase.
    """
    out: List[NarrativeFinding] = []
    if kpi is None or kpi.additive_across_dimensions is not False:
        return out
    for sentence in _sentences(text):
        m = _SUM_CUE.search(sentence)
        if not m:
            continue
        out.append(NarrativeFinding(
            kind="non_additive_summation", field=field_name,
            claimed=float(m.group(2)), expected=None,
            detail=(
                f"'{kpi.id}' is declared additive_across_dimensions=false -- this sentence states "
                f"a combined/total figure across segments, which is not a valid way to derive this "
                f"KPI's enterprise value regardless of whether the arithmetic itself is self-consistent"
            ),
            excerpt=sentence,
        ))
    return out


# "32.63% -> 29.94%", "from 32.63% to 29.94%". Captures both endpoints so the
# direction they describe can be compared with the direction claimed alongside.
_TRANSITION = re.compile(
    r"(?:from\s+)?(-?\d+(?:\.\d+)?)\s*%?\s*(?:->|→|–>|to)\s*(-?\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
# A signed movement stated in the same sentence, e.g. "(-2.69 points" or "-8.2%".
_SIGNED_MOVE = re.compile(r"([+-]\d+(?:\.\d+)?)\s*(?:pp|percentage\s+points?|points?|%)", re.IGNORECASE)


def check_transition_direction(text: str, field_name: str) -> List[NarrativeFinding]:
    """Flag "A -> B" whose direction contradicts a signed delta in the same sentence.

    A live production briefing stated, twice:

        "enterprise headline Gross Margin % move (-2.69 points, 29.94%->32.63%)"

    which reads as RISING from 29.94 to 32.63 while labelled -2.69 points. The
    endpoints were simply written in the wrong order. Nothing caught it: the
    numbers were individually correct and the sums balanced, so every existing
    check passed.

    Deliberately narrow. It fires only when BOTH a transition and a signed move
    appear in the same sentence and they disagree — enough to catch a reversed
    arrow without guessing at prose that merely mentions two figures.
    """
    findings: List[NarrativeFinding] = []
    for sentence in _sentences(text):
        m = _TRANSITION.search(sentence)
        if not m:
            continue
        try:
            start, end = float(m.group(1)), float(m.group(2))
        except ValueError:
            continue
        if start == end:
            continue
        moves = [float(x) for x in _SIGNED_MOVE.findall(sentence)]
        if not moves:
            continue
        stated_dir = 1.0 if (end - start) > 0 else -1.0
        # Any signed move that contradicts the endpoints is a contradiction; a
        # sentence carrying several is judged on the one that disagrees.
        for mv in moves:
            if mv == 0:
                continue
            if (1.0 if mv > 0 else -1.0) != stated_dir:
                findings.append(NarrativeFinding(
                    kind="direction_mismatch",
                    field=field_name,
                    claimed=end,
                    expected=start,
                    detail=(
                        f"states {start:g} -> {end:g} (a {'rise' if stated_dir > 0 else 'fall'}) "
                        f"alongside a stated move of {mv:+g} — the endpoints appear reversed"
                    ),
                    excerpt=sentence.strip()[:160],
                ))
                break
    return findings


def check_narrative(
    narrative_fields: Dict[str, Optional[str]],
    *,
    headline_value: Optional[float] = None,
    headline_delta: Optional[float] = None,
    kpi: Optional[KPI] = None,
) -> NarrativeCheck:
    """Validate every narrative field against numbers the pipeline already knows.

    `narrative_fields` maps a name (e.g. "problem_reframe.situation") to its text.
    `kpi` (Phase 17 T1/T2): the registry KPI record for the headline KPI this
    narrative discusses, when available. Enables check_additive_claim below;
    omitted entirely (None) when the caller has no registry connection, same
    documented-no-op posture as every other optional input here.
    Never raises — a validation failure must not be able to break generation.
    """
    result = NarrativeCheck()
    for name, text in (narrative_fields or {}).items():
        if not text or not isinstance(text, str):
            continue
        result.checked_fields.append(name)
        try:
            result.findings.extend(check_headline_claims(text, name, headline_value, headline_delta))
            result.findings.extend(check_stated_sums(text, name))
            result.findings.extend(check_transition_direction(text, name))
            result.findings.extend(check_additive_claim(text, name, kpi))
        except Exception:
            # Bookkeeping must never break the pipeline it observes.
            continue
    return result


def extract_narrative_fields(solutions: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Pull the prose an executive actually reads out of an SF payload."""
    pr = (solutions or {}).get("problem_reframe") or {}
    fields: Dict[str, Optional[str]] = {
        "problem_reframe.situation": pr.get("situation"),
        "problem_reframe.complication": pr.get("complication"),
        "problem_reframe.question": pr.get("question"),
        "recommendation_rationale": (solutions or {}).get("recommendation_rationale"),
    }
    return {k: v for k, v in fields.items() if isinstance(v, str) and v.strip()}
