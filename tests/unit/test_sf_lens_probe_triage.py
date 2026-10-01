"""Phase 22 addendum (2026-10-01) — lens-probe TRIAGE.

Driving production showed every probe question was a data request no CFO could
answer from the chair ("month-by-month volume-weighted cost-per-unit for each of
the three flagged products"). The prompt constrained only for
framework-distinctiveness, and maximising that pushes toward precise warehouse
queries, because that is where frameworks are most specific.

So a lens now decides WHO can answer: a `data_query` is resolved before
hypotheses form; only a `human_question` reaches the principal.

Covers the branch the pre-existing lens-probe tests do NOT reach — they mock
`analysis={"question": ...}` with no `kind`, which correctly falls through to the
human branch, so they pass unchanged and prove nothing about this path.
"""
import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent, _describe_queryable

LENS_COUNCIL = ["commercial", "operational", "structural"]


def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name, data_product_id="dp_x")


def _patched_provider():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "lubricants")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class _TriageOrchestrator:
    """Returns a per-persona triage verdict, plus a DPA stub for data queries."""

    def __init__(self, verdicts, *, dpa=None):
        self.verdicts = verdicts
        self.dpa = dpa

    async def get_agent(self, name, *a, **k):
        if name == "A9_Data_Product_Agent":
            return self.dpa
        return None

    async def execute_agent_method(self, agent_name, method_name, params):
        req = params.get("request")
        req_id = getattr(req, "request_id", "")
        assert "_lensprobe_" in req_id
        persona_id = req_id.rsplit("_lensprobe_", 1)[-1]
        return SimpleNamespace(status="success", request_id=req_id,
                               analysis=self.verdicts[persona_id],
                               model_used="mock", usage={})


def _dpa(*, rows=None, kpi_found=True, sql="SELECT 1"):
    d = MagicMock()
    d.get_kpi_definition = AsyncMock(
        return_value=_kpi("gross_margin_pct", "lubricants") if kpi_found else None
    )
    d.generate_sql_for_kpi = AsyncMock(return_value={"success": True, "sql": sql})
    d.execute_sql = AsyncMock(return_value={"success": True, "rows": rows if rows is not None else [{"v": 1}]})
    return d


DATA_Q = {"kind": "data_query", "kpi": "Gross Margin %", "dimension": "Product Line",
          "timeframe": "year_to_date", "comparison": True, "why": "separates cost from mix"}
HUMAN_Q = {"kind": "human_question", "question": "Did finance change costing allocation in Q3?",
           "why": "not recorded anywhere in the data"}


async def _build_sf(monkeypatch, orch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True, "enable_hybrid_council": True,
        "enable_causal_grounding": False,
    })
    await sf.connect()
    sf.orchestrator = orch
    sf.llm_service_agent = None  # force the orchestrator path
    return sf


def _request():
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"}},
        client_id="lubricants",
        preferences={"debate_stage": "lens_probe", "consulting_personas": LENS_COUNCIL},
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


