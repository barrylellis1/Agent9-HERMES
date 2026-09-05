"""
Phase 22 Stage A — the `portfolio_exit` lever family.

Added 2026-09-05 after reading the frontier_bakeoff_2026-09-04 corpus: 5 real
options across both arms (fable + astra) described the same real mechanism —
exit/de-emphasize an underperforming segment or tier, redirect to
margin-accretive ones — with no bucket in the taxonomy, because none phrase
it near the word "mix" (the only thing that would have caught it under
mix_shift's own `reallocat...mix` pattern).

Per this taxonomy's own provenance rule (mechanism.py's module docstring: "An
earlier guessed taxonomy... did not survive contact with the data"), these
tests are built from the real corpus text, not invented examples — including
the one false positive found and removed before shipping (a bare `withdraw`
pattern that caught "withdrawal of discretionary, noncontractual promotions"
in an option whose real thesis was demand repositioning, not a portfolio
exit).
"""
from __future__ import annotations

from src.analysis.mechanism import UNCLASSIFIED, classify_lever


class TestPortfolioExitFamily:
    """The 5 titles that motivated adding this family — frontier_bakeoff_2026-09-04."""

    def test_de_emphasize_and_redirect(self):
        fam, _ = classify_lever(
            "Portfolio Reallocation: De-emphasize Structurally Impaired Value-Tier "
            "Grades, Redirect to Margin-Accretive Formulations"
        )
        assert fam == "portfolio_exit"

    def test_portfolio_repositioning(self):
        fam, _ = classify_lever(
            "Portfolio Repositioning: Shift Volume Toward Structurally "
            "Higher-Margin Formulations"
        )
        assert fam == "portfolio_exit"

    def test_value_tier_portfolio_reallocation_decision(self):
        fam, _ = classify_lever(
            "COGS Component Waterfall & Value-Tier Portfolio Reallocation Decision"
        )
        assert fam == "portfolio_exit"

    def test_gated_withdrawal_and_reallocation(self):
        fam, _ = classify_lever(
            "Gated Value-Tier Withdrawal and Higher-Contribution Portfolio Reallocation"
        )
        assert fam == "portfolio_exit"

    def test_gate_specialty_reallocation(self):
        fam, _ = classify_lever("Gate Specialty Reallocation on Restored Contribution")
        assert fam == "portfolio_exit"


class TestTitleThesisBeatsDescriptionFallback:
    """4 more corpus options had NO title-level match under the pre-fix
    taxonomy at all and fell through to a description-fallback family picked
    up incidentally — landing on `indexation`, `pricing_corridor`, or
    `replication` depending on what unrelated word appeared in the prose.
    mechanism.py's own docstring rule is that a title match must always beat
    a description fallback; these assert that rule now actually holds for
    options whose title's real thesis is a portfolio exit.
    """

    def test_cogs_driver_isolation_title(self):
        fam, _ = classify_lever(
            "COGS Driver Isolation and Conditional Portfolio Reallocation "
            "Toward Higher-Margin Synthetic Grades",
            description="Decompose year-to-date COGS by account category...",
        )
        assert fam == "portfolio_exit"

    def test_portfolio_reallocation_with_deemphasis_title(self):
        fam, _ = classify_lever(
            "Portfolio Reallocation Toward Specialty Formulations, "
            "De-Emphasizing Conventional Grade",
            description="Reallocate sales effort and inventory toward specialty formulations...",
        )
        assert fam == "portfolio_exit"

    def test_gated_portfolio_reallocation_with_cost_removal_title(self):
        fam, _ = classify_lever(
            "Gated Portfolio Reallocation with Avoidable-Cost Removal",
            description="Replace the proposed audit-led approach with selective "
                        "non-renewal or service redesign...",
        )
        assert fam == "portfolio_exit"

    def test_revenue_protected_portfolio_reallocation_title(self):
        fam, _ = classify_lever(
            "Revenue-Protected Portfolio Reallocation",
            description="Redirect discretionary sales capacity and replenishment "
                        "investment from selected Synthetic Blend Engine Oil business...",
        )
        assert fam == "portfolio_exit"


class TestFalsePositiveRemoved:
    """A bare `withdraw` pattern was drafted, then removed before shipping: it
    was responsible for zero of the 9 correct reclassifications above and
    exactly one false positive — this option's real thesis is demand
    repositioning (closer to mix_shift), description-matched only via
    "withdrawal of discretionary, noncontractual promotions", a commercial-
    terms detail, not a portfolio exit. Regression guard: if `withdraw` (or
    anything as broad) is reintroduced, this must start failing.
    """

    def test_promotional_withdrawal_is_not_a_portfolio_exit(self):
        fam, _ = classify_lever(
            "Gate Premium Repositioning on Retained Gross Profit",
            description=(
                "Reposition selected Synthetic Blend demand toward higher-value "
                "formulations through customer-consented substitution and "
                "withdrawal of discretionary, noncontractual promotions. Do not "
                "move volume automatically..."
            ),
        )
        assert fam != "portfolio_exit"


class TestDoesNotStealFromMoreSpecificFamilies:
    """portfolio_exit is deliberately placed after mix_shift and
    volume_for_margin in LEVER_PATTERNS so a same-position tie resolves in
    their favor. This is the tie the placement exists to protect."""

    def test_reallocate_near_mix_still_wins_mix_shift(self):
        fam, _ = classify_lever("Reallocate Toward a Premium Mix")
        assert fam == "mix_shift"

    def test_walk_away_still_wins_volume_for_margin(self):
        fam, _ = classify_lever("Walk Away From Unprofitable Anchor Accounts")
        assert fam == "volume_for_margin"


class TestUnrelatedOptionsUnaffected:
    def test_plain_indexation_option_unaffected(self):
        fam, _ = classify_lever("Base Oil Cost-Indexing Clause via Accelerated Contract Renewal")
        assert fam == "indexation"

    def test_option_with_no_recognizable_lever_stays_unclassified(self):
        fam, _ = classify_lever("Convene a Cross-Functional Task Force")
        assert fam == UNCLASSIFIED
