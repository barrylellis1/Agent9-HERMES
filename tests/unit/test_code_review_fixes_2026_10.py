"""Fixes from the 2026-10 code review, owner go-ahead 2026-10-29.

1  Situation ids named only the KPI and a rounded figure, so two clients (and two months) shared
   a stored card. Ids now come from client, KPI, kind of card and period; a re-scan keeps the
   card's status.
2  A solution's id had no client, so two clients shared a solution row.
10 The email "approve" link called a method that does not exist and still reported an approval.
4  Acceleration ignored direction: a sudden revenue jump was carded "deterioration is accelerating".
6  Value Assurance's "Ahead of Plan" ignored direction: a cost 10% over budget read "Ahead".
"""
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent, _card_id
from src.agents.new.a9_value_assurance_agent import A9_Value_Assurance_Agent, _vs_plan
from src.agents.models.value_assurance_models import RegisterSolutionRequest, StrategySnapshot, VsPlanVerdict


# ---------------------------------------------------------------- 1. situation ids

def _card(kpi="net_revenue", period="ytd_vs_pytd", ref="2026-09-30", card_type="problem", alert_type="plan_variance"):
    ctx = SimpleNamespace(period_comparison=period, reference_day=ref)
    return SimpleNamespace(
        situation_id="plan_net_revenue_16", kpi_id=kpi, kpi_name="Net Revenue", card_type=card_type,
        alert_type=alert_type, dedupe_key=None, comparison_label=None, kpi_value=SimpleNamespace(context=ctx),
    )


def test_two_clients_never_share_a_card_id():
    assert _card_id("lubricants", _card()) != _card_id("apex_lubricants", _card())


def test_a_later_period_gets_its_own_card():
    assert _card_id("lubricants", _card(ref="2026-09-30")) != _card_id("lubricants", _card(ref="2026-10-31"))


def test_a_rescan_of_the_same_period_lands_on_the_same_card():
    # Whichever pattern leads the merged card this time, a problem card for the KPI and period
    # keeps its id, so its status (Analyzing, Solution approved) survives the re-scan.
    a = _card_id("lubricants", _card(alert_type="plan_variance"))
    b = _card_id("lubricants", _card(alert_type="threshold_breach"))
    assert a == b


def test_ids_name_no_client_and_are_url_safe():
    sid = _card_id("lubricants", _card())
    assert "lubricants" not in sid and sid.startswith("sit_")
    assert all(c.isalnum() or c == "_" for c in sid)


def test_two_cards_in_one_scan_never_share_an_id():
    cards = [_card(card_type="opportunity", alert_type="outperformance"),
             _card(card_type="opportunity", alert_type="outperformance")]
    A9_Situation_Awareness_Agent._assign_card_ids(cards, "lubricants")
    assert cards[0].situation_id != cards[1].situation_id


class _Resp:
    status_code = 201
    text = ""


class _Client:
    posted = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        _Client.posted.append(json)
        return _Resp()


