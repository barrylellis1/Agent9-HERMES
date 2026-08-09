"""Slice-validity probe — INTERNAL PRE-SALES CHECK, not a product feature.

WHAT IT ANSWERS
---------------
"If I point Agent9 at this client's data, which dimensions can their ratio KPIs
actually be sliced by?"

A ratio KPI (gross margin %, cost-to-serve, yield) is built from two or more
component measures. If those components are recorded at DIFFERENT dimensional
grain, slicing the ratio by a dimension only one component reaches produces a
confident, plausible-looking, completely wrong number.

WHY THIS EXISTS
---------------
Found 2026-08-09 in the Lubricants demo dataset. All COGS was attributed to a
single customer while revenue spanned twenty, so that one account showed -457%
gross margin and the other nineteen showed exactly 100.00%. Every layer behaved
correctly on top of it: Situation Awareness raised a breach, Deep Analysis found
the "concentration", three consulting personas diagnosed a base-oil pass-through,
and the briefing recommended renegotiating a contract to fix an ETL defect.
The enterprise number was correct throughout (33.25%), which is why nothing
caught it — the error only appears when you slice.

Real warehouses have this constantly: COGS booked at plant level, revenue at
customer level, SG&A at cost-centre level. In a mature SAP CO-PA / Margin
Analysis landscape standard COGS does carry customer and product, so this often
will NOT fire — but allocated cost, mid-market stacks, and warehouse layers that
dropped characteristics on the way in all reproduce it.

SCOPE — deliberately narrow
---------------------------
Run this by hand before building a demo on a new dataset. Output goes to whoever
runs it. It is NOT wired into any agent, does NOT gate any workflow, and has no
UI. Enforcement was considered and explicitly rejected as scope creep for the
current stage; see DEVELOPMENT_PLAN.md -> Phase 15 -> Stage I.

It measures PRESENCE, not provenance. It cannot tell an observed cost from an
allocated one — a fully-allocated COGS column looks perfect here. Detecting an
allocation-driver change as a false root cause is a pilot-phase capability that
needs a real CO-PA/PaPM feed; noted in the plan, not built.

USAGE
-----
    python scripts/check_slice_validity.py --view agent9-465818.LubricantsBusiness.LubricantsStarSchemaView
    python scripts/check_slice_validity.py --view <fq_view> --measure-column account_type \
        --components Revenue COGS --dimensions customer_name product_name channel_name

Requires GOOGLE_APPLICATION_CREDENTIALS (BigQuery only for now — the analysis is
backend-agnostic but the executor is not; add a branch when a client needs it).
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence

# Coverage below this fraction of the richest component = the dimension cannot
# carry the ratio at all. INVALID_BELOW is judgement, not science — set from two
# datasets, revisit as more are profiled.
INVALID_BELOW = 0.25

# "ok" requires FULL coverage, deliberately. If a component misses even one value
# of the dimension, that value's ratio is fabricated — 19 of 20 customers covered
# means one customer shows a confident wrong number. Partial coverage is the case
# most likely to be believed, so it never reads clean.
DEGRADED_BELOW = 1.0


@dataclass
class DimensionVerdict:
    dimension: str
    counts: Dict[str, int]          # component -> distinct dimension values
    coverage: float                 # weakest component / richest component
    verdict: str                    # "ok" | "degraded" | "INVALID"

    @property
    def weakest(self) -> str:
        return min(self.counts, key=lambda k: self.counts[k])


def assess(counts: Dict[str, int]) -> str:
    """Verdict for one dimension from its per-component distinct-value counts.

    Pure function, no I/O — this is the part worth testing and reusing.
    """
    richest = max(counts.values()) if counts else 0
    if richest == 0:
        return "unknown"
    ratio = min(counts.values()) / richest
    if ratio < INVALID_BELOW:
        return "INVALID"
    if ratio < DEGRADED_BELOW:
        return "degraded"
    return "ok"


def profile(
    run_query: Callable[[str], Sequence[dict]],
    view: str,
    measure_column: str,
    components: Sequence[str],
    dimensions: Sequence[str],
    version_filter: str | None = "Actual",
) -> List[DimensionVerdict]:
    """Count distinct values of each dimension, per component measure."""
    where = f"{measure_column} IN ({', '.join(repr(c) for c in components)})"
    if version_filter:
        where += f" AND version = {version_filter!r}"

    out: List[DimensionVerdict] = []
    for dim in dimensions:
        sql = (
            f"SELECT {measure_column} AS component, COUNT(DISTINCT {dim}) AS n "
            f"FROM `{view}` WHERE {where} GROUP BY component"
        )
        try:
            rows = run_query(sql)
        except Exception as exc:  # dimension absent from this view
            print(f"  {dim:24s} skipped — {str(exc).splitlines()[0][:70]}", file=sys.stderr)
            continue
        counts = {r["component"]: int(r["n"]) for r in rows}
        for c in components:            # a component with zero rows still counts
            counts.setdefault(c, 0)
        richest = max(counts.values()) if counts else 0
        coverage = (min(counts.values()) / richest) if richest else 0.0
        out.append(DimensionVerdict(dim, counts, coverage, assess(counts)))
    return out


def _bigquery_executor(project: str | None):
    from google.cloud import bigquery

    client = bigquery.Client(project=project) if project else bigquery.Client()

    def run(sql: str) -> Sequence[dict]:
        return [dict(r) for r in client.query(sql).result()]

    return run


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--view", required=True, help="Fully-qualified view, e.g. project.dataset.view")
    p.add_argument("--project", default=None, help="GCP project (defaults to the view's prefix)")
    p.add_argument("--measure-column", default="account_type",
                   help="Column separating the ratio's components (default: account_type)")
    p.add_argument("--components", nargs="+", default=["Revenue", "COGS"],
                   help="Component measures of the ratio (default: Revenue COGS)")
    p.add_argument("--dimensions", nargs="+", default=[
        "customer_name", "product_name", "product_line",
        "profit_center_name", "channel_name", "customer_segment",
    ])
    p.add_argument("--version", default="Actual", help="version filter, or '' to disable")
    args = p.parse_args()

    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set", file=sys.stderr)
        return 2

    project = args.project or args.view.split(".")[0]
    verdicts = profile(
        _bigquery_executor(project), args.view, args.measure_column,
        args.components, args.dimensions, args.version or None,
    )

    print(f"\nSlice validity — {args.view}")
    print(f"components: {' / '.join(args.components)}\n")
    width = max((len(v.dimension) for v in verdicts), default=20)
    for v in verdicts:
        counts = "  ".join(f"{c}={v.counts.get(c, 0)}" for c in args.components)
        mark = {"ok": "ok", "degraded": "DEGRADED", "INVALID": "INVALID"}[v.verdict]
        print(f"  {v.dimension:<{width}}  {counts:<28} coverage={v.coverage:5.0%}  {mark}")

    bad = [v for v in verdicts if v.verdict == "INVALID"]
    deg = [v for v in verdicts if v.verdict == "degraded"]
    print()
    if bad:
        print("DO NOT slice this ratio by:", ", ".join(v.dimension for v in bad))
        for v in bad:
            print(f"  - {v.dimension}: '{v.weakest}' reaches only {v.counts[v.weakest]} of "
                  f"{max(v.counts.values())} values. Slices will look confident and be wrong.")
    if deg:
        print("Degraded (usable only with an explicit caveat):",
              ", ".join(v.dimension for v in deg))
    if not bad and not deg:
        print("All checked dimensions carry every component. Ratio is safe to slice by them.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
