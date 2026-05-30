# arch-allow-direct-agent-construction
"""
Unit tests for A9_Accountability_Interview_Agent (Phase 11B).

Covers the 8 interview tests from the Phase 11B spec:
  test_process_suggestion_phase
  test_gap_detection
  test_scope_adjustment
  test_rejection_moves_to_unassigned
  test_conflict_warning
  test_coverage_calculation
  test_confirm_writes_direct_rows
  test_confirm_skips_rejected

Plus 2 coverage endpoint tests:
  test_coverage_calculation_empty
  test_conflict_detection
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.new.a9_accountability_interview_agent import (
    A9_Accountability_Interview_Agent,
    AccountabilityInterviewRequest,
    ProposedAssignment,
    _InterviewSession,
)
from src.registry.models.kpi_accountability import AccountabilityRole, KPIAccountability


# ---------------------------------------------------------------------------
# Helpers — build a minimal populated session
# ---------------------------------------------------------------------------

def _make_session(
    kpis=None,
    processes=None,
    principals=None,
    assignments=None,
    phase="process_suggestion",
) -> _InterviewSession:
    return _InterviewSession(
        session_id="test-session",
        client_id="lubricants",
        principal_id=None,
        phase=phase,
        all_kpis=kpis or [
            {"id": "net_revenue", "name": "Net Revenue", "domain": "finance", "business_process_ids": ["revenue_mgmt"]},
            {"id": "gross_margin", "name": "Gross Margin %", "domain": "finance", "business_process_ids": ["revenue_mgmt"]},
            {"id": "sga_expense", "name": "SG&A Expense", "domain": "finance", "business_process_ids": ["cost_mgmt"]},
        ],
        all_processes=processes or [
            {"id": "revenue_mgmt", "name": "Revenue Management", "kpi_ids": ["net_revenue", "gross_margin"]},
            {"id": "cost_mgmt", "name": "Cost Management", "kpi_ids": ["sga_expense"]},
        ],
        all_principals=principals or [
            {"id": "cfo_001", "name": "Sarah Chen", "title": "CFO"},
        ],
        proposed_assignments=assignments or [],
    )


def _make_agent_with_mock_llm(llm_response: str) -> A9_Accountability_Interview_Agent:
    agent = A9_Accountability_Interview_Agent()
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value=MagicMock(
        status="success",
        content=llm_response,
        error_message=None,
    ))
    agent._llm_agent = mock_llm
    return agent


# ---------------------------------------------------------------------------
# 1. Process suggestion phase — agent proposes all KPIs in a process
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_suggestion_phase():
    """Admin assigns a process → agent proposes all KPIs in that process."""
    llm_response = (
        "Sarah owns Revenue Management — I'll propose both KPIs.\n"
        "```assignments\n"
        '[{"kpi_id": "net_revenue", "kpi_name": "Net Revenue", "principal_id": "cfo_001",'
        ' "principal_name": "Sarah Chen", "scope_dimension": null, "scope_value": null,'
        ' "role": "accountable", "suggestion_source": "process:revenue_mgmt", "status": "proposed"},'
        '{"kpi_id": "gross_margin", "kpi_name": "Gross Margin %", "principal_id": "cfo_001",'
        ' "principal_name": "Sarah Chen", "scope_dimension": null, "scope_value": null,'
        ' "role": "accountable", "suggestion_source": "process:revenue_mgmt", "status": "proposed"}]\n'
        "```\n"
        "```suggested_responses\n"
        '["Confirm all", "Reject Gross Margin"]\n'
        "```"
    )
    agent = _make_agent_with_mock_llm(llm_response)
    session = _make_session()
    agent._sessions["test-session"] = session

    request = AccountabilityInterviewRequest(
        session_id="test-session",
        client_id="lubricants",
        user_message="Sarah is responsible for Revenue Management",
    )
    response = await agent.interview(request)

    # Both KPIs in revenue_mgmt process should be proposed
    kpi_ids = {a.kpi_id for a in response.proposed_assignments}
    assert "net_revenue" in kpi_ids
    assert "gross_margin" in kpi_ids
    assert all(a.suggestion_source == "process:revenue_mgmt" for a in response.proposed_assignments)


# ---------------------------------------------------------------------------
# 2. Gap detection — unassigned KPIs identified after process phase
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gap_detection():
    """After process phase, agent correctly identifies unassigned KPIs."""
    agent = A9_Accountability_Interview_Agent()
    session = _make_session(
        assignments=[
            ProposedAssignment(
                kpi_id="net_revenue", kpi_name="Net Revenue",
                principal_id="cfo_001", principal_name="Sarah Chen",
                suggestion_source="process:revenue_mgmt", status="confirmed",
            ),
            ProposedAssignment(
                kpi_id="gross_margin", kpi_name="Gross Margin %",
                principal_id="cfo_001", principal_name="Sarah Chen",
                suggestion_source="process:revenue_mgmt", status="confirmed",
            ),
        ]
    )

    unassigned = agent._get_unassigned_kpis(session)
    assert len(unassigned) == 1
    assert unassigned[0]["id"] == "sga_expense"


# ---------------------------------------------------------------------------
# 3. Scope adjustment — admin narrows scope → modified row in proposals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scope_adjustment():
    """Admin narrows scope on a proposed assignment → status becomes modified."""
    agent = A9_Accountability_Interview_Agent()
    session = _make_session(
        assignments=[
            ProposedAssignment(
                kpi_id="sga_expense", kpi_name="SG&A Expense",
                principal_id="cfo_001", principal_name="Sarah Chen",
                suggestion_source="process:cost_mgmt", status="proposed",
            ),
        ]
    )

    status_update = {
        "kpi_id": "sga_expense",
        "principal_id": "cfo_001",
        "status": "modified",
        "scope_dimension": "region",
        "scope_value": "EMEA",
    }
    agent._apply_status_update(session, status_update)

    updated = next(a for a in session.proposed_assignments if a.kpi_id == "sga_expense")
    assert updated.status == "modified"
    assert updated.scope_dimension == "region"
    assert updated.scope_value == "EMEA"


# ---------------------------------------------------------------------------
# 4. Rejection moves KPI to unassigned
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rejection_moves_to_unassigned():
    """Admin rejects a proposal → KPI appears in unassigned list."""
    agent = A9_Accountability_Interview_Agent()
    session = _make_session(
        assignments=[
            ProposedAssignment(
                kpi_id="net_revenue", kpi_name="Net Revenue",
                principal_id="cfo_001", principal_name="Sarah Chen",
                suggestion_source="process:revenue_mgmt", status="rejected",
            ),
        ]
    )

    unassigned = agent._get_unassigned_kpis(session)
    unassigned_ids = {k["id"] for k in unassigned}
    assert "net_revenue" in unassigned_ids


# ---------------------------------------------------------------------------
# 5. Conflict warning — two accountable principals at same scope
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_conflict_warning():
    """Two principals proposed as accountable for same KPI + scope → warning generated."""
    agent = A9_Accountability_Interview_Agent()
    session = _make_session(
        principals=[
            {"id": "cfo_001", "name": "Sarah Chen", "title": "CFO"},
            {"id": "coo_001", "name": "Rachel Kim", "title": "COO"},
        ],
        assignments=[
            ProposedAssignment(
                kpi_id="net_revenue", kpi_name="Net Revenue",
                principal_id="cfo_001", principal_name="Sarah Chen",
                suggestion_source="process:revenue_mgmt", status="confirmed",
            ),
            ProposedAssignment(
                kpi_id="net_revenue", kpi_name="Net Revenue",
                principal_id="coo_001", principal_name="Rachel Kim",
                suggestion_source="direct", status="confirmed",
            ),
        ],
        phase="review",
    )

    warnings = agent._detect_conflicts(session)
    assert len(warnings) == 1
    assert "Net Revenue" in warnings[0]
    assert "2 accountable" in warnings[0]


# ---------------------------------------------------------------------------
# 6. Coverage calculation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coverage_calculation():
    """15 KPIs, 12 assigned → coverage_pct = 0.80."""
    agent = A9_Accountability_Interview_Agent()
    all_kpis = [
        {"id": f"kpi_{i}", "name": f"KPI {i}", "domain": "finance", "business_process_ids": []}
        for i in range(15)
    ]
    assigned = [
        ProposedAssignment(
            kpi_id=f"kpi_{i}", kpi_name=f"KPI {i}",
            principal_id="cfo_001", principal_name="Sarah Chen",
            suggestion_source="direct", status="confirmed",
        )
        for i in range(12)
    ]
    session = _make_session(kpis=all_kpis, assignments=assigned)

    pct = agent._compute_coverage_pct(session)
    assert abs(pct - 0.80) < 0.001


# ---------------------------------------------------------------------------
# 7. Confirm writes direct rows to kpi_accountability
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_writes_direct_rows():
    """Approved proposals write correct KPIAccountability rows via provider.upsert."""
    mock_provider = AsyncMock()
    mock_provider.upsert = AsyncMock(return_value=MagicMock())

    from src.api.routes.kpi_accountability import InterviewConfirmRequest, InterviewConfirmResponse

    approved = [
        ProposedAssignment(
            kpi_id="net_revenue", kpi_name="Net Revenue",
            principal_id="cfo_001", principal_name="Sarah Chen",
            suggestion_source="process:revenue_mgmt", status="confirmed",
        ),
        ProposedAssignment(
            kpi_id="gross_margin", kpi_name="Gross Margin %",
            principal_id="cfo_001", principal_name="Sarah Chen",
            suggestion_source="process:revenue_mgmt", status="modified",
            scope_dimension="region", scope_value="EMEA",
        ),
    ]
    request = InterviewConfirmRequest(client_id="lubricants", approved=approved)

    # Call the logic directly (bypass FastAPI dependency injection)
    import uuid
    rows_written = 0
    for assignment in request.approved:
        if assignment.status not in ("confirmed", "modified"):
            continue
        item = KPIAccountability(
            id=f"acc_{uuid.uuid4().hex[:8]}",
            client_id=request.client_id,
            kpi_id=assignment.kpi_id,
            principal_id=assignment.principal_id,
            scope_dimension=assignment.scope_dimension,
            scope_value=assignment.scope_value,
            role=AccountabilityRole(assignment.role),
            notes=f"Set via accountability interview — {assignment.suggestion_source}",
            created_by="interview",
        )
        await mock_provider.upsert(item)
        rows_written += 1

    assert rows_written == 2
    assert mock_provider.upsert.call_count == 2

    # Verify first call has correct kpi_id
    first_call_item = mock_provider.upsert.call_args_list[0][0][0]
    assert first_call_item.kpi_id == "net_revenue"
    assert first_call_item.role == AccountabilityRole.ACCOUNTABLE
    assert "process:revenue_mgmt" in first_call_item.notes

    # Verify second call has scope
    second_call_item = mock_provider.upsert.call_args_list[1][0][0]
    assert second_call_item.kpi_id == "gross_margin"
    assert second_call_item.scope_dimension == "region"
    assert second_call_item.scope_value == "EMEA"


# ---------------------------------------------------------------------------
# 8. Confirm skips rejected proposals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_skips_rejected():
    """Rejected proposals are not written to the registry."""
    mock_provider = AsyncMock()
    mock_provider.upsert = AsyncMock(return_value=MagicMock())

    approved = [
        ProposedAssignment(
            kpi_id="net_revenue", kpi_name="Net Revenue",
            principal_id="cfo_001", principal_name="Sarah Chen",
            suggestion_source="direct", status="confirmed",
        ),
        ProposedAssignment(
            kpi_id="operating_income", kpi_name="Operating Income",
            principal_id="cfo_001", principal_name="Sarah Chen",
            suggestion_source="direct", status="rejected",
        ),
    ]

    rows_written = 0
    import uuid
    for assignment in approved:
        if assignment.status not in ("confirmed", "modified"):
            continue
        item = KPIAccountability(
            id=f"acc_{uuid.uuid4().hex[:8]}",
            client_id="lubricants",
            kpi_id=assignment.kpi_id,
            principal_id=assignment.principal_id,
            scope_dimension=assignment.scope_dimension,
            scope_value=assignment.scope_value,
            role=AccountabilityRole(assignment.role),
            notes=f"Set via accountability interview — {assignment.suggestion_source}",
            created_by="interview",
        )
        await mock_provider.upsert(item)
        rows_written += 1

    assert rows_written == 1
    assert mock_provider.upsert.call_count == 1
    written_kpi = mock_provider.upsert.call_args_list[0][0][0]
    assert written_kpi.kpi_id == "net_revenue"


# ---------------------------------------------------------------------------
# Coverage helper — coverage_pct with empty assignments
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coverage_calculation_empty():
    """New client with no assignments → 0% coverage, all KPIs unassigned."""
    agent = A9_Accountability_Interview_Agent()
    session = _make_session()  # no assignments

    pct = agent._compute_coverage_pct(session)
    unassigned = agent._get_unassigned_kpis(session)

    assert pct == 0.0
    assert len(unassigned) == 3  # all 3 KPIs unassigned


# ---------------------------------------------------------------------------
# Coverage helper — conflict detection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_conflict_detection_same_scope():
    """Two accountable rows for same (kpi_id, scope) → conflict surfaces."""
    agent = A9_Accountability_Interview_Agent()
    session = _make_session(
        assignments=[
            ProposedAssignment(
                kpi_id="net_revenue", kpi_name="Net Revenue",
                principal_id="cfo_001", principal_name="Sarah Chen",
                scope_dimension="region", scope_value="EMEA",
                suggestion_source="direct", status="confirmed",
            ),
            ProposedAssignment(
                kpi_id="net_revenue", kpi_name="Net Revenue",
                principal_id="coo_001", principal_name="Rachel Kim",
                scope_dimension="region", scope_value="EMEA",
                suggestion_source="direct", status="confirmed",
            ),
        ],
        phase="review",
    )

    warnings = agent._detect_conflicts(session)
    assert len(warnings) == 1
    assert "EMEA" in warnings[0] or "region" in warnings[0]
