"""Slice-validity profiling — deterministic, pure, backend-aware.

WHAT THIS ANSWERS
------------------
"If a ratio KPI is sliced by this dimension, does every component measure
reach that dimension at the same grain?" A ratio KPI (gross margin %,
cost-to-serve, yield) is built from two or more component measures. If those
components are recorded at DIFFERENT dimensional grain, slicing the ratio by
a dimension only one component reaches produces a confident, plausible,
completely wrong number.

WHY THIS EXISTS
----------------
Found 2026-08-09 in the Lubricants demo dataset. All COGS was attributed to a
single customer while revenue spanned twenty, so that one account showed
-457% gross margin and the other nineteen showed exactly 100.00%. Every layer
behaved correctly on top of it. Full incident record and the deliberate
decision NOT to auto-gate on this: docs/architecture/kpi_semantic_contract.md
§4, DEVELOPMENT_PLAN.md -> Phase 15 -> Stage I.

Originally `scripts/check_slice_validity.py`, a hand-run CLI tool, BigQuery
only. `profile()`/`assess()` were always pure (no I/O beyond an injected
`run_query` callable) — moved here, alongside the other pure analysis
modules (mechanism.py, groundedness.py, problem_profile.py), so
A9_Data_Governance_Agent.check_slice_validity() can call the same logic the
CLI does, with no duplication. The CLI re-exports these names and keeps
working unchanged.

BACKEND-AWARE QUERY BUILDING
------------------------------
The original query template hardcoded BigQuery's backtick-quoting directly
into the SQL text (backtick-wrapped `{view}` in the FROM clause) — a query built that way is a syntax
error on SQL Server or Snowflake, REGARDLESS of which database connection
routes it there. Connection routing and query dialect are two separate
problems; fixing only the connection (routing through
A9_Data_Product_Agent.execute_sql() instead of a BigQuery-only client) is
necessary but not sufficient, and was the gap in the first draft of this
design.

`_quote_view()` below picks the identifier-quoting convention per backend,
using the SAME conventions already live elsewhere in this codebase — not
invented here:
  - BigQuery:   backtick-wrap the whole fully-qualified `project.dataset.view`
                string (a9_data_product_agent.py's own BQ-reference regex:
                `` `[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_.-]+` ``)
  - SQL Server: bracket EACH dot-separated segment individually, e.g.
                `[dbo].[HessStarSchemaView]` (scripts/clients/hess.py's
                `_SS_PREFIX` literal — bracketing the whole string as one
                token, as BigQuery's backtick convention does, is wrong here)
  - Snowflake:  bare, unquoted (scripts/clients/apex_lubricants.py's `_VIEW`
                usage — Snowflake identifiers are case-insensitive unless
                quoted, and none of this codebase's Snowflake SQL quotes them)
  - DuckDB:     bare, unquoted, matching every DuckDB seed's `FROM {_VIEW}`
                usage; only column names containing spaces get double-quoted
                in this codebase's convention, and dimension/measure column
                names here are snake_case, so no column-quoting is needed.

Column identifiers (`measure_column`, each `dim`) are left unquoted across
all four backends — every dimension name this check has ever been run
against is snake_case with no spaces, matching the DuckDB double-quoting
precedent's own stated exception.
"""
from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

# Coverage below this fraction of the richest component = the dimension cannot
# carry the ratio at all. INVALID_BELOW is judgement, not science — set from two
# datasets, revisit as more are profiled.
INVALID_BELOW = 0.25

# "ok" requires FULL coverage, deliberately. If a component misses even one value
# of the dimension, that value's ratio is fabricated — 19 of 20 customers covered
# means one customer shows a confident wrong number. Partial coverage is the case
# most likely to be believed, so it never reads clean.
DEGRADED_BELOW = 1.0

# Recognised source_system values, matching the same normalisation
# generate_sql_for_kpi() already applies (a9_data_product_agent.py) — several
# spellings map to one backend so a caller doesn't need to know which alias
# the registry happens to use.
_SQLSERVER_ALIASES = {"sqlserver", "sql_server", "mssql"}


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


def _quote_view(view: str, source_system: str) -> str:
    """Return the FROM-clause reference for `view`, quoted per backend.

    See the module docstring's BACKEND-AWARE QUERY BUILDING section for the
    precedent each branch matches. Unrecognised source_system values fall
    through to the BigQuery convention (the original, longest-standing
    behaviour of this check) rather than raising — a check that refuses to
    run on an unfamiliar source_system is less useful than one that runs
    with the most common convention and lets a syntax error surface loudly
    if it's wrong, which is still louder than never running at all.
    """
    system = (source_system or "bigquery").strip().lower()
    if system in _SQLSERVER_ALIASES:
        return ".".join(f"[{segment}]" for segment in view.split("."))
    if system in ("snowflake", "duckdb", "databricks"):
        return view
    return f"`{view}`"


async def profile(
    run_query: Callable[[str], Any],
    view: str,
    measure_column: str,
    components: Sequence[str],
    dimensions: Sequence[str],
    version_filter: Optional[str] = "Actual",
    source_system: str = "bigquery",
) -> List[DimensionVerdict]:
    """Count distinct values of each dimension, per component measure.

    `run_query` is awaited, so it may be sync or async — `inspect.isawaitable`
    on the call result decides, rather than requiring every caller to wrap a
    sync executor. Made async (2026-08-15) so A9_Data_Governance_Agent can
    await A9_Data_Product_Agent.execute_sql() per dimension without a second,
    duplicate implementation of this loop; the CLI's own BigQuery executor is
    sync internally and is called through the same await-if-awaitable path.
    """
    where = f"{measure_column} IN ({', '.join(repr(c) for c in components)})"
    if version_filter:
        where += f" AND version = {version_filter!r}"

    quoted_view = _quote_view(view, source_system)

    out: List[DimensionVerdict] = []
    for dim in dimensions:
        # GROUP BY the underlying expression, not the `component` alias.
        # BigQuery/Snowflake/DuckDB/Postgres all accept grouping by a
        # SELECT-list alias; T-SQL (SQL Server) does not and fails with
        # "Invalid column name 'component'" — found live 2026-08-15 against
        # Hess. Grouping by the real expression is valid on every backend,
        # so this isn't a per-dialect branch, just a more portable query.
        sql = (
            f"SELECT {measure_column} AS component, COUNT(DISTINCT {dim}) AS n "
            f"FROM {quoted_view} WHERE {where} GROUP BY {measure_column}"
        )
        try:
            result = run_query(sql)
            rows = await result if inspect.isawaitable(result) else result
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
