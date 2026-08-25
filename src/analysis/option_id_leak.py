"""Deterministic check: internal option IDs (opt_1/opt_2/opt_3) must never
leak into free text a person reads.

Same discipline as narrative_claims.py in this package: every other guard in
Solution Finder scores the OPTIONS; this checks the PROSE, and it is checked
without an LLM because the leak is a literal string match, not a semantic
judgment — a model reviewer could make the same slip a model author made.

Backstops the "INTERNAL OPTION IDs ARE STRUCTURE, NOT PROSE" prompt rule in
a9_solution_finder_agent.py's synthesis CONSTRAINTS block. Found live
2026-08-24: a real synthesis call rendered decision_ask.decision_text as
"...diagnostic under opt_1." and immediate_actions[*].why_it_matters carried
the same leak twice more. A prompt instruction can fail silently; this
catches it when it does, non-fatally.
"""
import re
from typing import Any, Dict, List, Optional

_OPT_ID_RE = re.compile(r"\bopt_\d+\b")


def find_option_id_leaks(fields: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    """fields: {field_name: text_or_None}.

    Returns one entry per field containing a literal opt_N reference:
    {"field": name, "text": the offending text, "ids_found": [...]}.
    Empty list when clean.
    """
    findings: List[Dict[str, Any]] = []
    for name, text in fields.items():
        if not text or not isinstance(text, str):
            continue
        ids = sorted(set(_OPT_ID_RE.findall(text)))
        if ids:
            findings.append({"field": name, "text": text, "ids_found": ids})
    return findings


def as_audit_event(findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Absent when clean — an event asserting "no leak" is indistinguishable
    from a check that never ran, same convention as narrative_claims.py."""
    if not findings:
        return None
    return {"event": "option_id_leak", "findings": findings}