@pytest.mark.asyncio
async def test_a_rescan_does_not_reset_the_stored_status(monkeypatch):
    from src.database import situations_store as ss
    from src.agents.models.situation_awareness_models import OpportunitySignal

    monkeypatch.setenv("SUPABASE_URL", "http://supabase.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    _Client.posted = []
    with patch.object(ss.httpx, "AsyncClient", _Client):
        store = ss.SituationsStore()
        sit = SimpleNamespace(situation_id="sit_x", card_type="opportunity", kpi_name="Net Revenue",
                              kpi_value=None, severity="medium", description="d")
        with patch.object(ss, "_safe_json", lambda o: {}):
            assert await store.upsert_situation(sit)
        opp = OpportunitySignal(kpi_name="Net Revenue", kpi_display_name="Net Revenue", current_value=1.0,
                                baseline_value=0.9, delta_pct=11.0, opportunity_type="outperformance", headline="h")
        assert await store.upsert_opportunity(opp, "lubricants")
    situation_row, opportunity_row = _Client.posted
    assert "status" not in situation_row and "status" not in opportunity_row
    assert situation_row["card_type"] == "opportunity"  # was hard-coded "problem"
    assert opportunity_row["id"] != ss._stable_opportunity_id(opp, "apex_lubricants")


# ---------------------------------------------------------------- 2. solution ids

@pytest_asyncio.fixture
async def va():
    from src.agents.agent_config_models import A9ValueAssuranceAgentConfig

    class _Store:
        enabled = True

        def __getattr__(self, name):
            async def _noop(*a, **k):
                return True
            return _noop

    a = await A9_Value_Assurance_Agent.create_from_registry(A9ValueAssuranceAgentConfig(log_all_requests=False).model_dump())
    a.orchestrator = None
    a._va_store = _Store()
    return a


def _register(client_id):
    return RegisterSolutionRequest(
        request_id="r", principal_id="cfo_001", situation_id="sit_same", kpi_id="net_revenue", client_id=client_id,
        solution_description="d", expected_impact_lower=1.0, expected_impact_upper=2.0,
        strategy_snapshot=StrategySnapshot(principal_priorities=[], principal_role="CFO", business_process_domain="Finance",
                                           data_product_id="dp", kpi_threshold_at_approval=1.0, key_assumptions=[],
                                           business_context_name="c", captured_at="2026-10-29T00:00:00Z"),
    )


@pytest.mark.asyncio
async def test_two_clients_never_share_a_solution(va):
    a = await va.register_solution(_register("lubricants"))
    b = await va.register_solution(_register("apex_lubricants"))
    assert a.solution_id != b.solution_id
    again = await va.register_solution(_register("lubricants"))
    assert again.solution_id == a.solution_id  # the same approval fired twice still lands on one row


# ---------------------------------------------------------------- 10. email approve

@pytest.mark.asyncio
async def test_an_old_approve_link_claims_no_approval():
    from src.api.routes import pib

    class _Briefings:
        async def validate_and_consume_token(self, token):
            return {"token_type": "approve", "situation_id": "sit_x", "principal_id": "cfo_001",
                    "kpi_assessment_id": "ka-1"}

    with patch("src.database.briefing_store.BriefingStore", _Briefings):
        resp = await pib.execute_token_action("tok", runtime=None)
    assert resp.action_taken == "review_redirect"
    assert "approved" not in resp.message.lower() or "not available" in resp.message.lower()
    assert resp.redirect_url.endswith("/value-assurance")


def test_briefings_issue_no_approve_links():
    import inspect
    from src.agents.new import a9_pib_agent

    assert "TokenType.APPROVE" not in inspect.getsource(a9_pib_agent.A9_PIB_Agent._populate_solutions)


# ---------------------------------------------------------------- 4. acceleration direction

def _sa():
    return A9_Situation_Awareness_Agent.__new__(A9_Situation_Awareness_Agent)


def _months(values):
    return [{"period": f"2026-{i + 1:02d}", "value": v} for i, v in enumerate(values)]


class TestAccelerationDirection:
    # velocities -2,-2,-2,-2,-40: a revenue falling faster (the existing positive case)
    FALLING_FASTER = [100, 98, 96, 94, 92, 52]
    # its mirror: rising faster
    RISING_FASTER = [52, 54, 56, 58, 60, 100]

    def test_a_revenue_falling_faster_fires(self):
        assert _sa()._compute_acceleration(_months(self.FALLING_FASTER)) is not None

    def test_a_sudden_revenue_jump_does_not_fire(self):
        assert _sa()._compute_acceleration(_months(self.RISING_FASTER)) is None

    def test_a_cost_rising_faster_fires_in_both_sign_conventions(self):
        sa = _sa()
        assert sa._compute_acceleration(_months(self.RISING_FASTER), lower_is_better=True) is not None
        assert sa._compute_acceleration(_months([-v for v in self.RISING_FASTER]), lower_is_better=True) is not None

    def test_a_cost_falling_faster_does_not_fire_in_either_convention(self):
        sa = _sa()
        assert sa._compute_acceleration(_months(self.FALLING_FASTER), lower_is_better=True) is None
        assert sa._compute_acceleration(_months([-v for v in self.FALLING_FASTER]), lower_is_better=True) is None

    def test_growth_that_is_only_slowing_does_not_fire(self):
        # still rising every month, just by less: velocities 10,10,10,10,1
        assert _sa()._compute_acceleration(_months([100, 110, 120, 130, 140, 141])) is None


# ---------------------------------------------------------------- 6. vs plan direction

class TestVsPlanDirection:
    def test_a_revenue_above_plan_is_ahead(self):
        assert _vs_plan(110.0, 100.0, False)[1] == VsPlanVerdict.AHEAD_OF_PLAN

    def test_a_cost_over_budget_is_behind_in_both_sign_conventions(self):
        assert _vs_plan(110.0, 100.0, True)[1] == VsPlanVerdict.BEHIND_PLAN
        assert _vs_plan(-110.0, -100.0, True)[1] == VsPlanVerdict.BEHIND_PLAN

    def test_a_cost_under_budget_is_ahead_in_both_sign_conventions(self):
        assert _vs_plan(90.0, 100.0, True)[1] == VsPlanVerdict.AHEAD_OF_PLAN
        assert _vs_plan(-90.0, -100.0, True)[1] == VsPlanVerdict.AHEAD_OF_PLAN

    def test_the_percentage_stays_literal(self):
        assert _vs_plan(110.0, 100.0, True)[0] == pytest.approx(0.10)

    def test_within_two_percent_is_on_plan_and_no_plan_is_no_data(self):
        assert _vs_plan(101.0, 100.0, True)[1] == VsPlanVerdict.ON_PLAN
        assert _vs_plan(5.0, None, False) == (None, VsPlanVerdict.NO_PLAN_DATA)


# ---------------------------------------------------------------- 1b. cards carry their client

class _ReadClient:
    params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, headers=None, params=None):
        _ReadClient.params = params
        return SimpleNamespace(content=b"[]", raise_for_status=lambda: None)


