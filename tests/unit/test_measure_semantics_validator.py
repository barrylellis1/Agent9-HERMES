"""
DEVELOPMENT_PLAN.md Phase 16, step 2 -- the negation validator.

Pinned against the REAL sql_query strings from scripts/clients/*.py: the
known-broken Hess KPIs (must flag), and the clean lubricants/apex_lubricants
KPIs whose SQL uses the same account-type-CASE shape correctly (must not
false-positive). A validator that only passes on synthetic fixtures proves
nothing about the bug it exists to catch.
"""

from src.registry.validators.measure_semantics_validator import check_sql_sign_convention

LUBRICANTS_MEASURE_SEMANTICS = {
    "type_column": "account_type",
    "amount_column": "amount",
    "stored_sign": {"Revenue": "positive", "COGS": "negative", "SGA": "negative", "Other": "negative"},
}

HESS_MEASURE_SEMANTICS = LUBRICANTS_MEASURE_SEMANTICS  # same convention, per the Phase 16 finding


class TestKnownHessBugsAreFlagged:
    """scripts/clients/hess.py -- the SQL that produced the documented wrong numbers."""

    def test_gross_profit_explicit_when_renegates_cogs(self):
        sql = (
            "SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] "
            "WHEN [account_type] = 'COGS' THEN -[amount] ELSE 0 END) AS value "
            "FROM HessStarSchemaView WHERE [version] = 'Actual'"
        )
        violations = check_sql_sign_convention(sql, HESS_MEASURE_SEMANTICS)
        assert violations, "must flag gross_profit's explicit WHEN COGS THEN -[amount]"
        assert any("COGS" in v for v in violations)

    def test_gross_margin_pct_numerator_renegates_cogs(self):
        sql = (
            "SELECT ROUND(100.0 * SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] "
            "WHEN [account_type] = 'COGS' THEN -[amount] ELSE 0 END) "
            "/ NULLIF(SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE 0 END), 0), 2) AS value "
            "FROM HessStarSchemaView WHERE [version] = 'Actual'"
        )
        violations = check_sql_sign_convention(sql, HESS_MEASURE_SEMANTICS)
        assert violations, "must flag gross_margin_pct's numerator CASE"
        assert any("COGS" in v for v in violations)
        # The denominator CASE (Revenue-only, ELSE 0, no negation) must not itself
        # contribute a violation -- confirm we're not just flagging "any CASE exists".
        denom_only = (
            "SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE 0 END) AS value "
            "FROM HessStarSchemaView WHERE [version] = 'Actual'"
        )
        assert check_sql_sign_convention(denom_only, HESS_MEASURE_SEMANTICS) == []

    def test_operating_income_else_renegates_cogs_and_sga(self):
        sql = (
            "SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) AS value "
            "FROM HessStarSchemaView "
            "WHERE [account_type] IN ('Revenue', 'COGS', 'SGA') AND [version] = 'Actual'"
        )
        violations = check_sql_sign_convention(sql, HESS_MEASURE_SEMANTICS)
        assert violations, "must flag operating_income's ELSE -[amount] fallthrough"
        flagged_types = {"COGS", "SGA"} & {t for v in violations for t in ("COGS", "SGA") if t in v}
        assert flagged_types == {"COGS", "SGA"}, (
            f"both COGS and SGA fall through to ELSE and are both declared negative; "
            f"expected both flagged, got: {violations}"
        )

    def test_ebitda_else_renegates_cogs_sga_and_other(self):
        # ebitda was NOT in the original 3-KPI manual audit list -- this is the
        # validator finding a 4th live-broken KPI the hand walkthrough missed,
        # exactly the "catches it for the next person" case this step exists for.
        sql = (
            "SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) AS value "
            "FROM HessStarSchemaView "
            "WHERE ([account_type] IN ('Revenue', 'COGS', 'SGA') "
            "OR ([account_type] = 'Other' AND [account_category] = 'D&A')) "
            "AND [version] = 'Actual'"
        )
        violations = check_sql_sign_convention(sql, HESS_MEASURE_SEMANTICS)
        assert violations, "ebitda has the identical ELSE-negation shape as operating_income"

    def test_return_on_capital_else_renegates_cogs_and_sga(self):
        sql = (
            "SELECT ROUND(100.0 * SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) "
            "/ NULLIF(SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE 0 END) * 0.6, 0), 2) AS value "
            "FROM HessStarSchemaView "
            "WHERE [account_type] IN ('Revenue', 'COGS', 'SGA') AND [version] = 'Actual'"
        )
        violations = check_sql_sign_convention(sql, HESS_MEASURE_SEMANTICS)
        assert violations, "return_on_capital's numerator has the same ELSE-negation bug"

    def test_free_cash_flow_capex_branch_not_flagged_unknown_type(self):
        # CapEx isn't declared in stored_sign at all (doesn't exist in this
        # dataset's real account types) -- the validator must not guess; it
        # should silently skip a type it has no sign fact for.
        sql = (
            "SELECT SUM(CASE WHEN [account_type] = 'OperatingCF' THEN [amount] "
            "WHEN [account_type] = 'CapEx' THEN -[amount] ELSE 0 END) AS value "
            "FROM HessStarSchemaView WHERE [account_type] IN ('OperatingCF', 'CapEx') AND [version] = 'Actual'"
        )
        assert check_sql_sign_convention(sql, HESS_MEASURE_SEMANTICS) == []


