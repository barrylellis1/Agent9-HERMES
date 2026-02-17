"""
A9_Risk_Analysis_Agent - MVP risk assessment for core business risks.

Provides minimal, reliable risk assessment across three core risk categories:
market risk, operational risk, and financial risk. Uses simple weighted scoring
logic with plain-language summary output.

Protocol compliance:
- All I/O via Pydantic models (A2A protocol)
- Orchestrator-driven lifecycle (create_from_registry / create)
- LLM calls routed through A9_LLM_Service_Agent via orchestrator
- Structured logging via self.logger (A9_SharedLogger pattern)
- Standard lifecycle: create -> connect -> process -> disconnect
- Standard entrypoints: check_access, process_request
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)
from src.agents.agent_config_models import A9RiskAnalysisAgentConfig


logger = logging.getLogger(__name__)


# =============================================================================
# Scoring Constants
# =============================================================================

DEFAULT_WEIGHT_MARKET: float = 0.35
DEFAULT_WEIGHT_OPERATIONAL: float = 0.35
DEFAULT_WEIGHT_FINANCIAL: float = 0.30

RISK_THRESHOLD_LOW: float = 0.33
RISK_THRESHOLD_MEDIUM: float = 0.66

SCORE_MIN: float = 0.0
SCORE_MAX: float = 1.0


# =============================================================================
# Pydantic Input / Output Models
# =============================================================================


class MarketRiskFactors(A9AgentBaseModel):
    """Input factors for market risk assessment. Each factor is [0.0, 1.0]."""

    market_volatility: Optional[float] = Field(None, ge=0.0, le=1.0, description="Degree of price or market volatility")
    competitive_pressure: Optional[float] = Field(None, ge=0.0, le=1.0, description="Intensity of competitive threats")
    demand_uncertainty: Optional[float] = Field(None, ge=0.0, le=1.0, description="Uncertainty in customer demand")
    regulatory_environment: Optional[float] = Field(None, ge=0.0, le=1.0, description="Regulatory change risk")
    macro_economic_exposure: Optional[float] = Field(None, ge=0.0, le=1.0, description="Exposure to macro-economic headwinds")


class OperationalRiskFactors(A9AgentBaseModel):
    """Input factors for operational risk assessment. Each factor is [0.0, 1.0]."""

    process_reliability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk from unreliable processes")
    supply_chain_vulnerability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Exposure to supply chain disruptions")
    technology_dependency: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk from critical technology dependencies")
    talent_retention: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk from key personnel loss")
    compliance_exposure: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk of non-compliance with regulations")


class FinancialRiskFactors(A9AgentBaseModel):
    """Input factors for financial risk assessment. Each factor is [0.0, 1.0]."""

    liquidity_risk: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk of insufficient liquid assets")
    leverage_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk from high debt levels")
    revenue_concentration: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk from revenue source concentration")
    cost_variability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Unpredictability of cost base")
    cash_flow_stability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk from inconsistent cash flows")


class RiskAnalysisRequest(A9AgentBaseRequest):
    """Input model for a risk analysis request."""

    model_config = ConfigDict(extra="allow")

    market_factors: Optional[MarketRiskFactors] = Field(None, description="Market risk input factors")
    operational_factors: Optional[OperationalRiskFactors] = Field(None, description="Operational risk input factors")
    financial_factors: Optional[FinancialRiskFactors] = Field(None, description="Financial risk input factors")

    weight_market: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override weight for market risk")
    weight_operational: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override weight for operational risk")
    weight_financial: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override weight for financial risk")

    business_context_description: Optional[str] = Field(None, description="Free-text business context for summary")


class RiskCategoryResult(A9AgentBaseModel):
    """Result for a single risk category."""

    category: str = Field(..., description="Name of the risk category")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalised risk score")
    severity: str = Field(..., description="Plain-language severity: Low, Medium, or High")
    contributing_factors: List[str] = Field(default_factory=list, description="Top contributing factor names")
    recommendation: str = Field(default="", description="Actionable recommendation for this category")


class RiskAnalysisResponse(A9AgentBaseResponse):
    """Output model for a completed risk analysis."""

    model_config = ConfigDict(extra="allow")

    market_risk: Optional[RiskCategoryResult] = Field(None, description="Market risk result")
    operational_risk: Optional[RiskCategoryResult] = Field(None, description="Operational risk result")
    financial_risk: Optional[RiskCategoryResult] = Field(None, description="Financial risk result")

    composite_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Weighted composite risk score")
    composite_severity: Optional[str] = Field(None, description="Severity label for composite score")
    weights_applied: Optional[Dict[str, float]] = Field(None, description="Weights applied to each category")
    summary: Optional[str] = Field(None, description="Plain-language risk summary")


# =============================================================================
# Agent Implementation
# =============================================================================


class A9_Risk_Analysis_Agent:
    """
    A9 Risk Analysis Agent (MVP)

    Weighted risk scoring across market, operational, and financial categories
    with plain-language stakeholder summaries.

    Lifecycle:
        agent = await A9_Risk_Analysis_Agent.create(config)
        result = await agent.process_request(request)
        await agent.disconnect()

    Registry pattern:
        agent = await AgentRegistry.get_agent("A9_Risk_Analysis_Agent")
        agent = await A9_Risk_Analysis_Agent.create_from_registry(config_dict)
    """

    AGENT_NAME: str = "A9_Risk_Analysis_Agent"
    AGENT_VERSION: str = "1.0.0"

    # ------------------------------------------------------------------
    # Factory classmethods
    # ------------------------------------------------------------------

    @classmethod
    async def create(cls, config: Optional[Dict[str, Any]] = None) -> "A9_Risk_Analysis_Agent":
        """Async factory: creates and connects the agent."""
        inst = cls(config or {})
        await inst.connect()
        return inst

    @classmethod
    def create_from_registry(cls, config_dict: Dict[str, Any]) -> "A9_Risk_Analysis_Agent":
        """Synchronous factory for orchestrator/registry. Caller must call connect() separately."""
        return cls(config_dict)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, config: Dict[str, Any]) -> None:
        self.name: str = self.AGENT_NAME
        self.version: str = self.AGENT_VERSION
        self.config: A9RiskAnalysisAgentConfig = self._resolve_config(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.orchestrator: Optional[Any] = None
        self.llm_service_agent: Optional[Any] = None

        self.logger.info("%s v%s initialised", self.name, self.version)

    # ------------------------------------------------------------------
    # Lifecycle Methods
    # ------------------------------------------------------------------

    async def connect(self, orchestrator: Optional[Any] = None) -> bool:
        """Connect to dependent services. Gracefully degrades if LLM unavailable."""
        try:
            self.orchestrator = orchestrator

            if orchestrator is not None:
                try:
                    self.llm_service_agent = await orchestrator.get_agent("A9_LLM_Service_Agent")
                    self.logger.info("%s connected to A9_LLM_Service_Agent via orchestrator", self.name)
                except Exception as llm_err:
                    self.logger.warning(
                        "%s: LLM Service Agent not available (%s). Falling back to deterministic summaries.",
                        self.name, llm_err,
                    )
                    self.llm_service_agent = None
            else:
                try:
                    from src.agents.new.a9_orchestrator_agent import AgentRegistry
                    self.llm_service_agent = await AgentRegistry.get_agent("A9_LLM_Service_Agent")
                    self.logger.info("%s resolved A9_LLM_Service_Agent via AgentRegistry", self.name)
                except Exception:
                    self.llm_service_agent = None

            self.logger.info("%s connected successfully", self.name)
            return True
        except Exception as exc:
            self.logger.error("%s connect error: %s", self.name, exc)
            return False

    async def disconnect(self) -> bool:
        """Release resources."""
        try:
            self.llm_service_agent = None
            self.orchestrator = None
            self.logger.info("%s disconnected", self.name)
            return True
        except Exception as exc:
            self.logger.error("%s disconnect error: %s", self.name, exc)
            return False

    # ------------------------------------------------------------------
    # Protocol Entrypoints
    # ------------------------------------------------------------------

    async def check_access(self, request: RiskAnalysisRequest) -> bool:
        """MVP: permits all authenticated principals (non-empty principal_id)."""
        try:
            if not request.principal_id or not request.principal_id.strip():
                self.logger.warning("%s check_access denied: missing principal_id (request_id=%s)", self.name, request.request_id)
                return False
            return True
        except Exception as exc:
            self.logger.error("%s check_access error: %s", self.name, exc)
            return False

    async def process_request(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """Primary entrypoint: scores all risk categories and generates summary."""
        req_id = request.request_id
        self.logger.info("%s process_request start (request_id=%s, principal_id=%s)", self.name, req_id, request.principal_id)

        try:
            if not await self.check_access(request):
                return RiskAnalysisResponse(status="error", request_id=req_id, error_message="Access denied: principal_id is missing or unauthorised.")

            weights = self._resolve_weights(request)
            market_result = self._score_market_risk(request.market_factors)
            operational_result = self._score_operational_risk(request.operational_factors)
            financial_result = self._score_financial_risk(request.financial_factors)

            composite_score = (
                market_result.score * weights["market"]
                + operational_result.score * weights["operational"]
                + financial_result.score * weights["financial"]
            )
            composite_score = round(max(SCORE_MIN, min(SCORE_MAX, composite_score)), 4)
            composite_severity = _severity_label(composite_score)

            summary = await self._generate_summary(
                request=request, market_result=market_result,
                operational_result=operational_result, financial_result=financial_result,
                composite_score=composite_score, composite_severity=composite_severity, weights=weights,
            )

            self.logger.info("%s process_request complete (request_id=%s, composite=%.4f, severity=%s)", self.name, req_id, composite_score, composite_severity)

            return RiskAnalysisResponse(
                status="success", request_id=req_id,
                market_risk=market_result, operational_risk=operational_result, financial_risk=financial_result,
                composite_score=composite_score, composite_severity=composite_severity,
                weights_applied=weights, summary=summary,
            )
        except Exception as exc:
            self.logger.error("%s process_request failed (request_id=%s): %s", self.name, req_id, exc, exc_info=True)
            return RiskAnalysisResponse(status="error", request_id=req_id, error_message=f"Risk analysis failed: {exc}")

    # ------------------------------------------------------------------
    # Risk Scoring
    # ------------------------------------------------------------------

    def _score_market_risk(self, factors: Optional[MarketRiskFactors]) -> RiskCategoryResult:
        factor_values: Dict[str, float] = {}
        if factors is not None:
            candidates = {
                "Market Volatility": factors.market_volatility,
                "Competitive Pressure": factors.competitive_pressure,
                "Demand Uncertainty": factors.demand_uncertainty,
                "Regulatory Environment": factors.regulatory_environment,
                "Macro-Economic Exposure": factors.macro_economic_exposure,
            }
            factor_values = {name: _clamp(val) for name, val in candidates.items() if val is not None}

        score, contributing = _compute_score_and_contributors(factor_values)
        return RiskCategoryResult(
            category="market", score=score, severity=_severity_label(score),
            contributing_factors=contributing, recommendation=_market_recommendation(score, contributing),
        )

    def _score_operational_risk(self, factors: Optional[OperationalRiskFactors]) -> RiskCategoryResult:
        factor_values: Dict[str, float] = {}
        if factors is not None:
            candidates = {
                "Process Reliability": factors.process_reliability,
                "Supply Chain Vulnerability": factors.supply_chain_vulnerability,
                "Technology Dependency": factors.technology_dependency,
                "Talent Retention Risk": factors.talent_retention,
                "Compliance Exposure": factors.compliance_exposure,
            }
            factor_values = {name: _clamp(val) for name, val in candidates.items() if val is not None}

        score, contributing = _compute_score_and_contributors(factor_values)
        return RiskCategoryResult(
            category="operational", score=score, severity=_severity_label(score),
            contributing_factors=contributing, recommendation=_operational_recommendation(score, contributing),
        )

    def _score_financial_risk(self, factors: Optional[FinancialRiskFactors]) -> RiskCategoryResult:
        factor_values: Dict[str, float] = {}
        if factors is not None:
            candidates = {
                "Liquidity Risk": factors.liquidity_risk,
                "Leverage Ratio Risk": factors.leverage_ratio,
                "Revenue Concentration": factors.revenue_concentration,
                "Cost Variability": factors.cost_variability,
                "Cash Flow Instability": factors.cash_flow_stability,
            }
            factor_values = {name: _clamp(val) for name, val in candidates.items() if val is not None}

        score, contributing = _compute_score_and_contributors(factor_values)
        return RiskCategoryResult(
            category="financial", score=score, severity=_severity_label(score),
            contributing_factors=contributing, recommendation=_financial_recommendation(score, contributing),
        )

    # ------------------------------------------------------------------
    # Weight Resolution
    # ------------------------------------------------------------------

    def _resolve_weights(self, request: RiskAnalysisRequest) -> Dict[str, float]:
        w_market = float(getattr(self.config, "weight_market", DEFAULT_WEIGHT_MARKET) or DEFAULT_WEIGHT_MARKET)
        w_operational = float(getattr(self.config, "weight_operational", DEFAULT_WEIGHT_OPERATIONAL) or DEFAULT_WEIGHT_OPERATIONAL)
        w_financial = float(getattr(self.config, "weight_financial", DEFAULT_WEIGHT_FINANCIAL) or DEFAULT_WEIGHT_FINANCIAL)

        if request.weight_market is not None:
            w_market = float(request.weight_market)
        if request.weight_operational is not None:
            w_operational = float(request.weight_operational)
        if request.weight_financial is not None:
            w_financial = float(request.weight_financial)

        total = w_market + w_operational + w_financial
        if total <= 0.0:
            self.logger.warning("%s: weight total is zero; falling back to equal weighting", self.name)
            w_market = w_operational = w_financial = 1.0 / 3.0
        else:
            w_market /= total
            w_operational /= total
            w_financial /= total

        return {"market": round(w_market, 6), "operational": round(w_operational, 6), "financial": round(w_financial, 6)}

    # ------------------------------------------------------------------
    # Summary Generation
    # ------------------------------------------------------------------

    async def _generate_summary(self, request, market_result, operational_result, financial_result, composite_score, composite_severity, weights) -> str:
        baseline_summary = _build_deterministic_summary(
            market_result=market_result, operational_result=operational_result,
            financial_result=financial_result, composite_score=composite_score,
            composite_severity=composite_severity, weights=weights,
            business_context=request.business_context_description,
        )

        if self.llm_service_agent is None:
            return baseline_summary

        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_AnalysisRequest

            prompt_content = _build_llm_summary_prompt(
                baseline_summary=baseline_summary, market_result=market_result,
                operational_result=operational_result, financial_result=financial_result,
                composite_score=composite_score, composite_severity=composite_severity,
                business_context=request.business_context_description,
            )

            llm_request = A9_LLM_AnalysisRequest(
                request_id=f"risk_summary_{request.request_id}",
                principal_id=request.principal_id,
                content=prompt_content,
                analysis_type="risk_summary",
                context=request.business_context_description or "Risk analysis summary generation",
            )

            llm_response = await self.llm_service_agent.analyze(llm_request)

            if llm_response and llm_response.status == "success":
                analysis = getattr(llm_response, "analysis", None) or {}
                narrative = analysis.get("narrative") or analysis.get("summary") or analysis.get("text") or str(analysis)
                if narrative and len(str(narrative).strip()) > 20:
                    return str(narrative).strip()

            return baseline_summary
        except Exception as llm_exc:
            self.logger.warning("%s: LLM summary generation failed (%s); using deterministic summary", self.name, llm_exc)
            return baseline_summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_config(config: Dict[str, Any]) -> A9RiskAnalysisAgentConfig:
        try:
            return A9RiskAnalysisAgentConfig(**(config or {}))
        except Exception as cfg_err:
            logger.warning("A9_Risk_Analysis_Agent: config validation failed (%s); using defaults", cfg_err)
            return A9RiskAnalysisAgentConfig()


# =============================================================================
# Module-Level Helpers
# =============================================================================


def _clamp(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    return max(SCORE_MIN, min(SCORE_MAX, float(value)))


def _severity_label(score: float) -> str:
    if score <= RISK_THRESHOLD_LOW:
        return "Low"
    if score <= RISK_THRESHOLD_MEDIUM:
        return "Medium"
    return "High"


def _compute_score_and_contributors(factor_values: Dict[str, float]) -> tuple:
    if not factor_values:
        return 0.0, []
    avg_score = round(sum(factor_values.values()) / len(factor_values), 4)
    contributing = [name for name, val in sorted(factor_values.items(), key=lambda kv: kv[1], reverse=True) if val > 0.0]
    return avg_score, contributing


def _market_recommendation(score: float, contributors: List[str]) -> str:
    if score <= RISK_THRESHOLD_LOW:
        return "Market risk is currently low. Continue monitoring competitive dynamics and macro-economic indicators."
    top = contributors[0] if contributors else "identified risk factors"
    if score <= RISK_THRESHOLD_MEDIUM:
        return f"Market risk is moderate, primarily driven by {top}. Consider contingency plans for adverse market shifts and review pricing strategy quarterly."
    return f"Market risk is high, with {top} as the most critical driver. Stress-test revenue assumptions, engage key customers, and accelerate diversification."


def _operational_recommendation(score: float, contributors: List[str]) -> str:
    if score <= RISK_THRESHOLD_LOW:
        return "Operational risk is currently low. Maintain existing process controls and conduct periodic resilience reviews."
    top = contributors[0] if contributors else "identified operational factors"
    if score <= RISK_THRESHOLD_MEDIUM:
        return f"Operational risk is moderate, with {top} requiring attention. Review business continuity plans and ensure knowledge-transfer protocols are in place."
    return f"Operational risk is high. {top} is the most pressing concern. Activate contingency procedures and audit critical process dependencies within 30 days."


def _financial_recommendation(score: float, contributors: List[str]) -> str:
    if score <= RISK_THRESHOLD_LOW:
        return "Financial risk is currently low. Continue prudent capital allocation and maintain adequate liquidity reserves."
    top = contributors[0] if contributors else "identified financial factors"
    if score <= RISK_THRESHOLD_MEDIUM:
        return f"Financial risk is moderate, primarily driven by {top}. Review cash-flow forecasts and explore revenue diversification."
    return f"Financial risk is high. {top} is the most critical concern. Escalate to CFO, conduct a liquidity stress test, and implement cost controls."


def _build_deterministic_summary(market_result, operational_result, financial_result, composite_score, composite_severity, weights, business_context=None) -> str:
    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    context_clause = f" for the context described ({business_context.strip()})" if business_context else ""

    opening = (
        f"Risk Assessment Summary ({timestamp_str})\n\n"
        f"This assessment evaluated three core risk categories{context_clause}: "
        f"market risk, operational risk, and financial risk. "
        f"The overall composite risk level is {composite_severity.upper()} "
        f"(score: {composite_score:.2f} on a 0.0-1.0 scale)."
    )

    def _cat_para(result, weight):
        top_str = ", ".join(result.contributing_factors[:3]) if result.contributing_factors else "no specific factors provided"
        return (
            f"{result.category.title()} Risk - {result.severity} "
            f"(score: {result.score:.2f}, weight: {weight:.0%})\n"
            f"  Key drivers: {top_str}.\n"
            f"  Recommendation: {result.recommendation}"
        )

    breakdown = "\n\n".join([
        _cat_para(market_result, weights["market"]),
        _cat_para(operational_result, weights["operational"]),
        _cat_para(financial_result, weights["financial"]),
    ])

    high_risk = [r for r in [market_result, operational_result, financial_result] if r.severity == "High"]
    medium_risk = [r for r in [market_result, operational_result, financial_result] if r.severity == "Medium"]

    if high_risk:
        names = " and ".join(r.category.title() for r in high_risk)
        priority = f"PRIORITY ATTENTION REQUIRED: {names} risk {'is' if len(high_risk) == 1 else 'are'} rated High and should be escalated immediately."
    elif medium_risk:
        names = " and ".join(r.category.title() for r in medium_risk)
        priority = f"Areas to monitor: {names} risk {'is' if len(medium_risk) == 1 else 'are'} rated Medium and warrant near-term management attention."
    else:
        priority = "All three risk categories are currently rated Low. Continue routine monitoring and periodic reassessment."

    return "\n\n".join([opening, breakdown, priority])


def _build_llm_summary_prompt(baseline_summary, market_result, operational_result, financial_result, composite_score, composite_severity, business_context=None) -> str:
    context_section = f"\nBusiness Context: {business_context.strip()}" if business_context else ""
    scores_section = (
        f"Composite Risk: {composite_severity} ({composite_score:.2f})\n"
        f"  - Market Risk: {market_result.severity} ({market_result.score:.2f}) | Drivers: {', '.join(market_result.contributing_factors[:3]) or 'none'}\n"
        f"  - Operational Risk: {operational_result.severity} ({operational_result.score:.2f}) | Drivers: {', '.join(operational_result.contributing_factors[:3]) or 'none'}\n"
        f"  - Financial Risk: {financial_result.severity} ({financial_result.score:.2f}) | Drivers: {', '.join(financial_result.contributing_factors[:3]) or 'none'}"
    )
    return (
        f"You are a senior risk advisor writing a brief, plain-language risk "
        f"summary for a non-technical executive audience.{context_section}\n\n"
        f"Risk Scores:\n{scores_section}\n\n"
        f"Baseline assessment:\n{baseline_summary}\n\n"
        f"Please rewrite this as a concise, clear narrative (3-5 sentences per "
        f"section). Do not introduce risk factors not listed above. "
        f"Structure: (1) Overall situation, (2) Key concerns, (3) Recommended next steps."
    )