@pytest.mark.asyncio
async def test_a_stored_card_records_its_client(monkeypatch):
    from src.database import situations_store as ss

    monkeypatch.setenv("SUPABASE_URL", "http://supabase.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    _Client.posted = []
    with patch.object(ss.httpx, "AsyncClient", _Client), patch.object(ss, "_safe_json", lambda o: {}):
        store = ss.SituationsStore()
        sit = SimpleNamespace(situation_id="sit_x", card_type="problem", kpi_name="Net Revenue",
                              kpi_value=None, severity="medium", description="d")
        assert await store.upsert_situation(sit, "lubricants")
        assert await store.upsert_situation(sit)  # no client known: the column is left as it is
    with_client, without_client = _Client.posted
    assert with_client["client_id"] == "lubricants"
    assert "client_id" not in without_client


@pytest.mark.asyncio
async def test_open_cards_are_read_for_one_client_only(monkeypatch):
    from src.database import situations_store as ss

    monkeypatch.setenv("SUPABASE_URL", "http://supabase.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    with patch.object(ss.httpx, "AsyncClient", _ReadClient):
        store = ss.SituationsStore()
        _ReadClient.params = None
        assert await store.get_open_situations("lubricants") == []
        assert _ReadClient.params["client_id"] == "eq.lubricants"
        assert "principal_id" not in _ReadClient.params
        _ReadClient.params = None
        assert await store.get_open_situations(None) == []
        assert _ReadClient.params is None  # no client: no read at all, never every client's cards


def test_the_briefing_reads_only_its_own_clients_cards():
    import inspect
    from src.agents.new import a9_pib_agent

    src = inspect.getsource(a9_pib_agent)
    assert "get_open_situations(config.client_id)" in src
    assert "get_open_situations(principal_id=None)" not in src


def test_the_situations_table_is_in_the_rls_check():
    import importlib.util
    import pathlib

    path = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "verify_prod_registry.py"
    spec = importlib.util.spec_from_file_location("verify_prod_registry", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "situations" in mod._RLS_TABLES