class TestCleanKpisAreNotFlagged:
    """scripts/clients/lubricants.py and apex_lubricants.py -- SQL that gets the sign right."""

    def test_lubricants_gross_profit_in_list_no_negation(self):
        sql = (
            "SELECT SUM(amount) AS value FROM LubricantsStarSchemaView "
            "WHERE account_type IN ('Revenue', 'COGS') AND version = 'Actual'"
        )
        assert check_sql_sign_convention(sql, LUBRICANTS_MEASURE_SEMANTICS) == []

    def test_lubricants_gross_margin_numerator_case_in_list_no_negation(self):
        sql = (
            "SELECT ROUND(100.0 * SUM(CASE WHEN account_type IN ('Revenue', 'COGS') THEN amount ELSE 0 END) "
            "/ NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END), 0), 2) AS value "
            "FROM LubricantsStarSchemaView WHERE version = 'Actual'"
        )
        assert check_sql_sign_convention(sql, LUBRICANTS_MEASURE_SEMANTICS) == []

    def test_apex_gross_profit_explicit_when_no_negation(self):
        sql = (
            "SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount "
            "WHEN account_type = 'COGS' THEN amount ELSE 0 END) AS value "
            "FROM ApexStarSchemaView WHERE version = 'Actual'"
        )
        assert check_sql_sign_convention(sql, LUBRICANTS_MEASURE_SEMANTICS) == []

    def test_standalone_cogs_negation_is_legitimate_not_flagged(self):
        # apex_lubricants' `cogs` KPI: negating an ALREADY-negative measure that
        # is the ONLY thing being summed (no CASE, no sibling branch to fight)
        # is a legitimate "show this cost as a positive number" KPI, not a sign
        # bug. No CASE block exists here at all -- nothing for the validator to
        # inspect, by design (see module docstring).
        sql = "SELECT SUM(-amount) AS value FROM ApexStarSchemaView WHERE account_type = 'COGS' AND version = 'Actual'"
        assert check_sql_sign_convention(sql, LUBRICANTS_MEASURE_SEMANTICS) == []

    def test_apex_dna_branch_on_different_column_not_flagged(self):
        # WHEN account_category = 'D&A' is keyed on a different column than
        # type_column ('account_type') -- not attributable to a declared sign,
        # must be silently skipped rather than guessed at.
        sql = (
            "SELECT SUM(CASE WHEN account_type IN ('Revenue','COGS','SGA') THEN amount "
            "WHEN account_category = 'D&A' THEN -amount ELSE 0 END) AS value "
            "FROM ApexStarSchemaView WHERE version = 'Actual'"
        )
        assert check_sql_sign_convention(sql, LUBRICANTS_MEASURE_SEMANTICS) == []


class TestNonFatalOnMalformedInput:
    def test_measure_semantics_none_is_noop(self):
        assert check_sql_sign_convention("SELECT SUM(-amount) FROM t WHERE account_type='COGS'", None) == []

    def test_empty_sql_is_noop(self):
        assert check_sql_sign_convention("", LUBRICANTS_MEASURE_SEMANTICS) == []

    def test_missing_stored_sign_key_is_noop(self):
        assert check_sql_sign_convention(
            "SELECT SUM(CASE WHEN account_type='COGS' THEN -amount ELSE 0 END) FROM t",
            {"type_column": "account_type", "amount_column": "amount"},
        ) == []

    def test_malformed_measure_semantics_type_does_not_raise(self):
        # measure_semantics must be a dict; anything else is a no-op, never a raise.
        assert check_sql_sign_convention("SELECT 1", "not-a-dict") == []
        assert check_sql_sign_convention("SELECT 1", ["also", "not", "a", "dict"]) == []

    def test_no_case_block_at_all_is_noop(self):
        assert check_sql_sign_convention(
            "SELECT SUM(amount) AS value FROM t WHERE account_type = 'Revenue'",
            LUBRICANTS_MEASURE_SEMANTICS,
        ) == []


class TestPositiveMeasureUnexpectedNegation:
    def test_negating_a_declared_positive_measure_is_flagged(self):
        sql = (
            "SELECT SUM(CASE WHEN account_type = 'Revenue' THEN -amount "
            "WHEN account_type = 'COGS' THEN amount ELSE 0 END) AS value FROM t"
        )
        violations = check_sql_sign_convention(sql, LUBRICANTS_MEASURE_SEMANTICS)
        assert violations
        assert any("Revenue" in v and "positive" in v for v in violations)
