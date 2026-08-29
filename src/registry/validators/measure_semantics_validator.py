"""
Negation validator -- DEVELOPMENT_PLAN.md Phase 16, step 2.

Checks a KPI's `sql_query` against its data product's declared
`measure_semantics.stored_sign` and flags any place the SQL re-negates a
measure the contract already states is stored negative.

This is exactly the bug class that produced Hess's gross_margin_pct=165.57%
(true value 34.43%): `HessStarSchemaView` stores COGS/SGA/Other as negative
amounts (same convention as the BigQuery and Snowflake views), and three
seeded KPIs negate them again --
    SUM(CASE WHEN account_type='Revenue' THEN amount
             WHEN account_type='COGS'    THEN -amount ELSE 0 END)
-- which ADDS cost to revenue instead of subtracting it. The direction error
is the dangerous part: reported margin rose while true margin fell.

Scope, deliberately narrow (static SQL-text analysis, not a SQL parser):
- Only inspects CASE ... END expressions that combine two or more DISTINCT
  account types in one SUM -- that is the shape where a double negative can
  fight against an unnegated sibling branch (Revenue) and silently invert an
  aggregate. A standalone `SELECT SUM(-amount) WHERE account_type = 'COGS'`
  is NOT flagged: negating an already-negative measure that is the ONLY
  thing being summed is a legitimate "show this cost as a positive number"
  KPI (e.g. apex_lubricants' `cogs`/`sga_expenses` KPIs), not a sign bug --
  there is no sibling branch for it to fight.
- A WHEN branch keyed on a column other than `type_column` (e.g.
  `account_category = 'D&A'`) is not attributable to any declared account
  type and is silently skipped, not flagged -- the validator has no sign
  fact to check it against.
- This is regex-based text matching over known SQL shapes actually seeded in
  this codebase (bare identifiers, `[bracket]`-quoted SQL Server
  identifiers, single-equality and IN-list WHEN branches). It is not a SQL
  parser and will not understand nested CASE, subqueries, or unconventional
  formatting -- false negatives are possible on SQL shaped differently from
  what exists today. It does not currently produce false positives against
  any KPI in scripts/clients/*.py (validated against all four seeded
  clients as part of building this).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _norm_ident(text: str) -> str:
    """Strip optional [] / `` / "" quoting and surrounding whitespace from an identifier."""
    return text.strip().strip("[]`\"").strip()


def _is_negated_amount(expr: str, amount_column: str) -> bool:
    r"""True when `expr` is exactly a unary-minus negation of the amount column.

    Matches `-amount`, `- amount`, `-[amount]`, `-"amount"`, `` -`amount` `` --
    the only shapes this codebase's seeded KPI SQL actually uses. Does not
    attempt to evaluate arbitrary arithmetic expressions.
    """
    expr = expr.strip()
    pattern = re.compile(
        r"^-\s*[\[\"`]?" + re.escape(amount_column) + r"[\]\"`]?$",
        re.IGNORECASE,
    )
    return bool(pattern.match(expr))


def _find_case_blocks(sql: str) -> List[str]:
    """Return the inner text of every non-nested CASE ... END block in `sql`."""
    return re.findall(r"\bCASE\b(.*?)\bEND\b", sql, flags=re.IGNORECASE)


def _account_type_universe(sql: str, type_column: str) -> List[str]:
    """Every account-type literal named anywhere in the query (WHERE + CASE branches).

    Used only to infer which account types an ELSE branch falls through to.
    Overreaches slightly if a WHEN references a type absent from the WHERE
    clause's own restriction -- acceptable for this heuristic's purpose,
    documented in the module docstring.
    """
    col = re.escape(type_column)
    found: List[str] = []
    for m in re.finditer(
        r"[\[\"`]?" + col + r"[\]\"`]?\s*=\s*'([^']+)'", sql, flags=re.IGNORECASE
    ):
        found.append(m.group(1))
    for m in re.finditer(
        r"[\[\"`]?" + col + r"[\]\"`]?\s*IN\s*\(([^)]+)\)", sql, flags=re.IGNORECASE
    ):
        for lit in re.findall(r"'([^']+)'", m.group(1)):
            found.append(lit)
    # de-dupe, preserve first-seen order
    seen = set()
    ordered = []
    for v in found:
        if v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered


def _extract_when_branches(case_body: str, type_column: str) -> Dict[str, str]:
    """Map account_type literal -> its THEN expression, for WHEN branches keyed on type_column.

    Handles both `WHEN type_column = 'X' THEN <expr>` and
    `WHEN type_column IN ('X','Y') THEN <expr>` (the expr is attributed to
    every literal in the IN-list). A branch keyed on a different column is
    not represented in the returned map.
    """
    col = re.escape(type_column)
    # Non-greedy THEN-expression, terminated by the next WHEN/ELSE/END boundary.
    stop = r"(?=\s+WHEN\b|\s+ELSE\b|$)"

    branches: Dict[str, str] = {}

    for m in re.finditer(
        r"WHEN\s*[\[\"`]?" + col + r"[\]\"`]?\s*=\s*'([^']+)'\s*THEN\s*(.+?)" + stop,
        case_body,
        flags=re.IGNORECASE,
    ):
        branches[m.group(1)] = m.group(2)

    for m in re.finditer(
        r"WHEN\s*[\[\"`]?"
        + col
        + r"[\]\"`]?\s*IN\s*\(([^)]+)\)\s*THEN\s*(.+?)"
        + stop,
        case_body,
        flags=re.IGNORECASE,
    ):
        literals = re.findall(r"'([^']+)'", m.group(1))
        for lit in literals:
            branches[lit] = m.group(2)

    return branches


def _extract_else(case_body: str) -> Optional[str]:
    m = re.search(r"ELSE\s*(.+?)\s*$", case_body, flags=re.IGNORECASE)
    return m.group(1) if m else None


def check_sql_sign_convention(
    sql_query: str,
    measure_semantics: Optional[Dict[str, Any]],
) -> List[str]:
    """Return human-readable violation strings; empty list means clean (or nothing to check).

    `measure_semantics` is `DataProduct.measure_semantics` -- None (not yet
    declared for this data product) is a documented no-op, not a failure.
    Never raises: malformed input yields an empty (or best-effort) result,
    consistent with every other non-fatal validator in this codebase.
    """
    if not sql_query or not isinstance(measure_semantics, dict):
        return []

    type_column = measure_semantics.get("type_column")
    amount_column = measure_semantics.get("amount_column")
    stored_sign = measure_semantics.get("stored_sign")
    if not type_column or not amount_column or not isinstance(stored_sign, dict):
        return []

    violations: List[str] = []
    universe = _account_type_universe(sql_query, type_column)

    for case_body in _find_case_blocks(sql_query):
        branches = _extract_when_branches(case_body, type_column)
        if not branches:
            # No branch keyed on the declared type_column in this CASE --
            # nothing here to check against a sign fact we have.
            continue

        for account_type, then_expr in branches.items():
            sign = stored_sign.get(account_type)
            if sign is None:
                continue
            negated = _is_negated_amount(then_expr, amount_column)
            if sign == "negative" and negated:
                violations.append(
                    f"WHEN {type_column}='{account_type}' THEN -{amount_column}: "
                    f"'{account_type}' is already declared negative in "
                    f"measure_semantics -- this branch negates it again, which ADDS "
                    f"it instead of subtracting it when combined with an unnegated "
                    f"sibling branch."
                )
            elif sign == "positive" and negated:
                violations.append(
                    f"WHEN {type_column}='{account_type}' THEN -{amount_column}: "
                    f"'{account_type}' is declared positive in measure_semantics -- "
                    f"this branch negates it unexpectedly."
                )

        else_expr = _extract_else(case_body)
        if else_expr is not None and _is_negated_amount(else_expr, amount_column):
            # Account types that fall through to ELSE: everything in the
            # query's universe not explicitly branched in THIS case block.
            fallthrough = [t for t in universe if t not in branches]
            for account_type in fallthrough:
                sign = stored_sign.get(account_type)
                if sign == "negative":
                    violations.append(
                        f"ELSE -{amount_column}: '{account_type}' falls through to "
                        f"ELSE without an explicit WHEN branch, and is already "
                        f"declared negative in measure_semantics -- the ELSE "
                        f"negation re-negates it, which ADDS it instead of "
                        f"subtracting it when combined with an unnegated sibling "
                        f"branch (e.g. Revenue)."
                    )

    return violations
