"""EnterpriseAssessmentEngine._assess_kpi now emits reliability.detection_confidence
audit events (docs/architecture/audit_event_system_design.md, 2026-10-02 scope
extension) -- the second pilot signal for the stage-wise reliability panel,
after DA's [ROLLUP-CHECK] (see test_audit_service.py).

No live DB: AuditService.log is patched to a spy, same convention as the rest
of this suite's assessment-engine tests -- the write path itself is already
covered by test_audit_service.py's mocked-pool tests.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from run_enterprise_assessment import EnterpriseAssessmentEngine
from src.agents.models.assessment_models import AssessmentConfig, KPIAssessmentStatus
from src.agents.models.situation_awareness_models import SituationSeverity


def _engine(severity_floor=0.3):
    config = AssessmentConfig(severity_floor=severity_floor, client_id="lubricants")
    return EnterpriseAssessmentEngine(orchestrator=AsyncMock(), registry_factory=None, config=config)


def _kpi(kpi_id="gross_margin_pct", confidence_floor=0.6):
    return SimpleNamespace(
        id=kpi_id,
        name=kpi_id,
        client_id="lubricants",
        monitoring_profile=SimpleNamespace(volatility_band=0.05, confidence_floor=confidence_floor),
        business_process_ids=[],
        filters={},
    )


def _situation(confidence, severity=SituationSeverity.CRITICAL):
    return {"kpi_name": "gross_margin_pct", "severity": severity, "confidence": confidence}


@pytest.mark.asyncio
async def test_detected_emits_pass():
    engine = _engine()
    engine.orchestrator.orchestrate_situation_detection = AsyncMock(
        return_value={"situations": [_situation(confidence=0.9)]}
    )
    with patch("run_enterprise_assessment.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        result = await engine._assess_kpi("run-1", _kpi())

    assert result.status == KPIAssessmentStatus.DETECTED
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["outcome"] == "pass"
    assert kwargs["event_type"] == "reliability.detection_confidence"
    assert kwargs["client_id"] == "lubricants"
    assert kwargs["resource_id"] == "gross_margin_pct"


@pytest.mark.asyncio
async def test_below_confidence_floor_emits_abstain_not_fail():
    engine = _engine()
    engine.orchestrator.orchestrate_situation_detection = AsyncMock(
        return_value={"situations": [_situation(confidence=0.4)]}  # below the 0.6 floor
    )
    with patch("run_enterprise_assessment.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        result = await engine._assess_kpi("run-1", _kpi(confidence_floor=0.6))

    assert result.status == KPIAssessmentStatus.MONITORING
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["outcome"] == "abstain"  # inconclusive, not a defect -- see retention note


@pytest.mark.asyncio
async def test_detection_exception_emits_fail():
    engine = _engine()
    engine.orchestrator.orchestrate_situation_detection = AsyncMock(side_effect=RuntimeError("DPA unreachable"))
    with patch("run_enterprise_assessment.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        result = await engine._assess_kpi("run-1", _kpi())

    assert result.status == KPIAssessmentStatus.ERROR
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["outcome"] == "fail"
    assert kwargs["severity"] == "error"


@pytest.mark.asyncio
async def test_below_threshold_emits_no_reliability_event():
    # Severity gate, not a confidence check -- must not be conflated with the
    # confidence signal (see the wiring comment in run_enterprise_assessment.py).
    engine = _engine(severity_floor=0.9)
    engine.orchestrator.orchestrate_situation_detection = AsyncMock(
        return_value={"situations": [_situation(confidence=0.9, severity=SituationSeverity.LOW)]}
    )
    with patch("run_enterprise_assessment.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        result = await engine._assess_kpi("run-1", _kpi())

    assert result.status == KPIAssessmentStatus.BELOW_THRESHOLD
    spy.assert_not_awaited()


@pytest.mark.asyncio
async def test_audit_failure_never_breaks_the_assessment():
    # AuditService.log already guarantees this internally (test_audit_service.py);
    # this confirms the call site doesn't accidentally wrap it in something that
    # would propagate a failure.
    engine = _engine()
    engine.orchestrator.orchestrate_situation_detection = AsyncMock(
        return_value={"situations": [_situation(confidence=0.9)]}
    )
    with patch("run_enterprise_assessment.AuditService.log", new=AsyncMock(return_value=False)):
        result = await engine._assess_kpi("run-1", _kpi())

    assert result.status == KPIAssessmentStatus.DETECTED
