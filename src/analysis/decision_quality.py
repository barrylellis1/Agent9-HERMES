"""
Deterministic Decision Quality (DQ) scoring for Solution Finder runs.

WHY THIS EXISTS
---------------
Every instrument in this package so far measures a PROXY — divergence, lever
stability, citation hygiene — each chosen because it was measurable, none of them
the objective. `persona_council_experiments.md` §5 states the problem outright:

    "Optimising a proxy is not optimising the objective... Until 'better' has a
     referent, every additional arm refines a number nobody should act on."

This module supplies the referent. The standard is **Decision Quality** (Stanford
SDG — Spetzler, Matheson & Howard): six requirements evaluated as a chain, where
overall quality is the WEAKEST LINK, not the average. Design rationale, the
frameworks considered and rejected, and the corpus limits are in
`docs/architecture/decision_quality_rubric.md`.

GRANULARITY: THE RUN IS THE DECISION
------------------------------------
Four of the six links are properties of the run (frame, alternatives, tradeoffs,
commitment); only two are per-option (information, reasoning). So the chain is
scored at RUN level and option-level checks are aggregated into it.

This is also the DQ-correct reading. A "decision" is *what do we do about this
margin problem* — one run, producing several candidate alternatives and one
recommendation. The options are alternatives WITHIN a decision, not competing
decisions. Scoring each option as its own decision would make link 2 (creative
alternatives) unaskable, since a single option trivially has no alternatives.

WEAKEST LINK IS REPORTED, NEVER COLLAPSED
-----------------------------------------
`chain_verdict` applies the strict DQ rule (one failed link caps the decision).
But all six links are always reported alongside it. If link 1 fails on every run
ever measured, a bare capped score says the same thing forever and teaches
nothing; the per-link detail is where the actionable content lives.

NOT-CHECKED IS NOT PASS
-----------------------
Same discipline as `groundedness`: True / False / None, where None means the
input needed was not supplied. None is excluded from both numerator and
denominator.

SCREENS ARE NOT VERDICTS
------------------------
Links 1 and 4 are semantic. `persona_council_experiments.md` §5 measured a **71%
false-positive rate** on a term screen for a semantic property. So both links are
marked `advisory=True` and carry their matched terms in `evidence`, for
adjudication recorded as data beside the screen — never folded into a cleverer
regex.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# Frame-widening vocabulary: a response that does something OTHER than recover
# the breached KPI within its existing structure. Derived from the DQ "frame"
# link, not from the corpus — deliberately, because the finding under test is
# that the corpus contains none of it (0 of 27 options across the whole
# investigation). A taxonomy derived from data that lacks the category cannot
# detect the category.
FRAME_WIDENING_PATTERNS: List[str] = [
    r"\bexit\b", r"\bdivest", r"discontinu", r"wind[-\s]down", r"\bsunset\b",
    r"walk[-\s]away", r"stop serving", r"deprioriti[sz]", r"delist",
    r"portfolio (?:reshap|rationali[sz]|exit|reset)", r"rationali[sz]e the portfolio",
    r"reallocat(?:e|ing) capital", r"harvest", r"\bwithdraw\b",
]

# NO LEVER FAMILY IS TREATED AS AN AUTOMATIC FRAME-WIDENING SIGNAL.
#
# The first cut of this module counted `volume_for_margin` as structural, on the
# reasoning that "walk-away" and "full-potential" denote a portfolio response.
# It produced a false positive on the first arm scored: "Full Potential Margin
# Recovery: Accelerated Renewal, Cost Reserve & Base Oil Sourcing Diversification"
# matched `full[-\s]potential` while being, on reading, an ordinary KPI-recovery
# plan wearing Bain vocabulary. The lever taxonomy classifies MECHANISM; it was
# never built to classify FRAME, and borrowing it for that purpose imported a
# rhetoric match as a structural verdict.
#
# Frame is screened on the term list alone, and the screen is advisory.
STRUCTURAL_FAMILIES: Set[str] = set()

# `mechanism.classify_lever` returns this when no pattern matches the title or
# the description. It is a MEASUREMENT GAP, not a lever family, and must never be
# counted as a distinct alternative — see `score_run` link 2.
UNCLASSIFIED = "unclassified"

# The agent's config defaults (`A9_Solution_Finder_Agent_Config.weight_*`). When
# `request.evaluation_criteria` is not supplied, these are what the tradeoff
# matrix reports — so a matrix carrying exactly this vector states a SYSTEM
# CONSTANT, not the decision maker's values. DQ link 4 asks for the latter.
DEFAULT_CRITERIA_WEIGHTS: Tuple[Tuple[str, float], ...] = (
    ("impact", 0.5), ("cost", 0.25), ("risk", 0.25),
)

# The cost-allocation artefact question — does anyone challenge HOW the number
# was constructed before diagnosing a commercial cause? Term list carried over
# from `tools/ab_harness/b3_artefact_score.py`, where it screened 14 candidates
# of which 4 survived adjudication. Kept identical so the two are comparable.
ARTEFACT_PATTERNS: List[str] = [
    r"absorpt", r"allocat", r"costing method", r"cost method", r"standard cost",
    r"overhead", r"ledger", r"accounting (?:artefact|artifact|treatment|change)",
    r"how (?:the )?cost", r"granularity",
]


@dataclass
class LinkResult:
    """One DQ link. `advisory` marks a semantic screen rather than a verdict."""
    name: str
    passed: Optional[bool] = None
    advisory: bool = False
    detail: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class DecisionQualityScore:
    run_id: str
    l1_frame: LinkResult = field(default_factory=lambda: LinkResult("frame", advisory=True))
    l2_alternatives: LinkResult = field(default_factory=lambda: LinkResult("alternatives"))
    l3_information: LinkResult = field(default_factory=lambda: LinkResult("information"))
    l4_tradeoffs: LinkResult = field(default_factory=lambda: LinkResult("tradeoffs", advisory=True))
    l5_reasoning: LinkResult = field(default_factory=lambda: LinkResult("reasoning"))
    l6_commitment: LinkResult = field(default_factory=lambda: LinkResult("commitment"))
    # Diagnostics that are facts rather than verdicts.
    distinct_lever_families: int = 0
    lever_families: Tuple[str, ...] = ()
    unclassified_options: int = 0
    n_options: int = 0
    criteria_defaulted: Optional[bool] = None

    def links(self) -> List[LinkResult]:
        return [self.l1_frame, self.l2_alternatives, self.l3_information,
                self.l4_tradeoffs, self.l5_reasoning, self.l6_commitment]

    @property
    def checked(self) -> int:
        return sum(1 for l in self.links() if l.passed is not None)

    @property
    def passed(self) -> int:
        return sum(1 for l in self.links() if l.passed is True)

    @property
    def score(self) -> Optional[float]:
        return (self.passed / self.checked) if self.checked else None

    @property
    def weakest_links(self) -> List[str]:
        return [l.name for l in self.links() if l.passed is False]

    @property
    def chain_verdict(self) -> Optional[bool]:
        """Strict DQ: the chain holds only if no checked link failed.

        Returns None when nothing could be checked at all — an unscored decision
        is not a passing one.
        """
        if self.checked == 0:
            return None
        return not self.weakest_links


def _norm(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _option_blob(option: Dict[str, Any]) -> str:
    parts = [str(option.get(k) or "") for k in ("title", "description", "rationale")]
    parts += [str(p) for p in (option.get("prerequisites") or [])]
    for persp in option.get("perspectives") or []:
        if isinstance(persp, dict):
            parts += [str(a) for a in (persp.get("arguments_for") or [])]
            parts += [str(a) for a in (persp.get("arguments_against") or [])]
    return _norm(" ".join(parts))


def _hits(patterns: List[str], text: str) -> List[str]:
    return sorted({m.group(0) for p in patterns for m in [re.search(p, text)] if m})


def score_run(
    solutions: Dict[str, Any],
    *,
    da_result: Optional[Dict[str, Any]] = None,
    run_id: str = "?",
) -> DecisionQualityScore:
    """Score one SF run against the six DQ links.

    `solutions` is the SF result payload. `da_result` supplies the observed
    magnitudes link 5 needs; omitting it degrades link 5 to not-checked rather
    than scoring against an absent baseline.
    """
    from src.analysis.groundedness import DAFacts, extract_da_facts, score_option
    from src.analysis.mechanism import classify_lever

    s = DecisionQualityScore(run_id=run_id)
    options = solutions.get("options_ranked") or []
    s.n_options = len(options)

    audit = solutions.get("audit_log") or []
    audit_events = {e.get("event"): e for e in audit if isinstance(e, dict)}
    is_stub_run = "heuristic_stub_fallback" in audit_events

    blobs = {str(o.get("id") or i): _option_blob(o) for i, o in enumerate(options)}
    all_text = " ".join(blobs.values())

    # ---- L2: creative alternatives -----------------------------------------
    # Counted by DISTINCT LEVER FAMILY, not by option count. Three options that
    # are all `indexation` are one alternative presented three times, which is
    # exactly the failure DQ's second link exists to name.
    families = []
    for o in options:
        primary, _ = classify_lever(o.get("title"), o.get("description"))
        families.append(primary)
    classified = sorted({f for f in families if f != UNCLASSIFIED})
    n_unclassified = sum(1 for f in families if f == UNCLASSIFIED)
    s.lever_families = tuple(families)
    s.distinct_lever_families = len(classified)
    s.unclassified_options = n_unclassified
    if options:
        # >=2 is a FLOOR, not a quality bar: one distinct family means literally
        # no alternative was offered. No threshold above that is asserted, per
        # the same reasoning `mechanism.modal_share` gives for refusing one.
        #
        # UNCLASSIFIED OPTIONS ARE NOT COUNTED AS ALTERNATIVES. The taxonomy in
        # `mechanism` was derived from 13 payloads in Aug 2026 and does not cover
        # every lever these arms produced (mix-shift and hedging both fall
        # through). Two unclassified options may be one lever or two — unknown.
        # So when they could flip the verdict, the link degrades to not-checked
        # rather than guessing in either direction.
        if len(classified) >= 2:
            s.l2_alternatives.passed = True
        elif len(classified) + n_unclassified >= 2:
            s.l2_alternatives.passed = None  # undetermined; taxonomy gap decides it
        else:
            s.l2_alternatives.passed = False
        s.l2_alternatives.detail = (
            f"{len(options)} options; {len(classified)} classified lever "
            f"famil{'y' if len(classified) == 1 else 'ies'}"
            f"{' (' + ', '.join(classified) + ')' if classified else ''}"
            + (f"; {n_unclassified} UNCLASSIFIED — taxonomy gap, verdict undetermined"
               if n_unclassified and s.l2_alternatives.passed is None else
               f"; {n_unclassified} unclassified" if n_unclassified else "")
        )
        s.l2_alternatives.evidence = classified

    # ---- L1: appropriate frame (ADVISORY) ----------------------------------
    # Does the decision ever consider a response other than recovering this KPI
    # within its existing structure?
    if options:
        structural = [f for f in families if f in STRUCTURAL_FAMILIES]
        widening = _hits(FRAME_WIDENING_PATTERNS, all_text)
        s.l1_frame.passed = bool(structural or widening)
        s.l1_frame.evidence = sorted(set(structural)) + widening
        s.l1_frame.detail = (
            f"frame-widening signals: {', '.join(s.l1_frame.evidence)}"
            if s.l1_frame.evidence else
            "every option recovers the breached KPI within its existing structure"
        )

    # ---- L3: reliable information ------------------------------------------
    sub3: List[Optional[bool]] = []
    notes3: List[str] = []

    sub3.append(not is_stub_run)
    if is_stub_run:
        notes3.append("run fell back to the heuristic stub")

    # Constraint exposure: an option generated without seeing an active
    # constraint was not working from complete information — deterministic, and
    # a stronger signal than groundedness G5's text screen because it reads what
    # the persona was actually shown.
    ce = solutions.get("constraint_exposure") or {}
    by_option = ce.get("by_option") or {}
    if by_option:
        unseen = {oid: v.get("constraints_unseen") or []
                  for oid, v in by_option.items() if v.get("constraints_unseen")}
        sub3.append(not unseen)
        if unseen:
            notes3.append(f"{len(unseen)} option(s) never saw an active constraint")
        else:
            notes3.append(f"all options saw all {ce.get('union_size', 0)} active constraints")

    # The artefact question, as a screen. Includes critic findings — the critic
    # pass is a legitimate place for it to be raised.
    critic_text = _norm(str(audit_events.get("critic_pass_findings") or ""))
    artefact = _hits(ARTEFACT_PATTERNS, all_text + " " + critic_text)
    if artefact:
        notes3.append(f"artefact-question terms present (SCREEN, needs adjudication): {', '.join(artefact)}")
    else:
        notes3.append("no cost-construction challenge anywhere in options or critic findings")

    checked3 = [c for c in sub3 if c is not None]
    if checked3:
        s.l3_information.passed = all(checked3)
    s.l3_information.detail = "; ".join(notes3)
    s.l3_information.evidence = artefact

    # ---- L4: clear values and tradeoffs (ADVISORY) -------------------------
    # Presence of a weighted criteria set is checkable. Whether the weights
    # reflect THIS principal's values is not, from one payload — so the check is
    # presence, and `evidence` carries the weight vector so invariance across
    # runs can be read at the batch level, where it IS visible.
    tm = solutions.get("tradeoff_matrix") or {}
    criteria = tm.get("criteria") or []
    named = [c for c in criteria if isinstance(c, dict) and c.get("name")]
    weighted = [c for c in named if isinstance(c.get("weight"), (int, float))]
    if tm:
        vector = tuple((str(c["name"]), c.get("weight")) for c in named)
        s.criteria_defaulted = vector == DEFAULT_CRITERIA_WEIGHTS
        present = bool(named) and len(weighted) == len(named)
        # PRESENCE IS NOT SUFFICIENT. `request.evaluation_criteria or [defaults]`
        # in the agent means an unsupplied criteria set silently becomes the
        # config constant — which renders as a fully-populated weighted matrix
        # and passes any presence check. DQ link 4 asks whether THIS decision
        # maker's values were made explicit, so a matrix that is exactly the
        # system default is evidence they were not.
        s.l4_tradeoffs.passed = present and not s.criteria_defaulted
        s.l4_tradeoffs.detail = (
            f"{len(named)} criteria, {len(weighted)} weighted — "
            + ("VECTOR IS THE AGENT CONFIG DEFAULT: no principal-specific "
               "values were supplied for this decision"
               if s.criteria_defaulted else "criteria supplied for this decision")
            if named else "tradeoff matrix present but names no criteria"
        )
        s.l4_tradeoffs.evidence = [f"{c['name']}={c.get('weight')}" for c in named]

    # ---- L5: sound reasoning ------------------------------------------------
    if da_result is not None and options:
        facts = extract_da_facts(da_result)
        grades = solutions.get("moderator_grades") or {}
        bad: List[str] = []
        checked_any = False
        for o in options:
            oid = str(o.get("id") or "?")
            g = score_option(
                o, facts,
                moderator_grade=grades.get(oid),
                is_stub_run=is_stub_run,
            )
            if g.g3_arithmetic_plausible is not None:
                checked_any = True
                if not g.g3_arithmetic_plausible:
                    bad.append(f"{oid} claims {g.impact_ratio}x observed move")
            if g.cross_segment_summation:
                bad.append(f"{oid} cross-segment summation")
        if checked_any:
            s.l5_reasoning.passed = not bad
            s.l5_reasoning.detail = "; ".join(bad) if bad else "impact claims within observed magnitudes"
            s.l5_reasoning.evidence = bad
        else:
            s.l5_reasoning.detail = "no option stated a scope+range that could be checked against DA facts"

    # ---- L6: commitment to action ------------------------------------------
    ask = solutions.get("decision_ask") or {}
    imm = solutions.get("immediate_actions") or []
    nxt = solutions.get("next_steps") or []
    has_owner = bool(isinstance(ask, dict) and ask.get("decision_owner"))
    has_text = bool(isinstance(ask, dict) and ask.get("decision_text"))
    s.l6_commitment.passed = bool(has_text and has_owner and imm)
    s.l6_commitment.detail = (
        f"decision_ask={'yes' if has_text else 'no'}, owner="
        f"{ask.get('decision_owner') if has_owner else 'none'}, "
        f"{len(imm)} immediate actions, {len(nxt)} next steps"
    )

    return s
