"""
Deterministic mechanism fingerprinting for SF options.

WHY THIS EXISTS
---------------
Comparing recommendations by title is hopeless. These are the SAME mechanism:

    "Base Oil Cost-Indexing Clause via Accelerated Contract Renewal"
    "Structural Contract Reset: Base Oil Indexing Clause + Stable-Segment Replication"
    "Trigger-Based Base Oil Indexation Clause in Chain A Contract Renewal"

...and a naive string comparison calls them three different answers, which is how
you conclude a system is unstable when it may only be verbose.

The fingerprint is deliberately COARSE. It answers "is this the same kind of
intervention?", not "is this the same sentence."

TAXONOMY PROVENANCE
-------------------
The families below are NOT invented a priori. They were derived by reading the
option titles from 13 real SF payloads (5 baseline / 5 moderator / 2 diverse /
1 control, Aug 2026 A-B runs) and clustering what actually recurred. An earlier
guessed taxonomy (pricing / contract_terms / cost_structure / mix / governance /
platform) did not survive contact with the data — real output splits along
different seams, e.g. "indexation" and "pricing corridor" are distinct recurring
mechanisms that a generic "pricing" bucket would have merged.

COMPOUND OPTIONS
----------------
Real options routinely carry two or three levers:

    "Service Centers Cost-to-Serve Audit + Pre-Negotiated Synthetic Blend Pricing Corridor"
    "Volume-for-Margin Portfolio Reset ... with Parallel Benchmark Replication"

So classification returns BOTH a primary family (for fingerprint comparability)
and the full matched set (for diagnostics). Primary is resolved by an explicit
priority order — most distinctive lever wins — because a fingerprint has to be a
single comparable value.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Ordered most-distinctive-first. Order IS the tie-break rule for compound
# options, so it is part of the contract, not a cosmetic detail.
#
# Rationale for the ordering: a lever named by a rare, specific phrase
# ("volume-for-margin", "walk-away") identifies the option's actual thesis. A
# lever named by a common word ("pricing") is frequently incidental — nearly
# every option in this domain touches price somewhere. Specific beats generic.
LEVER_PATTERNS: List[Tuple[str, List[str]]] = [
    # A deliberate trade of volume/share for margin — always the option's thesis
    # when present, never a supporting detail.
    ("volume_for_margin", [
        r"volume[-\s]for[-\s]margin",
        r"walk[-\s]away",
        r"account economics reset",
        r"full[-\s]potential",
    ]),
    # Buy the input forward rather than repricing the output. Added 2026-08-15
    # after DQ scoring found `hedging` options falling through to `unclassified`
    # (real: "Base Oil Forward-Buy Hedge Paired with Q3-Aligned Price Reset",
    # which the description fallback had been mislabelling as `governance`).
    # Placed high because these terms are never incidental — an option that says
    # "hedge" is proposing one.
    ("hedging", [
        r"hedg(?:e|ing)",
        r"forward[-\s]buy",
        r"forward contract",
        r"\bfutures\b",
    ]),
    # Change WHAT is sold rather than what it costs or what it is priced at.
    # Added 2026-08-15 with `hedging`: mix-shift was the single most common
    # unclassified lever in the corpus, appearing in 6 of 11 arms across BOTH
    # MBB and lens rosters. Its absence made link 2 (creative alternatives)
    # unreadable wherever it occurred.
    ("mix_shift", [
        r"mix[-\s]shift",
        r"premium[-\s]mix",
        r"mix optimi[sz]",
        r"reallocat\w*[^.]{0,40}mix",
        r"sku rationali[sz]",
        r"rebalanc",
        r"assortment",
    ]),
    # Contractual mechanism that ties price to an input-cost index. Distinct from
    # a plain price increase: the lever is the CLAUSE, not the level.
    ("indexation", [
        r"index(?:ed|ing|ation)?\b",
        r"reindex",
        r"pass[-\s]through",
    ]),
    # Build/deploy a system: data, automation, monitoring infrastructure.
    ("platform", [
        r"\bplatform\b",
        r"intelligence",
        r"automat(?:ed|ion|e)\b",
        r"monitoring",
        r"\berp\b",
        r"margin feed",
        r"visibility",
    ]),
    # Process/organisational control: who decides, on what cadence, under what rules.
    ("governance", [
        r"governance",
        r"\bcontrols?\b",
        r"calendar",
        r"discipline",
        r"systemati[sz]e",
        r"institutionali[sz]e",
        r"\bcouncil\b",
        r"compliance",
    ]),
    # Renegotiate the price level / band itself for a product or account.
    ("pricing_corridor", [
        r"pricing corridor",
        r"price corridor",
        r"repricing",
        r"reprice",
        r"pricing",
    ]),
    # Attack the cost side rather than the price side.
    ("cost_audit", [
        r"cost[-\s]to[-\s]serve",
        r"cost audit",
        r"sourcing",
        r"procurement",
        r"spend controls",
    ]),
    # Transfer a practice that already works elsewhere in the portfolio.
    ("replication", [
        r"replicat(?:e|ion)",
        r"best[-\s]practice",
        r"benchmark",
    ]),
]

# The heuristic fallback SF returns when the LLM produces no usable options. These
# two titles are hardcoded in the agent, so matching them is exact, not fuzzy.
# Detected here as a SAFETY NET only — `heuristic_stub_fallback` in the audit log
# is the authoritative signal (see groundedness.G6). Title matching catches the
# case where a payload is inspected without its audit log attached.
STUB_TITLES = {"tighten spend controls", "optimize pricing"}

UNCLASSIFIED = "unclassified"
STUB = "stub"


@dataclass(frozen=True)
class MechanismFingerprint:
    """A coarse, comparable identity for 'what kind of intervention is this'.

    Equality is by value, so fingerprints can be counted directly to compute a
    modal share. `lever_family` is the discriminating component in practice —
    see the note in `fingerprint()` about the other two.
    """
    lever_family: str
    scope_label: Optional[str]
    causal_edge: Optional[str]
    # Diagnostics — deliberately excluded from equality so a compound option
    # still matches its own family across runs that phrase it differently.
    all_levers: Tuple[str, ...] = field(default=(), compare=False)

    def key(self) -> str:
        return f"{self.lever_family}|{self.scope_label or '-'}|{self.causal_edge or '-'}"


def _norm(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _matches_in(text: str) -> List[Tuple[int, int, str]]:
    """All families matching `text`, as (earliest_position, priority_index, family)."""
    out: List[Tuple[int, int, str]] = []
    for prio, (family, patterns) in enumerate(LEVER_PATTERNS):
        positions = [m.start() for p in patterns for m in [re.search(p, text)] if m]
        if positions:
            out.append((min(positions), prio, family))
    return out


def classify_lever(title: Optional[str], description: Optional[str] = None) -> Tuple[str, List[str]]:
    """Return (primary_family, all_matched_families).

    PRIMARY IS DECIDED BY THE TITLE, AND BY POSITION WITHIN IT.

    This rule was derived empirically in Phase 0, after the obvious approach
    failed. Matching title+description together and resolving by a fixed
    priority order produced three clear misclassifications on real payloads:

        "Enterprise Margin Intelligence Platform with Portfolio-Wide Repricing"
            -> indexation   (should be platform)
        "Systematize Anchor-Account Renewal Governance and Margin Controls"
            -> platform     (should be governance)
        "Renegotiate Synthetic Blend Pricing Corridor Within Current Price-Lock..."
            -> indexation   (the word "index" does not occur in the title at all)

    Cause: descriptions are long and mention nearly every lever in passing, so
    incidental prose outvoted the option's actual thesis.

    A title is a curated thesis statement — the model chose what to lead with,
    and that choice is signal. So: match the TITLE, and among matches take the
    one appearing EARLIEST. This correctly separates the two genuinely different
    compound options below, which any fixed priority order would collapse:

        "Enterprise-Wide Margin Intelligence Platform & Indexed Contracting"
            -> platform    (leads with the platform)
        "Accelerate Chain A Renewal with Indexed Pricing + Automated Margin Feed"
            -> indexation  (leads with the clause; monitoring is the add-on)

    Description is used only as a FALLBACK when the title names no lever at all,
    and otherwise contributes to `all_matched_families` for diagnostics.
    """
    t, d = _norm(title), _norm(description)
    if not t and not d:
        return UNCLASSIFIED, []

    if t in STUB_TITLES:
        return STUB, [STUB]

    title_hits = _matches_in(t)
    desc_hits = _matches_in(d)

    # Union for diagnostics, ordered by taxonomy priority for stable output.
    all_families = sorted(
        {f for _, _, f in title_hits} | {f for _, _, f in desc_hits},
        key=lambda f: next(i for i, (fam, _) in enumerate(LEVER_PATTERNS) if fam == f),
    )

    hits = title_hits or desc_hits
    if not hits:
        return UNCLASSIFIED, []

    # (position, priority) — earliest wins; taxonomy order breaks positional ties.
    hits.sort(key=lambda x: (x[0], x[1]))
    primary = hits[0][2]

    # Put primary first so callers can read all_levers[0] as the thesis and the
    # remainder as supporting levers.
    ordered = [primary] + [f for f in all_families if f != primary]
    return primary, ordered


def normalize_causal_edge(raw: Optional[str]) -> Optional[str]:
    """Reduce a moderator `causal_grounding` string to a comparable `a->b` edge.

    The moderator emits prose around the edge, e.g.
        "gross_margin_pct <-> cogs (confirmed, correlational, ~1 month lag) — primary edge"
        "cogs -> gross_margin_pct (base oil cost pass-through; confirmed)"
    Both denote the same relationship. Endpoints are sorted so direction of
    phrasing does not create spurious fingerprint differences — we are asking
    "which relationship does this option pull", not "which way did the model
    happen to write the arrow".
    """
    if not raw:
        return None
    text = _norm(raw)
    if "ungrounded" in text:
        return "ungrounded"
    if "insufficient_data" in text or "insufficient data" in text:
        return "insufficient_data"

    m = re.search(r"([a-z_][a-z0-9_]{2,})\s*(?:<->|->|<-|→|↔)\s*([a-z_][a-z0-9_]{2,})", text)
    if not m:
        return None
    a, b = sorted([m.group(1), m.group(2)])
    return f"{a}<->{b}"


def fingerprint(
    option: Dict[str, Any],
    moderator_grade: Optional[Dict[str, Any]] = None,
) -> MechanismFingerprint:
    """Build the deterministic fingerprint for one option.

    NOTE ON DISCRIMINATING POWER (measured, Aug 2026): across the 13-payload
    validation set, `scope_label` was "National Auto Parts Chain A" and
    `causal_edge` was cogs<->gross_margin_pct for nearly every option — because
    every run analysed the same situation. So on that data the fingerprint is
    effectively `lever_family` alone, and the taxonomy carries the full weight.
    The other two components earn their place across DIFFERENT situations (where
    scope and edge do vary) and as a guard against a taxonomy collision — but
    do not expect them to separate runs within one situation.
    """
    ie = option.get("impact_estimate") or {}
    primary, all_levers = classify_lever(option.get("title"), option.get("description"))
    edge = normalize_causal_edge((moderator_grade or {}).get("causal_grounding"))
    scope_label = _norm(ie.get("scope_label")) or None

    return MechanismFingerprint(
        lever_family=primary,
        scope_label=scope_label,
        causal_edge=edge,
        all_levers=tuple(all_levers),
    )


def modal_share(fingerprints: List[MechanismFingerprint]) -> Tuple[Optional[str], float]:
    """Return (modal_key, share) — the stability rate for a set of runs.

    Share is the fraction of runs landing on the most common fingerprint. 1.0 is
    perfectly repeatable; 1/N means every run produced something different.
    Deliberately reports a raw rate with NO pass/fail threshold: we have no
    empirical basis yet for what "stable enough" means, and inventing one would
    launder a guess as a standard.
    """
    if not fingerprints:
        return None, 0.0
    counts: Dict[str, int] = {}
    for fp in fingerprints:
        counts[fp.key()] = counts.get(fp.key(), 0) + 1
    best = max(counts, key=counts.get)
    return best, counts[best] / len(fingerprints)


def lever_set(fingerprints: List[MechanismFingerprint]) -> set:
    """The union of primary lever families seen — used for OPTION-SET stability,
    as distinct from selection stability. See the plan: a system that generates a
    stable SET of candidate levers but picks a different winner each time has a
    selection problem, not a generation problem, and the two want different fixes.
    """
    return {fp.lever_family for fp in fingerprints}
