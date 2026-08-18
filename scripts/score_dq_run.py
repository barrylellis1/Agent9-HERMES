"""Score captured Solution Finder runs against the six Decision Quality links.

Wraps `src.analysis.decision_quality.score_run` for payloads captured off the
wire by the live Playwright specs, so an e2e run can be graded without re-running
the pipeline.

WHY THIS IS A SCRIPT AND NOT A TEST
-----------------------------------
Two of the six links (frame, tradeoffs) are semantic screens carrying a measured
71% false-positive rate, and `decision_quality` marks them advisory for that
reason. Asserting on them in a test would convert an advisory signal into a gate,
which is exactly what the rubric says not to do. This prints them for a human to
adjudicate instead.

Usage:
    py scripts/score_dq_run.py <run-dir-or-payload.json> [more...]

A run directory is expected to hold `sf-synthesis-payload.json` and optionally
`da-payload.json`. Without the DA payload link 5 degrades to NOT-CHECKED rather
than being scored against an absent baseline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.decision_quality import score_run  # noqa: E402

_MARK = {True: "PASS", False: "FAIL", None: "not-checked"}


def _load(path: Path) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], str]:
    """Return (solutions, da_result, label) for a run dir or a payload file."""
    if path.is_dir():
        sf_path = path / "sf-synthesis-payload.json"
        da_path = path / "da-payload.json"
        label = path.name
    else:
        sf_path = path
        da_path = path.parent / "da-payload.json"
        label = path.parent.name

    if not sf_path.exists():
        raise FileNotFoundError(f"no sf-synthesis-payload.json at {sf_path}")

    raw = json.loads(sf_path.read_text(encoding="utf-8"))
    # The status endpoint wraps the SF body as {"solutions": {...}}. Unwrap it —
    # scoring the wrapper finds no options and reports a uniformly empty chain,
    # which looks like a catastrophic run rather than a read at the wrong level.
    solutions = raw.get("solutions", raw) if isinstance(raw, dict) else raw

    da = None
    if da_path.exists():
        da_raw = json.loads(da_path.read_text(encoding="utf-8"))
        if isinstance(da_raw, dict):
            da = da_raw.get("deep_analysis", da_raw)
    return solutions, da, label


def _report(path: Path) -> None:
    solutions, da, label = _load(path)
    s = score_run(solutions, da_result=da, run_id=label)

    print("=" * 78)
    print(f"RUN: {label}")
    print(f"  options: {s.n_options}   distinct lever families: {s.distinct_lever_families}"
          f"   unclassified: {s.unclassified_options}")
    if da is None:
        print("  NOTE: no da-payload.json — link 5 cannot be scored for this run.")
    print("-" * 78)

    for i, link in enumerate(s.links(), start=1):
        flag = " (advisory screen, not a verdict)" if link.advisory else ""
        print(f"  L{i} {link.name:<14} {_MARK[link.passed]:<12}{flag}")
        if link.detail:
            print(f"       {link.detail}")
        if link.evidence:
            shown = ", ".join(str(e) for e in link.evidence[:6])
            print(f"       evidence: {shown}")

    print("-" * 78)
    score = s.score
    print(f"  links passed : {s.passed}/{s.checked}"
          f"{f'  ({score:.0%})' if score is not None else ''}")
    # Weakest-link is the DQ rule: one failed link caps the decision. Printed
    # alongside the per-link detail, never instead of it — a bare capped verdict
    # says the same thing forever and teaches nothing.
    print(f"  chain verdict: {_MARK[s.chain_verdict]}"
          + (f"  — capped by: {', '.join(s.weakest_links)}" if s.weakest_links else ""))
    print()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    for arg in argv[1:]:
        try:
            _report(Path(arg))
        except Exception as exc:  # noqa: BLE001 — a bad path should not kill the batch
            print(f"!! {arg}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
