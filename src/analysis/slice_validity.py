"""Slice-validity profiling — deterministic, pure, backend-aware.

TWO INDEPENDENT CHECKS, NOT ONE
--------------------------------
`profile()` answers one question: "if a ratio KPI is sliced by this
dimension, does every component measure reach it at the same grain?" A
ratio KPI (gross margin %, cost-to-serve, yield) is built from two or more
component measures; if those components are recorded at DIFFERENT
dimensional grain, slicing the ratio by a dimension only one component
reaches produces a confident, plausible, completely wrong number. This
check only applies where there are 2+ components to compare — it says
nothing about a single-component KPI (`net_revenue`, a plain `SUM(amount)`),
because there is nothing on the other side of the comparison.

`check_completeness()` (added 2026-08-16, after shipping `profile()` without
it was called out as a real gap — see git history) answers a DIFFERENT
question that applies to EVERY KPI, one component or many: "of the rows
this KPI actually sums, what fraction have a non-NULL value for this
dimension at all?" A single-component KPI can be wrong when sliced even
though the enterprise total is right — some revenue rows might have no
`customer_name`, so `SUM(net_revenue) GROUP BY customer_name` silently
drops that revenue rather than misattributing it, and the per-customer
numbers no longer reconstruct the total. `profile()` cannot see this
failure at all, because it never looks at a KPI with only one component.

Both checks share `assess()`/`DimensionVerdict`/`_quote_view()` — they
differ only in what `counts` means (component name -> distinct dimension
values reached, vs `total_rows`/`complete_rows`), and a caller (currently
A9_Data_Governance_Agent.check_slice_validity()) is expected to run BOTH
per dimension and treat a dimension as unsafe to slice by if EITHER fails.

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
import re
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


def _filter_pattern(column: str) -> re.Pattern:
    """`<column> = 'X'` or `<column> IN ('X', 'Y', ...)`, bracket-quoting
    (`[column]`) optional so it matches every backend's convention this
    codebase actually writes — SQL Server bracket-quotes, everything else
    doesn't."""
    return re.compile(rf"\[?{column}\]?\s*(?:=\s*'([^']+)'|IN\s*\(([^)]+)\))", re.IGNORECASE)


# Tried in order. account_type is the discriminator for every ratio/composite
# KPI in this codebase (Revenue vs COGS vs SGA); account_category is a SECOND,
# finer-grained discriminator a real subset of single-component KPIs filter
# on instead — found live 2026-08-15 running this against every KPI, not
# assumed: product_sales_revenue ("account_category = 'Product Sales'"),
# service_revenue, base_oil_cost, distribution_cost all have NO account_type
# filter anywhere in their sql_query, only account_category. Confirmed on
# both BigQuery and Snowflake twins of these four.
_COMPONENT_COLUMN_PATTERNS = [
    ("account_type", _filter_pattern("account_type")),
    ("account_category", _filter_pattern("account_category")),
]