async def _run(sf, request):
    with _patched_provider(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        return await sf.recommend_actions(request)


def _sol(resp):
    """The response exposes these as top-level fields (see
    test_sf_lens_probe_generation.py, which reads resp.lens_probe_questions)."""
    return {
        "lens_probe_questions": getattr(resp, "lens_probe_questions", None) or {},
        "lens_probe_findings": getattr(resp, "lens_probe_findings", None) or {},
    }


class TestTriage:
    @pytest.mark.asyncio
    async def test_data_query_is_answered_and_never_shown_to_the_principal(self, monkeypatch):
        """The whole point: a question the warehouse can answer must not become
        homework for a CFO."""
        dpa = _dpa(rows=[{"product_line": "Engine Oils", "value": 39359562.24}])
        orch = _TriageOrchestrator({p: DATA_Q for p in LENS_COUNCIL}, dpa=dpa)
        sf = await _build_sf(monkeypatch, orch)
        resp = await _run(sf, _request())
        sol = _sol(resp)

        findings = sol.get("lens_probe_findings") or {}
        questions = sol.get("lens_probe_questions") or {}
        assert set(findings) == set(LENS_COUNCIL), "all three answered from data"
        assert questions == {}, "nothing should be asked of the principal"
        assert findings["commercial"]["rows"][0]["product_line"] == "Engine Oils"

    @pytest.mark.asyncio
    async def test_human_question_still_reaches_the_principal(self, monkeypatch):
        orch = _TriageOrchestrator({p: HUMAN_Q for p in LENS_COUNCIL}, dpa=_dpa())
        sf = await _build_sf(monkeypatch, orch)
        sol = _sol(await _run(sf, _request()))
        assert set(sol.get("lens_probe_questions") or {}) == set(LENS_COUNCIL)
        assert not (sol.get("lens_probe_findings") or {})

    @pytest.mark.asyncio
    async def test_mixed_council_splits_correctly(self, monkeypatch):
        """The real UX case: some lenses answer themselves, one needs a person."""
        dpa = _dpa(rows=[{"v": 1}])
        orch = _TriageOrchestrator(
            {"commercial": DATA_Q, "operational": DATA_Q, "structural": HUMAN_Q}, dpa=dpa)
        sf = await _build_sf(monkeypatch, orch)
        sol = _sol(await _run(sf, _request()))
        assert set(sol.get("lens_probe_findings") or {}) == {"commercial", "operational"}
        assert set(sol.get("lens_probe_questions") or {}) == {"structural"}

    @pytest.mark.asyncio
    async def test_unanswerable_query_degrades_to_a_question_not_silence(self, monkeypatch):
        """A warehouse failure must stay visible. Dropping the lens entirely
        would read as 'this lens had nothing to ask'."""
        orch = _TriageOrchestrator({p: DATA_Q for p in LENS_COUNCIL}, dpa=_dpa(kpi_found=False))
        sf = await _build_sf(monkeypatch, orch)
        sol = _sol(await _run(sf, _request()))
        assert not (sol.get("lens_probe_findings") or {})
        assert set(sol.get("lens_probe_questions") or {}) == set(LENS_COUNCIL)

    @pytest.mark.asyncio
    async def test_kpi_lookup_is_tenant_scoped(self, monkeypatch):
        """Regression guard. get_kpi_definition without client_id resolved
        another tenant's KPI in production (fixed 2026-10-01); this path must
        never reintroduce it."""
        dpa = _dpa(rows=[{"v": 1}])
        orch = _TriageOrchestrator({p: DATA_Q for p in LENS_COUNCIL}, dpa=dpa)
        sf = await _build_sf(monkeypatch, orch)
        await _run(sf, _request())
        assert dpa.get_kpi_definition.await_count >= 1
        for call in dpa.get_kpi_definition.await_args_list:
            assert call.kwargs.get("client_id") == "lubricants", \
                "every KPI lookup must carry the tenant key"

    @pytest.mark.asyncio
    async def test_absent_kind_is_treated_as_a_human_question(self, monkeypatch):
        """Backward compatibility with the pre-triage response shape."""
        orch = _TriageOrchestrator({p: {"question": "legacy shape"} for p in LENS_COUNCIL}, dpa=_dpa())
        sf = await _build_sf(monkeypatch, orch)
        sol = _sol(await _run(sf, _request()))
        assert set(sol.get("lens_probe_questions") or {}) == set(LENS_COUNCIL)


class TestQueryableVocabulary:
    def test_is_tenant_scoped(self):
        """Listing another client's KPIs would invite a lens to ask for them by
        name -- the read-side leak get_kpi_definition was fixed for."""
        import logging
        provider = MagicMock()
        provider.get_all.return_value = [
            _kpi("gross_margin_pct", "lubricants", "Gross Margin %"),
            _kpi("secret_kpi", "hess", "Hess Only Metric"),
        ]
        factory = MagicMock()
        factory.get_provider.side_effect = lambda n: provider if n == "kpi" else None
        with patch("src.registry.factory.RegistryFactory", return_value=factory):
            out = _describe_queryable("lubricants", logging.getLogger("t"))
        assert "Gross Margin %" in out
        assert "Hess Only Metric" not in out, "another tenant's KPI must never be offered"

    def test_empty_vocabulary_degrades_safely(self):
        import logging
        provider = MagicMock()
        provider.get_all.return_value = []
        factory = MagicMock()
        factory.get_provider.return_value = provider
        with patch("src.registry.factory.RegistryFactory", return_value=factory):
            out = _describe_queryable("lubricants", logging.getLogger("t"))
        assert "ask a person" in out.lower(), "no vocabulary must push toward the human, not a guess"