def extract_components(sql_query: Optional[str]) -> tuple[str, List[str]]:
    """Pull the column and distinct values a KPI's own sql_query filters its
    components on. Returns (measure_column, components).

    Both check_completeness() and profile() need to know which components a
    KPI is actually built from, and requiring a caller to specify that by
    hand doesn't scale to "every KPI" (42 across the three seeded clients,
    26 of them single-component). The KPI's sql_query already encodes the
    answer correctly by construction — extract it rather than ask twice.

    Matches every shape this codebase's KPI definitions actually use,
    confirmed by reading real examples, not assumed: a bare `= 'Revenue'`
    filter, an `IN (...)` list, multiple separate matches inside a
    `CASE WHEN account_type = 'Revenue' THEN ... WHEN account_type = 'COGS'
    THEN ...` expression (each WHEN is its own match), and the
    account_category fallback above.

    Returns `("account_type", [])` when NEITHER column matches anything —
    the caller decides what "no components found" means for that KPI, but
    account_type stays the reported column since it's the more common case,
    not a real signal either way when nothing matched at all.
    """
    for column, pattern in _COMPONENT_COLUMN_PATTERNS:
        values: set = set()
        for m in pattern.finditer(sql_query or ""):
            if m.group(1):
                values.add(m.group(1))
            elif m.group(2):
                values.update(re.findall(r"'([^']+)'", m.group(2)))
        if values:
            # Revenue first when present — it's the reference component in
            # every example this codebase has (the "richest" reach every cost
            # component is compared against); alphabetical after that.
            return column, sorted(values, key=lambda v: (v != "Revenue", v))
    return "account_type", []


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
            # Snowflake returns unquoted identifiers UPPERCASE by default
            # ("COMPONENT"/"N", not "component"/"n") — found live 2026-08-15
            # against apex_lubricants: r["component"] raised KeyError,
            # OUTSIDE this try/except in the original code, so it killed the
            # entire check (every dimension, not just one) rather than being
            # skipped the way a genuinely absent dimension is below. Moved
            # inside the try/except and made case-insensitive so it degrades
            # the same way a missing column does, and works regardless of
            # which backend's casing convention produced the row.
            counts = {}
            for r in rows:
                row = {str(k).lower(): v for k, v in r.items()}
                counts[row["component"]] = int(row["n"])
        except Exception as exc:  # dimension absent from this view, or a row-shape surprise
            print(f"  {dim:24s} skipped — {str(exc).splitlines()[0][:70]}", file=sys.stderr)
            continue
        for c in components:            # a component with zero rows still counts
            counts.setdefault(c, 0)
        richest = max(counts.values()) if counts else 0
        coverage = (min(counts.values()) / richest) if richest else 0.0
        out.append(DimensionVerdict(dim, counts, coverage, assess(counts)))
    return out


async def check_completeness(
    run_query: Callable[[str], Any],
    view: str,
    measure_column: str,
    components: Sequence[str],
    dimensions: Sequence[str],
    value_column: str = "amount",
    version_filter: Optional[str] = "Actual",
    source_system: str = "bigquery",
) -> List[DimensionVerdict]:
    """For each dimension, what fraction of this KPI's own rows have a
    non-NULL value for that dimension?

    Applies to EVERY KPI — `components` may be a single value (a plain sum
    like `net_revenue` filtered to `account_type = 'Revenue'`) or several (a
    composite like `gross_margin_pct`). Unlike `profile()`, this never has
    "nothing to compare" — a lone component still has rows, and those rows
    either carry the dimension or don't.

    `counts` here means `{"total_rows": N, "complete_rows": M}` (M <= N
    always), NOT component-name -> value-count like `profile()`'s
    `DimensionVerdict.counts` — same dataclass, different meaning by
    construction, documented here so a caller doesn't conflate the two.

    `COUNT(dim)` in SQL already excludes NULLs by definition, so
    `complete_rows` is exactly "rows where this dimension is populated" —
    no CASE WHEN needed. `value_column` is accepted but not summed by this
    check (row-count is the coverage unit, matching profile()'s own
    DISTINCT-count philosophy rather than mixing in a dollar-weighted
    measure with its own sign/magnitude questions); kept as a parameter so a
    future caller can request a value-weighted variant without a signature
    change if row-count coverage ever proves too coarse.
    """
    where = f"{measure_column} IN ({', '.join(repr(c) for c in components)})"
    if version_filter:
        where += f" AND version = {version_filter!r}"

    quoted_view = _quote_view(view, source_system)

    out: List[DimensionVerdict] = []
    for dim in dimensions:
        sql = (
            f"SELECT COUNT(*) AS total_rows, COUNT({dim}) AS complete_rows "
            f"FROM {quoted_view} WHERE {where}"
        )
        try:
            result = run_query(sql)
            rows = await result if inspect.isawaitable(result) else result
            row = {str(k).lower(): v for k, v in rows[0].items()}
            counts = {"total_rows": int(row["total_rows"]), "complete_rows": int(row["complete_rows"])}
        except Exception as exc:  # dimension absent from this view, or a row-shape surprise
            print(f"  {dim:24s} skipped (completeness) — {str(exc).splitlines()[0][:70]}", file=sys.stderr)
            continue
        coverage = (counts["complete_rows"] / counts["total_rows"]) if counts["total_rows"] else 0.0
        out.append(DimensionVerdict(dim, counts, coverage, assess(counts)))
    return out
