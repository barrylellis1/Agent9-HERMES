"""
# doc-sync-skip
A9 Situation Awareness Agent

This agent provides automated situation awareness for Finance KPIs,
detecting anomalies, trends, and insights based on principal context.

MVP implementation focuses on the Finance KPIs from the FI Star Schema.
"""
# doc-sync-skip

import os
import re
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple, Protocol, runtime_checkable

# Import data models and enums
from src.agents.models.situation_awareness_models import (
    BusinessProcess, PrincipalRole, TimeFrame, ComparisonType,
    SituationSeverity, KPIDefinition, Situation, KPIValue,
    PrincipalContext, SituationDetectionRequest, SituationDetectionResponse,
    NLQueryRequest, NLQueryResponse, HITLRequest, HITLResponse, HITLDecision,
    OpportunitySignal
)
from src.agents.models.principal_context_models import PrincipalProfileResponse

# Import agent protocol and base classes
from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.shared.a9_agent_base_model import A9AgentBaseModel

# Import registry and database components
from src.registry.factory import RegistryFactory
from src.registry.models.kpi import KPI

# Import other agents
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, agent_registry
from src.registry.providers.accountability_provider import KPIAccountabilityProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.kpi_provider import KPIProvider as KpiProvider
from src.models.kpi_models import KPI, KPIThreshold, KPIComparisonMethod

# LLM Service models for SQL generation
from src.agents.new.a9_llm_service_agent import A9_LLM_SQLGenerationRequest
from src.llm_services.claude_service import ClaudeTaskType, get_claude_model_for_task

# Data quality filtering utility
from src.agents.utils.data_quality_filter import DataQualityFilter

logger = logging.getLogger(__name__)

class A9_Situation_Awareness_Agent:
    """
    Agent9 Situation Awareness Agent
    
    Implements SituationAwarenessProtocol to detect situations based on KPI thresholds, 
    trends, and principal context. Provides automated, personalized situation 
    awareness for Finance KPIs.
    """
    
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'A9_Situation_Awareness_Agent':
        """
        Create a new instance of the Situation Awareness Agent.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            A9_Situation_Awareness_Agent instance
        """
        agent = cls(config)
        await agent.connect()
        return agent
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Situation Awareness Agent.
        
        Args:
            config: Configuration dictionary
        """
        # Store configuration
        if config is None:
            config = {}
            
        # Store the config for later use
        self.config = config 
        # Set up agent properties
        self.name = "A9_Situation_Awareness_Agent"
        self.version = "0.1.0"
        self.data_product_agent = None  # Will be loaded via orchestrator during connect
        self.data_governance_agent = None  # Wired post-bootstrap by runtime._wire_governance_dependencies()
        self.orchestrator_agent = None  # Will be initialized during connect
        self.principal_context_agent = None  # Will be loaded via orchestrator during connect
        self.llm_service_agent = None  # Will be loaded via orchestrator during connect
        
        # Set up internal data structures
        self.business_processes = {}
        self.kpi_registry = {}
        self.principal_profiles = {}  # Initialize principal_profiles to avoid AttributeError
        
        # Initialize logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # KPI registry populated during connect() via _load_kpi_registry() from Supabase
        self.kpi_registry = {}
        # Cache for last generated SQL per KPI to avoid regenerating for UI display
        self._last_sql_cache: Dict[str, Dict[str, str]] = {}

        # Opportunity detection configuration
        self._opportunity_threshold_multiplier: float = float(
            config.get("opportunity_threshold_multiplier", 1.1)
        )
        self._opportunity_recovery_min_delta_pct: float = float(
            config.get("opportunity_recovery_min_delta_pct", 5.0)
        )
    
    async def connect(self, orchestrator=None):
        """Initialize connections to dependent services."""
        try:
            # Use provided orchestrator if available
            if orchestrator:
                self.orchestrator_agent = orchestrator

            # Initialize the orchestrator agent if not already set
            if not hasattr(self, 'orchestrator_agent') or self.orchestrator_agent is None:
                self.orchestrator_agent = await A9_Orchestrator_Agent.create({})
                if self.orchestrator_agent is None:
                    logger.error("Failed to create orchestrator agent")
                    return False
            
            # Get the Data Product Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.data_product_agent = await self.orchestrator_agent.get_agent("A9_Data_Product_Agent")
                except Exception as e:
                    logger.error(f"Error getting Data Product Agent from orchestrator: {e}")
                    self.data_product_agent = None
            if not self.data_product_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("Data Product Agent not available via orchestrator, using direct instantiation")
                from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
                self.data_product_agent = await A9_Data_Product_Agent.create({})
                await self.data_product_agent.connect()
                # Register the directly instantiated agent with the orchestrator
                await self.orchestrator_agent.register_agent("A9_Data_Product_Agent", self.data_product_agent)
            
            # DGA is wired post-bootstrap by runtime._wire_governance_dependencies().
            # No need to acquire it here — self.data_governance_agent will be set after connect().

            # Get the Principal Context Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.principal_context_agent = await self.orchestrator_agent.get_agent("A9_Principal_Context_Agent")
                except Exception as e:
                    logger.error(f"Error getting Principal Context Agent from orchestrator: {e}")
                    self.principal_context_agent = None
            if not self.principal_context_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("Principal Context Agent not available via orchestrator, using direct instantiation")
                try:
                    from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
                    self.principal_context_agent = await A9_Principal_Context_Agent.create({})
                    await self.principal_context_agent.connect()
                    # Register the directly instantiated agent with the orchestrator
                    await self.orchestrator_agent.register_agent("A9_Principal_Context_Agent", self.principal_context_agent)
                except Exception as e:
                    logger.error(f"Failed to instantiate Principal Context Agent directly: {e}")
                    logger.warning("Principal Context Agent functionality will be limited")
            # Load principal profiles from Principal Context Agent (both orchestrator and fallback paths)
            try:
                if hasattr(self.principal_context_agent, 'principal_profiles'):
                    self.principal_profiles = self.principal_context_agent.principal_profiles
                    # Normalize to dict for downstream code/tests expecting a dict-like structure
                    if isinstance(self.principal_profiles, list):
                        normalized = {}
                        for idx, profile in enumerate(self.principal_profiles):
                            if isinstance(profile, dict):
                                key = profile.get('id') or profile.get('role') or profile.get('name') or f"profile_{idx+1}"
                                normalized[key] = profile
                            else:
                                # Convert model-like objects to dict
                                try:
                                    pdata = profile.model_dump() if hasattr(profile, 'model_dump') else (vars(profile) if hasattr(profile, '__dict__') else {})
                                except Exception:
                                    pdata = {}
                                key = pdata.get('id') or pdata.get('role') or pdata.get('name') or f"profile_{idx+1}"
                                normalized[key] = pdata
                        self.principal_profiles = normalized
                    logger.info(f"Loaded {len(self.principal_profiles)} principal profiles from Principal Context Agent")
                else:
                    # Fallback to empty dictionary
                    logger.warning("Principal Context Agent doesn't have principal_profiles attribute")
                    self.principal_profiles = {}
            except Exception as e:
                logger.error(f"Error loading principal profiles: {e}")
                self.principal_profiles = {}
            
            # Get the LLM Service Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.llm_service_agent = await self.orchestrator_agent.get_agent("A9_LLM_Service_Agent")
                except Exception as e:
                    logger.error(f"Error getting LLM Service Agent from orchestrator: {e}")
                    self.llm_service_agent = None
            if not self.llm_service_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("LLM Service Agent not available via orchestrator, using direct instantiation")
                try:
                    from src.agents.new.a9_llm_service_agent import A9_LLM_Service_Agent
                    self.llm_service_agent = await A9_LLM_Service_Agent.create({})
                    # Register the directly instantiated agent with the orchestrator
                    await self.orchestrator_agent.register_agent("A9_LLM_Service_Agent", self.llm_service_agent)
                except Exception as e:
                    logger.error(f"Failed to instantiate LLM Service Agent directly: {e}")
                    logger.warning("LLM-based SQL generation will be limited")
            
            # Load KPIs from registry
            await self._load_kpi_registry()
            
            
            logger.info("Connected to dependent services")
            return True
        except Exception as e:
            logger.error(f"Error connecting to services: {e}")
            return False
    
    async def _load_kpi_registry(self):
        """
        Load KPIs from the Supabase-backed registry asynchronously.
        No YAML fallbacks — if the provider returns no data, log an error and return empty.
        """
        try:
            # Prefer the shared, already-initialized registry factory injected via config.
            registry_factory = self.config.get("registry_factory")
            if registry_factory is None:
                from src.registry.factory import RegistryFactory
                registry_factory = RegistryFactory()
                try:
                    if not registry_factory.is_initialized:
                        await registry_factory.initialize()
                        logger.info("Registry factory initialized successfully")
                    else:
                        logger.info("Registry factory already initialized")
                except Exception as e:
                    logger.warning(f"Error initializing registry factory: {str(e)}")

            kpi_provider = registry_factory.get_kpi_provider()
            if kpi_provider is None:
                kpi_provider = registry_factory.get_provider("kpi")

            if not kpi_provider:
                logger.error("KPI provider not available — check Supabase bootstrap")
                return

            kpis = kpi_provider.get_all() or []
            if not kpis:
                try:
                    await kpi_provider.load()
                    kpis = kpi_provider.get_all() or []
                except Exception as e:
                    logger.warning(f"KPI provider load attempt failed: {e}")

            if not kpis:
                logger.error("No KPIs found in Supabase registry — verify seed data")
                return

            target_domains = self.config.get("target_domains", ["Finance"])
            logger.info(f"Filtering KPIs for domains: {target_domains}")
            self.kpi_registry = {}
            templates_skipped = 0
            for kpi in kpis:
                # Phase 12A guard: never evaluate template KPIs.
                # Template rows are research artifacts pending data connection — they have
                # no data_product_id mapping and would either error or return zero values.
                kpi_status = getattr(kpi, "status", "active") or "active"
                if kpi_status != "active":
                    templates_skipped += 1
                    continue

                if self._kpi_matches_domains(kpi, target_domains):
                    kpi_def = self._convert_to_kpi_definition(kpi)
                    if kpi_def:
                        # Store under plain name (used by NL-query name lookups, last-write wins).
                        self.kpi_registry[kpi_def.name] = kpi_def
                        # Also store under a client-qualified key so multi-tenant scans can
                        # iterate collision-free even when two clients share a KPI name.
                        if kpi_def.client_id:
                            self.kpi_registry[f"{kpi_def.client_id}:{kpi_def.name}"] = kpi_def
            unique_names = len([k for k in self.kpi_registry if ':' not in k])
            logger.info(
                f"Added {unique_names} unique KPI names to registry for domains: {target_domains} "
                f"(skipped {templates_skipped} template KPIs)"
            )
            if not self.kpi_registry:
                logger.warning("No matching KPIs found in registry for target domains")
        except Exception as e:
            logger.error(f"Error loading KPI registry: {str(e)}")
            self.kpi_registry = {}
    
    async def disconnect(self):
        """Disconnect from dependent services."""
        # Data Product Agent doesn't need explicit disconnection as it's managed by the orchestrator
        
        logger.info(f"{self.name} disconnected from dependent services")
    
    # Principal profile management has been moved to the Principal Context Agent
    
    async def detect_situations(
        self, 
        request: SituationDetectionRequest = None, **kwargs
    ) -> SituationDetectionResponse:
        """Handle both direct request object and dictionary with request key"""
        # Store original request_id for response
        original_request_id = str(uuid.uuid4())
        
        # Handle case where request is passed as a keyword argument
        if request is None and 'request' in kwargs:
            request = kwargs['request']
            
        # Convert dict to SituationDetectionRequest if needed
        if isinstance(request, dict):
            # Save the request_id if present
            if 'request_id' in request:
                original_request_id = request.get('request_id')
                
            # Ensure request has all required fields
            if 'request_id' not in request:
                request['request_id'] = original_request_id
            if 'timestamp' not in request:
                request['timestamp'] = datetime.now()
            if 'principal_context' not in request:
                self.logger.error("Missing principal_context in request")
                return SituationDetectionResponse(
                    request_id=original_request_id,
                    status="error",
                    message="Missing principal_context in request",
                    situations=[]
                )
            if 'business_processes' not in request:
                request['business_processes'] = []
                
            try:
                request = SituationDetectionRequest(**request)
            except Exception as e:
                self.logger.error(f"Error converting request dict to SituationDetectionRequest: {str(e)}")
                return SituationDetectionResponse(
                    request_id=original_request_id,
                    status="error",
                    message=f"Invalid request format: {str(e)}",
                    situations=[]
                )
        """
        Detect situations across KPIs based on principal context and business processes.
        
        Args:
            request: SituationDetectionRequest containing principal context and filters
            
        Returns:
            SituationDetectionResponse with detected situations
        """
        try:
            # Ensure we have a valid request_id for the response
            request_id = getattr(request, 'request_id', original_request_id)

            self.logger.info(f"Detecting situations for {request.principal_context.role}")

            # Infra A4-a: refresh KPI registry from Supabase per request so new
            # clients / new KPIs become visible without a service restart.
            await self._load_kpi_registry()

            # Get relevant KPIs based on principal context and business processes.
            # Prefer client_id from the request body; fall back to principal_context.client_id.
            client_id = (
                getattr(request, "client_id", None)
                or getattr(request.principal_context, "client_id", None)
            )

            # Load accountability assignments so the scan is restricted to KPIs
            # this principal owns. Falls back to all KPIs when no assignments exist.
            accountable_kpi_ids: Optional[Set[str]] = None
            _principal_id = getattr(request.principal_context, "principal_id", None)
            if client_id and _principal_id:
                try:
                    _assignments = await KPIAccountabilityProvider().get_for_principal(
                        client_id, _principal_id
                    )
                    if _assignments:
                        accountable_kpi_ids = {a.kpi_id for a in _assignments}
                        self.logger.info(
                            "SA: accountability filter — restricting to %d KPIs for principal %s",
                            len(accountable_kpi_ids), _principal_id,
                        )
                except Exception as _exc:
                    self.logger.warning(
                        "SA: accountability lookup failed for %s — scanning all KPIs: %s",
                        _principal_id, _exc,
                    )

            relevant_kpis = self._get_relevant_kpis(
                request.principal_context,
                request.business_processes,
                client_id=client_id,
                accountable_kpi_ids=accountable_kpi_ids,
            )

            if not relevant_kpis:
                self.logger.warning("No relevant KPIs found for principal context and business processes")
                return SituationDetectionResponse(
                    request_id=request_id,
                    status="success",
                    message="No relevant KPIs found for principal context and business processes",
                    situations=[]
                )
            
            self.logger.info(f"Found {len(relevant_kpis)} relevant KPIs for detection")
            
            # For bullet tracer MVP, we'll process a limited set of KPIs
            # In production, we would process all relevant KPIs
            situations = []
            kpi_values = []
            
            # Process each relevant KPI to fetch actual values from database (no cap)
            opportunities: List[OpportunitySignal] = []
            for kpi_name, kpi_definition in relevant_kpis.items():
                try:
                    # Get actual KPI value from database using Data Product Agent
                    kpi_value = await self._get_kpi_value(
                        kpi_definition,
                        request.timeframe,
                        request.comparison_type,
                        request.filters,
                        request.principal_context
                    )

                    if kpi_value:
                        kpi_values.append(kpi_value)
                        self.logger.info(f"Retrieved KPI value: {kpi_name} = {kpi_value.value}")

                        # Detect problems based on thresholds, trends, etc.
                        detected_situations = self._detect_kpi_situations(
                            kpi_definition,
                            kpi_value,
                            request.principal_context
                        )
                        self.logger.info(f"Detected {len(detected_situations)} situations for {kpi_name}")

                        # ── 11I-A: tag existing threshold situations ──────────────────────
                        for s in detected_situations:
                            if s.alert_type is None:
                                s.alert_type = "threshold_breach"

                        # ── 11I-A Pattern 4: covenant/regulatory → always critical ────────
                        _kpi_type = getattr(kpi_definition, 'kpi_type', 'operational')
                        if _kpi_type in ('covenant', 'regulatory'):
                            for s in detected_situations:
                                s.severity = SituationSeverity.CRITICAL
                                s.alert_type = _kpi_type  # 'covenant' or 'regulatory'

                        # ── 11I-A Pattern 1: plan variance ────────────────────────────────
                        _budget_val = None  # hoisted for reuse by projected_breach (budget-derived floor)
                        _plan_version = getattr(kpi_definition, 'plan_version_value', None)
                        if _plan_version:
                            try:
                                plan_val = await self._fetch_plan_value(
                                    kpi_definition, request.timeframe, request.filters, request.principal_context
                                )
                                _budget_val = plan_val
                                if plan_val is not None and abs(plan_val) > 0:
                                    variance_pct = (kpi_value.value - plan_val) / abs(plan_val)
                                    # variance_pct < 0 always means actual < plan (numerically).
                                    # For revenue KPIs: actual < plan is bad.
                                    # For cost KPIs stored as negative values: actual < plan numerically
                                    # means higher absolute costs (more negative) — also bad.
                                    # inverse_logic is NOT applied here; the sign already encodes direction.
                                    bad_direction = variance_pct < 0

                                    # Read per-KPI plan_variance tolerance bands from registry thresholds.
                                    # KPIThreshold entries with comparison_type='plan_variance' store the
                                    # severity cutoffs as percentage magnitudes: green=min, yellow=medium, red=critical.
                                    # Fall back to hardcoded 2%/8%/15% bands if not configured.
                                    _pv_meta = (getattr(kpi_definition, 'metadata', None) or {}).get('variance_thresholds', {})
                                    _pv_bands = _pv_meta.get('plan_variance', {})
                                    _pv_min = abs(float(_pv_bands.get('green', 2.0))) / 100.0  # MEDIUM trigger
                                    _pv_high = abs(float(_pv_bands.get('yellow', 8.0))) / 100.0  # HIGH trigger
                                    _pv_crit = abs(float(_pv_bands.get('red', 15.0))) / 100.0  # CRITICAL trigger

                                    if abs(variance_pct) >= _pv_min:
                                        severity = (
                                            SituationSeverity.CRITICAL if abs(variance_pct) >= _pv_crit else (
                                                SituationSeverity.HIGH if abs(variance_pct) >= _pv_high
                                                else SituationSeverity.MEDIUM
                                            )
                                        )
                                        # Wording must reflect the KPI's polarity. For a cost KPI
                                        # (inverse / negative-stored), bad_direction means spending is
                                        # OVER budget → "above plan"; an opportunity means UNDER budget →
                                        # "below plan". For revenue/profit KPIs the mapping is reversed.
                                        _is_cost = bool(getattr(kpi_value, 'inverse_logic', False))
                                        if _is_cost:
                                            direction_word = "above" if bad_direction else "below"
                                        else:
                                            direction_word = "below" if bad_direction else "ahead of"
                                        plan_sit = Situation(
                                            situation_id=f"plan_{getattr(kpi_definition, 'id', None) or kpi_name}_{int(abs(variance_pct)*100)}",
                                            kpi_name=kpi_name,
                                            kpi_id=getattr(kpi_definition, 'id', None),
                                            kpi_value=kpi_value,
                                            severity=severity,
                                            card_type="problem" if bad_direction else "opportunity",
                                            direction='down' if bad_direction else 'up',
                                            alert_type="plan_variance",
                                            plan_value=plan_val,
                                            description=f"{kpi_name} is {abs(variance_pct)*100:.1f}% {direction_word} plan",
                                            business_impact=(
                                                f"{kpi_name} is tracking {abs(variance_pct)*100:.1f}% "
                                                f"{direction_word} the {_plan_version} baseline."
                                            ),
                                            hitl_required=bad_direction and severity == SituationSeverity.CRITICAL,
                                        )
                                        detected_situations.append(plan_sit)
                            except Exception as _pv_err:
                                self.logger.warning(f"Plan variance detection failed for {kpi_name}: {_pv_err}")

                        # ── 11I-A Patterns 2 & 3: projection and acceleration ─────────────
                        # Threshold-presence gating (Option A): each pattern runs ONLY if the
                        # KPI carries a registry threshold row for that comparison_type.
                        #   projected_breach → variance_thresholds['projected_breach'] (percent-of-budget tolerance)
                        #   acceleration     → variance_thresholds['acceleration']     (volatility-normalised sensitivity ×)
                        _monthly = getattr(kpi_value, 'monthly_values', None) or []
                        _inverse = getattr(kpi_value, 'inverse_logic', False)
                        _thresholds_meta = (getattr(kpi_definition, 'metadata', None) or {}).get('variance_thresholds', {})
                        _pb_cfg = _thresholds_meta.get('projected_breach')
                        _accel_cfg = _thresholds_meta.get('acceleration')

                        # Pattern 2: projected breach (suppress if actual breach already exists).
                        # Budget-anchored (dominant FP&A practice): the projection floor is derived
                        # from the plan/budget run-rate, not a static dollar level. _pb_cfg['red'] is a
                        # percent tolerance (magnitude) against the monthly budget run-rate.
                        #   monthly_budget = budget / months-in-timeframe
                        #   floor          = monthly_budget − |monthly_budget| × (tol%/100)
                        # Breach fires when the projected monthly trend falls below `floor`. This holds for
                        # BOTH positive-stored KPIs (revenue below budget) and negative-stored costs (more
                        # negative = over budget) — the sign is already encoded, so inverse_logic is not applied
                        # (same reasoning as the plan-variance block above).
                        _has_threshold_breach = any(s.alert_type == "threshold_breach" for s in detected_situations)
                        if (
                            not _has_threshold_breach and _monthly and isinstance(_pb_cfg, dict)
                            and _budget_val is not None and abs(_budget_val) > 0
                            and _pb_cfg.get('red') is not None
                        ):
                            try:
                                # Additive/flow KPIs ($ revenue, cost, income) accumulate across the
                                # timeframe → convert the aggregate budget to a monthly run-rate.
                                # Rate/ratio KPIs (%, e.g. margin, ROCE) do NOT accumulate → the budget
                                # value is already the monthly-comparable level; do not divide.
                                _unit = getattr(kpi_definition, 'unit', '') or ''
                                _is_ratio = ('%' in _unit) or ('ratio' in _unit.lower())
                                if _is_ratio:
                                    _monthly_budget = _budget_val
                                else:
                                    _n_months = self._timeframe_month_count(request.timeframe)
                                    _monthly_budget = _budget_val / max(1, _n_months)
                                _pb_tol = abs(float(_pb_cfg['red'])) / 100.0
                                _pb_floor = _monthly_budget - abs(_monthly_budget) * _pb_tol
                                proj = self._project_trend(_monthly, {'red': _pb_floor}, inverse_logic=False)
                                if proj:
                                    pb_sit = Situation(
                                        situation_id=f"proj_{getattr(kpi_definition, 'id', None) or kpi_name}_{proj['periods_until_breach']}",
                                        kpi_name=kpi_name,
                                        kpi_id=getattr(kpi_definition, 'id', None),
                                        kpi_value=kpi_value,
                                        severity=SituationSeverity.HIGH,
                                        card_type="problem",
                                        direction='down',
                                        alert_type="projected_breach",
                                        plan_value=_budget_val,
                                        projected_breach_at_period=proj['projected_breach_at_period'],
                                        projection_confidence=proj['projection_confidence'],
                                        periods_until_breach=proj['periods_until_breach'],
                                        description=f"{kpi_name} on trajectory to breach the {_plan_version} baseline in {proj['periods_until_breach']} period(s)",
                                        business_impact=(
                                            f"At current run-rate ({proj['slope']:+.2f}/period), "
                                            f"{kpi_name} is projected to fall more than {abs(float(_pb_cfg['red'])):.0f}% "
                                            f"below the {_plan_version} baseline within {proj['periods_until_breach']} period(s). "
                                            f"Trend confidence: {proj['projection_confidence']:.0%}."
                                        ),
                                        hitl_required=proj['periods_until_breach'] <= 2,
                                    )
                                    detected_situations.append(pb_sit)
                            except Exception as _proj_err:
                                self.logger.warning(f"Projection detection failed for {kpi_name}: {_proj_err}")

                        # Pattern 3: acceleration — gated on presence of an 'acceleration' threshold row.
                        # yellow = fire floor (× rolling velocity std to trigger); red = HIGH-severity cutoff.
                        if _monthly and isinstance(_accel_cfg, dict):
                            try:
                                _fire_mult = float(_accel_cfg.get('yellow') if _accel_cfg.get('yellow') is not None else 2.0)
                                _high_mult = float(_accel_cfg.get('red') if _accel_cfg.get('red') is not None else 3.0)
                                accel_signal = self._compute_acceleration(_monthly, fire_multiplier=_fire_mult)
                                if accel_signal is not None and accel_signal > 0:
                                    accel_sit = Situation(
                                        situation_id=f"accel_{getattr(kpi_definition, 'id', None) or kpi_name}_{int(accel_signal*10)}",
                                        kpi_name=kpi_name,
                                        kpi_id=getattr(kpi_definition, 'id', None),
                                        kpi_value=kpi_value,
                                        severity=SituationSeverity.HIGH if accel_signal >= _high_mult else SituationSeverity.MEDIUM,
                                        card_type="problem",
                                        direction='down',
                                        alert_type="acceleration",
                                        acceleration_signal=accel_signal,
                                        description=f"{kpi_name} deterioration is accelerating ({accel_signal:.1f}× baseline volatility)",
                                        business_impact=(
                                            f"The rate of change in {kpi_name} is itself increasing — "
                                            f"the period-over-period decline is accelerating at {accel_signal:.1f}× the historical pace."
                                        ),
                                        hitl_required=False,
                                    )
                                    detected_situations.append(accel_sit)
                            except Exception as _acc_err:
                                self.logger.warning(f"Acceleration detection failed for {kpi_name}: {_acc_err}")

                        # Commit detected situations before enrichment so detection
                        # failures in LLM calls can never silently discard situations.
                        situations.extend(detected_situations)
                        # Enrich with LLM-generated observations and trend note
                        for sit in detected_situations:
                            try:
                                sit.key_observations = await self._generate_key_observations(kpi_definition, kpi_value, sit)
                                sit.trend_note = await self._generate_trend_note(kpi_definition, kpi_value, sit)
                            except Exception as _enrich_err:
                                self.logger.warning(f"Enrichment failed for {kpi_name}/{sit.alert_type}: {_enrich_err}")

                        # Detect positive opportunity signals
                        try:
                            detected_opportunities = self._detect_opportunities(
                                kpi_definition,
                                kpi_value,
                            )
                            if detected_opportunities:
                                self.logger.info(
                                    f"Detected {len(detected_opportunities)} opportunity signal(s) for {kpi_name}"
                                )
                            opportunities.extend(detected_opportunities)
                            # Convert high-confidence opportunity signals into clickable Situation cards
                            for signal in detected_opportunities:
                                if signal.confidence >= 0.7:
                                    opp_dedupe_key = f"opp_{signal.kpi_name}_{signal.opportunity_type}"
                                    if not any(s.dedupe_key == opp_dedupe_key for s in situations):
                                        try:
                                            opp_situation = Situation.from_opportunity_signal(signal, kpi_value)
                                            opp_situation.dedupe_key = opp_dedupe_key
                                            situations.append(opp_situation)
                                        except Exception as _opp_conv_err:
                                            self.logger.warning(
                                                f"Could not convert opportunity signal to Situation for {signal.kpi_name}: {_opp_conv_err}"
                                            )
                        except Exception as opp_err:
                            self.logger.warning(
                                f"Error detecting opportunities for KPI {kpi_name}: {opp_err}"
                            )

                except Exception as kpi_error:
                    self.logger.warning(f"Error processing KPI {kpi_name}: {str(kpi_error)}")
                    # Continue with other KPIs

            # ── 11I-B: compound cross-KPI alert detection ─────────────────
            situations = await self._detect_compound_alerts(situations, client_id)

            # Deduplicate by (kpi_name, alert_type) — keep highest severity per pair
            _seen_kpi: dict = {}
            _severity_order = {s: i for i, s in enumerate(SituationSeverity)}
            for sit in situations:
                _key = (sit.kpi_name, sit.alert_type or "threshold_breach")
                if _key not in _seen_kpi:
                    _seen_kpi[_key] = sit
                else:
                    _existing_rank = _severity_order.get(_seen_kpi[_key].severity, 99)
                    _new_rank = _severity_order.get(sit.severity, 99)
                    if _new_rank < _existing_rank:
                        _seen_kpi[_key] = sit
            situations = list(_seen_kpi.values())

            # ── Consolidate multiple problem alert_types for the same KPI ──────
            # A single KPI can legitimately trigger several 11I-A/11I-B patterns in one
            # scan (e.g. threshold_breach + plan_variance + acceleration). Showing each
            # as its own card duplicates the KPI in the UI and inflates finding counts.
            # Fold all 'problem' situations for a given kpi_name into one card, keyed off
            # the most severe member; every original alert_type is preserved in
            # merged_alert_types and its narrative folded into key_observations (capped
            # so a KPI with many simultaneous patterns doesn't produce an unbounded card).
            situations = self._merge_compound_kpi_situations(situations)

            # Sort situations: primary = severity (critical first), secondary = |percent_change| descending
            situations.sort(key=lambda s: (
                list(SituationSeverity).index(s.severity) if s.severity in SituationSeverity else 99,
                -abs((s.kpi_value.percent_change or 0) if s.kpi_value else 0)
            ))
            
            # Generate summary SQL for debugging/transparency
            sample_sql = ""
            if kpi_values and self.data_product_agent:
                first_kpi_def = relevant_kpis.get(kpi_values[0].kpi_name)
                if first_kpi_def:
                    try:
                        # Use Data Product Agent to generate SQL for the KPI
                        merged_filters = {}
                        try:
                            pc_df = getattr(request.principal_context, 'default_filters', None)
                            if isinstance(pc_df, dict):
                                merged_filters.update(pc_df)
                        except Exception:
                            pass
                        try:
                            if isinstance(request.filters, dict):
                                merged_filters.update(request.filters)
                        except Exception:
                            pass
                        # Debug: log merged filters so we can verify principal defaults are present
                        try:
                            self.logger.info(f"[SA SQL-DEBUG] merged_filters for sample SQL: {merged_filters}")
                        except Exception:
                            pass
                        sql_response = await self.data_product_agent.generate_sql_for_kpi(
                            kpi_definition=first_kpi_def,
                            timeframe=request.timeframe,
                            filters=merged_filters
                        )
                        if sql_response.get('success', False) and sql_response.get('sql'):
                            sample_sql = sql_response['sql']
                    except Exception as e:
                        logger.warning(f"Error generating sample SQL: {e}")
                        sample_sql = ""
            
            return SituationDetectionResponse(
                request_id=request.request_id,
                status="success",
                message=(
                    f"Detected {len(situations)} situations across {len(kpi_values)} KPIs"
                ),
                situations=situations,
                opportunities=[],  # Phase 11C: deprecated — opportunity signals are now Situation cards
                sql_query=sample_sql,
                kpi_evaluated_count=len(kpi_values),
                kpis_evaluated=[kv.kpi_name for kv in kpi_values],
                kpi_details=kpi_values  # Return full KPIValue objects for debugging
            )
        
        except Exception as e:
            self.logger.error(f"Error detecting situations: {str(e)}")
            # Use the stored request_id in case request object is invalid
            req_id = getattr(request, 'request_id', original_request_id) if hasattr(request, 'request_id') else original_request_id
            return SituationDetectionResponse(
                request_id=req_id,
                status="error",
                message=f"Error detecting situations: {str(e)}",
                situations=[]
            )
    
    async def process_nl_query(
        self,
        request: NLQueryRequest = None, **kwargs
    ) -> NLQueryResponse:
        """Handle both direct request object and dictionary with request key"""
        # Store original request_id for response
        original_request_id = str(uuid.uuid4())
        
        # Handle case where request is passed as a keyword argument
        if request is None and 'request' in kwargs:
            request = kwargs['request']
            
        # Convert dict to NLQueryRequest if needed
        if isinstance(request, dict):
            # Save the request_id if present
            if 'request_id' in request:
                original_request_id = request.get('request_id')
                
            # Ensure request has all required fields
            if 'request_id' not in request:
                request['request_id'] = original_request_id
            if 'timestamp' not in request:
                request['timestamp'] = datetime.now()
            if 'query' not in request:
                self.logger.error("Missing query in request")
                return NLQueryResponse(
                    request_id=original_request_id,
                    status="error",
                    answer="Missing query in request",
                    kpi_values=[],
                    sql_query=""
                )
            if 'principal_context' not in request:
                self.logger.warning("Missing principal_context in request, using default")
                
            try:
                request = NLQueryRequest(**request)
            except Exception as e:
                self.logger.error(f"Error converting request dict to NLQueryRequest: {str(e)}")
                return NLQueryResponse(
                    request_id=original_request_id,
                    status="error",
                    answer=f"Invalid request format: {str(e)}",
                    kpi_values=[],
                    sql_query=""
                )
        """
        Process a natural language query about KPIs or situations.
        
        Args:
            request: NLQueryRequest containing the query and principal context
            
        Returns:
            NLQueryResponse containing the answer, KPI values, and SQL query
        """
        if self.data_governance_agent is None:
            raise RuntimeError(
                "Data Governance Agent not initialized. "
                "Ensure _wire_governance_dependencies() was called during startup."
            )

        try:
            logger.info(f"Processing NL query: {request.query}")

            # Infra A4-a: refresh KPI registry from Supabase per request so new
            # clients / new KPIs become visible without a service restart.
            await self._load_kpi_registry()

            # Extract business terms from the query using Data Governance Agent
            # This is a simple extraction for MVP - in production would use NLP Agent
            query_terms = [term.strip() for term in request.query.split() if len(term.strip()) > 3]
            
            # Translate business terms to technical attribute names via DGA (mandatory)
            from src.agents.models.data_governance_models import BusinessTermTranslationRequest

            translation_result = await self.data_governance_agent.translate_business_terms(
                BusinessTermTranslationRequest(
                    business_terms=query_terms,
                    system="duckdb",
                    context={
                        "principal_context": request.principal_context.model_dump() if request.principal_context else {},
                        "business_processes": getattr(request, 'business_processes', None) or (
                            request.principal_context.business_processes if request.principal_context else []
                        )
                    }
                )
            )
            # Persist for later checks in this method
            self.translation_result = translation_result

            if translation_result.human_action_required:
                logger.warning(f"Unmapped business terms: {translation_result.unmapped_terms}")
                if not translation_result.resolved_terms:
                    logger.warning("No business terms could be mapped, proceeding with direct KPI matching")
            
            # Extract KPI mentions from the query
            query_lower = request.query.lower()
            kpi_values = []
            
            # Map KPIs to data products via DGA (mandatory)
            from src.agents.models.data_governance_models import KPIDataProductMappingRequest

            mapped_kpis = []
            potential_kpi_names = []

            if hasattr(self, 'translation_result') and getattr(self.translation_result, 'resolved_terms', None):
                potential_kpi_names.extend(list(self.translation_result.resolved_terms.values()))

            for kpi_name in self.kpi_registry.keys():
                if kpi_name.lower() in query_lower:
                    potential_kpi_names.append(kpi_name)

            potential_kpi_names = list(set(potential_kpi_names))

            if potential_kpi_names:
                mapping_response = await self.data_governance_agent.map_kpis_to_data_products(
                    KPIDataProductMappingRequest(
                        kpi_names=potential_kpi_names,
                        context={
                            "principal_id": request.principal_context.principal_id if request.principal_context else "",
                            "business_processes": getattr(request, 'business_processes', None) or (
                                request.principal_context.business_processes if request.principal_context else []
                            )
                        }
                    )
                )
                for mapping in mapping_response.mappings:
                    mapped_kpis.append(mapping.kpi_name)
                logger.info(f"Data Governance Agent mapped {len(mapping_response.mappings)} KPIs")
            
            # Process KPIs - first from Data Governance Agent mappings, then fall back to direct matching
            processed_kpis = set()
            
            # First process mapped KPIs from Data Governance Agent
            for kpi_name in mapped_kpis:
                if kpi_name not in processed_kpis:
                    try:
                        # Check if we have this KPI in our registry
                        if kpi_name in self.kpi_registry:
                            kpi_def = self.kpi_registry[kpi_name]
                        else:
                            # Try to get KPI definition from Data Governance Agent
                            try:
                                # Get the mapping for this KPI
                                for mapping in mapping_response.mappings:
                                    if mapping.kpi_name == kpi_name:
                                        # Create a temporary KPI definition from the mapping
                                        kpi_def = KPIDefinition(
                                            name=mapping.kpi_name,
                                            description=mapping.metadata.get("description", "") if mapping.metadata else "",
                                            data_product_id=mapping.data_product_id,
                                            calculation="",  # Will be generated by Data Product Agent
                                            view_name=mapping.technical_name,
                                            thresholds=mapping.metadata.get("thresholds", {}) if mapping.metadata else {},
                                            dimensions=mapping.metadata.get("dimensions", []) if mapping.metadata else [],
                                            business_processes=mapping.metadata.get("business_processes", []) if mapping.metadata else [],
                                            positive_trend_is_good=mapping.metadata.get("positive_trend_is_good", True) if mapping.metadata else True
                                        )
                                        break
                            except Exception as e:
                                logger.warning(f"Error creating KPI definition from mapping: {e}")
                                kpi_def = None
                                
                        # Get KPI value if we have a definition
                        if kpi_def:
                            kpi_value = await self._get_kpi_value(
                                kpi_def,
                                request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,  # Default timeframe
                                request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,  # Default comparison
                                request.filters if request.filters else {},
                                request.principal_context
                            )
                            if kpi_value:
                                kpi_values.append(kpi_value)
                                processed_kpis.add(kpi_name)
                    except Exception as kpi_error:
                        logger.warning(f"Error retrieving KPI {kpi_name}: {str(kpi_error)}")
                        # Continue with other KPIs
                        
            # Then fall back to direct KPI name matching in the query for any KPIs not already processed
            for kpi_name in self.kpi_registry.keys():
                if kpi_name.lower() in query_lower and kpi_name not in processed_kpis:
                    try:
                        kpi_def = self.kpi_registry[kpi_name]
                        kpi_value = await self._get_kpi_value(
                            kpi_def,
                            request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,  # Default timeframe
                            request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,  # Default comparison
                            request.filters if request.filters else {},
                            request.principal_context
                        )
                        if kpi_value:
                            kpi_values.append(kpi_value)
                            processed_kpis.add(kpi_name)
                    except Exception as kpi_error:
                        logger.warning(f"Error retrieving KPI {kpi_name}: {str(kpi_error)}")
                        # Continue with other KPIs
            
            # For bullet tracer MVP, if no KPIs are found in query, get principal's top KPI
            if not kpi_values and request.principal_context:
                try:
                    # Get KPIs relevant to principal (scoped by client_id)
                    _nl_client_id = getattr(request.principal_context, 'client_id', None) if hasattr(request.principal_context, 'client_id') else None
                    relevant_kpis = self._get_relevant_kpis(
                        request.principal_context,
                        None,  # No business process filter for NL queries
                        client_id=_nl_client_id,
                    )
                    
                    # Get first KPI
                    if relevant_kpis:
                        first_kpi_name = next(iter(relevant_kpis.keys()))
                        # Use KPI definition (not name) when fetching KPI value
                        first_kpi_def = relevant_kpis[first_kpi_name]
                        kpi_value = await self._get_kpi_value(
                            first_kpi_def,
                            request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,
                            request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,
                            request.filters if request.filters else {}
                        )
                        if kpi_value:
                            kpi_values.append(kpi_value)
                except Exception as e:
                    logger.warning(f"Error getting default KPI: {str(e)}")
            
            # Generate SQL for the query using Data Product Agent
            sql_query = await self._generate_sql_for_query(request.query, kpi_values)
            # Fallback: if NL->SQL did not return SQL but we have a KPI, generate deterministic SQL
            if (not sql_query) and kpi_values and self.data_product_agent:
                try:
                    first_kpi_name = getattr(kpi_values[0], 'kpi_name', None)
                    kpi_def = None
                    # Try to resolve KPI definition from registry
                    if first_kpi_name and isinstance(self.kpi_registry, dict):
                        kpi_def = self.kpi_registry.get(first_kpi_name)
                    # Merge principal default filters with explicit request filters
                    merged_filters = {}
                    try:
                        if getattr(request.principal_context, 'default_filters', None):
                            df = request.principal_context.default_filters
                            if isinstance(df, dict):
                                merged_filters.update(df)
                    except Exception:
                        pass
                    try:
                        if isinstance(request.filters, dict):
                            merged_filters.update(request.filters)
                    except Exception:
                        pass

                    # Minimal NL intent extraction for Top/Bottom N breakdowns (e.g., "top 5 profit centers")
                    # Prefer simple, robust patterns for MVP
                    def _parse_topn_and_dims(q: str):
                        try:
                            import re as _re
                            ql = (q or "").strip().lower()
                            limit_type = None
                            limit_n = None
                            # Numeric N (e.g., "top 5", "bottom 10")
                            m_top = _re.search(r"\btop\s+(\d+)\b", ql)
                            m_bot = _re.search(r"\bbottom\s+(\d+)\b", ql)
                            if m_top:
                                limit_type = 'top'
                                limit_n = int(m_top.group(1))
                            elif m_bot:
                                limit_type = 'bottom'
                                limit_n = int(m_bot.group(1))
                            else:
                                # Spelled-out small numbers (e.g., "top five") and default when just 'top'/'bottom'
                                words_map = {
                                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'twelve': 12
                                }
                                m_word = _re.search(r"\b(top|bottom)\s+(one|two|three|four|five|six|seven|eight|nine|ten|twelve)\b", ql)
                                if m_word:
                                    limit_type = m_word.group(1)
                                    limit_n = words_map.get(m_word.group(2))
                                else:
                                    if _re.search(r"\btop\b", ql):
                                        limit_type, limit_n = 'top', 10
                                    elif _re.search(r"\bbottom\b", ql):
                                        limit_type, limit_n = 'bottom', 10
                            # Dimension detection (extendable): map common phrases to canonical business terms
                            # Prefer more specific patterns before generic ones (e.g., Product Type before Product)
                            dim_map = [
                                (r"\bproduct\s*type(s)?\b|\bproduct\s*category(ies)?\b|\bcategory(ies)?\b", "Product Type"),
                                (r"\bproduct(s)?\b", "Product"),
                                (r"\bprofit\s*center(s)?\b", "Profit Center"),
                                (r"\bcustomer\s*type(s)?\b", "Customer Type"),
                                (r"\bregion(s)?\b", "Region"),
                                (r"\bcountr(y|ies)\b", "Country"),
                                (r"\bchannel(s)?\b", "Channel"),
                            ]
                            dims = []
                            for pat, canon in dim_map:
                                if _re.search(pat, ql):
                                    dims.append(canon)
                            return limit_type, limit_n, dims
                        except Exception:
                            return None, None, []

                    # If the question asks for a Top/Bottom breakdown on a known dimension, request grouped SQL
                    breakdown = False
                    override_group_by = None
                    topn_spec = None
                    lt, ln, dims = _parse_topn_and_dims(request.query)
                    # Keep SA neutral: do not reorder detected dimensions post hoc; dim_map order already prefers specificity
                    # Detect growth intent (fastest growing vs previous period)
                    try:
                        import re as _re
                        ql = (request.query or "").strip().lower()
                        growth_metric = bool(_re.search(r"\b(fastest\s+growing|growth|increase|vs\s+previous|versus\s+previous|delta|variance)\b", ql))
                    except Exception:
                        growth_metric = False

                    if dims:
                        breakdown = True
                        override_group_by = dims[:1]  # Single-dimension breakdown for MVP
                        # Build TopN spec; if growth intent but no N specified, default to 5
                        if not (lt and isinstance(ln, int) and ln > 0) and growth_metric:
                            lt, ln = 'top', 5
                        if lt and isinstance(ln, int) and ln > 0:
                            topn_spec = {"limit_type": lt, "limit_n": ln}
                            if growth_metric:
                                topn_spec["metric"] = "delta_prev"

                    if kpi_def:
                        dp_resp_fallback = await self.data_product_agent.generate_sql_for_kpi(
                            kpi_definition=kpi_def,
                            timeframe=request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,
                            filters=merged_filters,
                            breakdown=breakdown,
                            override_group_by=override_group_by,
                            topn=topn_spec,
                        )
                        if isinstance(dp_resp_fallback, dict) and dp_resp_fallback.get('success') and dp_resp_fallback.get('sql'):
                            sql_query = dp_resp_fallback['sql']
                            try:
                                logger.info("[SA] Using KPI SQL fallback for NL response display (breakdown=%s, group_by=%s, topn=%s)", breakdown, override_group_by, topn_spec)
                            except Exception:
                                pass
                except Exception as _fallback_err:
                    try:
                        logger.warning(f"KPI SQL fallback failed: {_fallback_err}")
                    except Exception:
                        pass
            
            # Check if we need HITL escalation due to unmapped terms
            human_action_required = False
            human_action_type = None
            human_action_context = None
            
            # If we have unmapped terms from the Data Governance Agent, provide HITL context
            if hasattr(self, 'translation_result') and \
               getattr(self.translation_result, 'human_action_required', False) and not kpi_values:
                human_action_required = True
                human_action_type = "clarification"
                human_action_context = {
                    "unmapped_terms": self.translation_result.unmapped_terms,
                    "message": "I need clarification on these business terms to answer your query."
                }
                answer = "I need additional clarification on some terms in your query."
            else:
                # Generate answer based on KPI values and query
                answer = self._generate_answer_for_query(request.query, kpi_values)
            
            return NLQueryResponse(
                request_id=request.request_id,
                status="success",
                answer=answer,
                kpi_values=kpi_values,
                sql_query=sql_query,
                human_action_required=human_action_required,
                human_action_type=human_action_type,
                human_action_context=human_action_context
            )
            
        except Exception as e:
            logger.error(f"Error processing NL query: {str(e)}")
            # Use the stored request_id in case request object is invalid
            req_id = getattr(request, 'request_id', original_request_id) if hasattr(request, 'request_id') else original_request_id
            return NLQueryResponse(
                request_id=req_id,
                status="error",
                message=f"Error processing query: {str(e)}",
                answer="I'm sorry, I couldn't process your query due to an error.",
                kpi_values=[]
            )
    
    async def process_hitl_feedback(
        self,
        request: HITLRequest
    ) -> HITLResponse:
        """
        Process human-in-the-loop feedback for a situation.
        
        Args:
            request: HITLRequest containing the decision and any modifications
            
        Returns:
            HITLResponse with the updated situation if applicable
        """
        # For MVP, we'll just acknowledge the feedback
        # In production, this would update the situation and potentially trigger actions
        
        return HITLResponse(
            request_id=request.request_id,
            status="success",
            message=f"Processed {request.decision} feedback"
        )
    
    # ──────────────────────────────────────────────────────────────────────────
    # BigQuery date-filter helpers
    # Used when a KPI carries a pre-built SQL with fully-qualified BQ table refs.
    # These bypass the DuckDB/time_dim-centric generate_sql_for_kpi path entirely.
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _bq_get_period_dates(timeframe, is_comparison=False, comparison_type=None):
        """Return (start_date_str, end_date_str) for a timeframe/comparison pair."""
        from datetime import date
        import calendar as _cal
        today = date.today()
        y, m = today.year, today.month

        def quarter_dates(yr, qtr):
            sm = (qtr - 1) * 3 + 1
            em = qtr * 3
            return date(yr, sm, 1), date(yr, em, _cal.monthrange(yr, em)[1])

        # Use .value for Enum members (Python 3.11 changed str(StrEnum) to include class name).
        tf = (getattr(timeframe, 'value', None) or str(timeframe) or "").strip().lower() if timeframe else "last_quarter"

        # Determine current quarter
        cur_q = (m - 1) // 3 + 1

        if tf in ("last_quarter",):
            bq = cur_q - 1 or 4
            by = y if cur_q > 1 else y - 1
            base_start, base_end = quarter_dates(by, bq)
        elif tf in ("current_quarter", "quarter_to_date"):
            base_start, base_end = quarter_dates(y, cur_q)
            base_end = min(base_end, today)
        elif tf in ("last_month",):
            pm = m - 1 or 12
            py = y if m > 1 else y - 1
            base_start = date(py, pm, 1)
            base_end = date(py, pm, _cal.monthrange(py, pm)[1])
        elif tf in ("current_month", "month_to_date"):
            base_start = date(y, m, 1)
            base_end = min(date(y, m, _cal.monthrange(y, m)[1]), today)
        elif tf in ("last_year",):
            base_start, base_end = date(y - 1, 1, 1), date(y - 1, 12, 31)
        elif tf in ("year_to_date", "current_year"):
            base_start, base_end = date(y, 1, 1), today
        else:
            # Default to last quarter
            bq = cur_q - 1 or 4
            by = y if cur_q > 1 else y - 1
            base_start, base_end = quarter_dates(by, bq)

        if not is_comparison:
            return str(base_start), str(base_end)

        ct = str(comparison_type).strip().lower() if comparison_type else "year_over_year"
        if "year" in ct:
            return str(date(base_start.year - 1, base_start.month, base_start.day)), \
                   str(date(base_end.year - 1, base_end.month, base_end.day))
        elif "quarter" in ct:
            # Previous quarter
            pq = ((base_start.month - 1) // 3)  # 0-indexed quarter before current
            py = base_start.year if pq > 0 else base_start.year - 1
            pq = pq or 4
            cs, ce = quarter_dates(py, pq)
            return str(cs), str(ce)
        else:  # month_over_month or default
            pm = base_start.month - 1 or 12
            py = base_start.year if base_start.month > 1 else base_start.year - 1
            cs = date(py, pm, 1)
            ce = date(py, pm, _cal.monthrange(py, pm)[1])
            return str(cs), str(ce)

    @staticmethod
    def _bq_apply_period(sql, timeframe, is_comparison=False, comparison_type=None, date_col="transaction_date"):
        """Append a BigQuery-compatible date range filter to an existing KPI SQL."""
        import re as _re
        start, end = A9_Situation_Awareness_Agent._bq_get_period_dates(
            timeframe, is_comparison=is_comparison, comparison_type=comparison_type
        )
        cond = f"{date_col} BETWEEN '{start}' AND '{end}'"
        if _re.search(r'\bWHERE\b', sql, _re.IGNORECASE):
            return sql + f" AND {cond}"
        return sql + f" WHERE {cond}"

    def _bq_monthly_series_sql(self, base_sql: str, date_col: str = "transaction_date", num_months: int = 9) -> str:
        """Generate SQL returning the most recent N monthly aggregates for a KPI.

        Approach: no hard-coded date window. Let the data determine which months
        exist by using ORDER BY period DESC LIMIT N, then wrap to return ascending.
        This works regardless of what calendar period the dataset covers.

        Non-date WHERE conditions (version, account_type, etc.) are preserved.
        Any existing date range filter is stripped — the subquery LIMIT handles recency.
        """
        import re as _re

        # Match: SELECT <agg> AS <alias> FROM <table_ref> [rest]
        # table_ref may be backtick-quoted (`project.dataset.view`),
        # double-quoted ("ViewName"), or unquoted (ViewName).
        match = _re.match(
            r'SELECT\s+(.+?)\s+AS\s+\w+\s+FROM\s+'
            r'((?:`[^`]+`|"[^"]+"|\w+)(?:\.(?:`[^`]+`|"[^"]+"|\w+))*)'
            r'(.*)',
            base_sql,
            _re.IGNORECASE | _re.DOTALL,
        )
        if not match:
            self.logger.warning(f"[Monthly] Could not parse base SQL for monthly series: {base_sql[:200]}")
            return ""

        agg_expr = match.group(1).strip()
        table_ref = match.group(2).strip()
        rest = match.group(3).strip()

        # If DPA injected a time_dim JOIN (DuckDB pattern), extract just the WHERE
        # portion and drop the JOIN — BigQuery resolves the view via default_dataset.
        where_match = _re.search(r'\bWHERE\b(.*)', rest, _re.IGNORECASE | _re.DOTALL)
        where_clause = ("WHERE" + where_match.group(1)) if where_match else rest

        # Normalise date_col: strip surrounding double-quotes
        bare_date_col = date_col.strip('"')

        # Strip ALL date range conditions — recency is handled by LIMIT, not a WHERE filter
        if where_clause.upper().startswith("WHERE"):
            existing_conditions = where_clause[5:].strip()
            date_col_pattern = rf'"?{_re.escape(bare_date_col)}"?'
            cleaned = _re.sub(
                rf'(?:\bAND\s+)?{date_col_pattern}\s+'
                rf'(?:BETWEEN\s+[\'"\d\-T]+\s+AND\s+[\'"\d\-T]+|[<>]=?\s*[\'"\d\-T]+)',
                '',
                existing_conditions,
                flags=_re.IGNORECASE,
            ).strip().lstrip(',').strip()
            cleaned = _re.sub(r'^AND\s+', '', cleaned, flags=_re.IGNORECASE).strip()
            non_date_where = f"WHERE {cleaned}" if cleaned else ""
        else:
            non_date_where = ""

        # transaction_date is stored as STRING (YYYY-MM-DD) in BigQuery.
        # LEFT(..., 7) extracts YYYY-MM from any ISO date string.
        # Outer query re-orders to ascending so the chart reads left→right chronologically.
        monthly_sql = (
            f"SELECT period, value FROM ("
            f"SELECT LEFT({bare_date_col}, 7) AS period, "
            f"{agg_expr} AS value "
            f"FROM {table_ref} "
            f"{non_date_where} "
            f"GROUP BY period "
            f"ORDER BY period DESC "
            f"LIMIT {num_months}"
            f") ORDER BY period ASC"
        )
        return monthly_sql

    def _ss_monthly_series_sql(
        self,
        base_sql: str,
        year_col: str = "fiscal_year",
        period_col: str = "fiscal_period",
        num_months: int = 9,
    ) -> str:
        """T-SQL monthly series using fiscal_year + fiscal_period integer columns.

        Uses TOP n subquery so no date-window filter is needed — the most recent
        N periods are returned and then reordered ascending for the sparkline.
        Non-date WHERE conditions (account_type, version, etc.) are preserved.
        Returns period as 'YYYY-PP' (zero-padded, e.g. '2026-03').
        """
        import re as _re

        match = _re.match(
            r'SELECT\s+(.+?)\s+AS\s+\w+\s+FROM\s+'
            r'((?:\[[^\]]+\]|\w+)(?:\.(?:\[[^\]]+\]|\w+))*)'
            r'(.*)',
            base_sql,
            _re.IGNORECASE | _re.DOTALL,
        )
        if not match:
            self.logger.warning(f"[Monthly-SS] Could not parse base SQL: {base_sql[:200]}")
            return ""

        agg_expr = match.group(1).strip()
        table_ref = match.group(2).strip()
        rest = match.group(3).strip()

        where_match = _re.search(r'\bWHERE\b(.*)', rest, _re.IGNORECASE | _re.DOTALL)
        non_date_where = ("WHERE " + where_match.group(1).strip()) if where_match else ""

        y = f"[{year_col.strip('[]')}]"
        p = f"[{period_col.strip('[]')}]"
        period_expr = f"CAST({y} AS VARCHAR(4)) + '-' + RIGHT('0' + CAST({p} AS VARCHAR(2)), 2)"

        return (
            f"SELECT period, value FROM ("
            f"SELECT TOP {num_months} "
            f"{period_expr} AS period, "
            f"{agg_expr} AS value "
            f"FROM {table_ref} "
            f"{non_date_where} "
            f"GROUP BY {y}, {p} "
            f"ORDER BY {y} DESC, {p} DESC"
            f") t ORDER BY period ASC"
        )

    def _sf_monthly_series_sql(
        self,
        base_sql: str,
        year_col: str = "fiscal_year",
        period_col: str = "fiscal_period",
        num_months: int = 9,
    ) -> str:
        """Snowflake monthly series using fiscal_year + fiscal_period integer columns.

        Uses LIMIT n subquery (Snowflake syntax). String concatenation via ||.
        Returns period as 'YYYY-PP' (zero-padded, e.g. '2026-03').
        """
        import re as _re

        match = _re.match(
            r'SELECT\s+(.+?)\s+AS\s+\w+\s+FROM\s+'
            r'((?:`[^`]+`|"[^"]+"|\w+)(?:\.(?:`[^`]+`|"[^"]+"|\w+))*)'
            r'(.*)',
            base_sql,
            _re.IGNORECASE | _re.DOTALL,
        )
        if not match:
            self.logger.warning(f"[Monthly-SF] Could not parse base SQL: {base_sql[:200]}")
            return ""

        agg_expr = match.group(1).strip()
        table_ref = match.group(2).strip()
        rest = match.group(3).strip()

        where_match = _re.search(r'\bWHERE\b(.*)', rest, _re.IGNORECASE | _re.DOTALL)
        non_date_where = ("WHERE " + where_match.group(1).strip()) if where_match else ""

        period_expr = (
            f"CAST({year_col} AS VARCHAR) || '-' || "
            f"LPAD(CAST({period_col} AS VARCHAR), 2, '0')"
        )

        return (
            f"SELECT period, value FROM ("
            f"SELECT {period_expr} AS period, "
            f"{agg_expr} AS value "
            f"FROM {table_ref} "
            f"{non_date_where} "
            f"GROUP BY {year_col}, {period_col} "
            f"ORDER BY {year_col} DESC, {period_col} DESC "
            f"LIMIT {num_months}"
            f") AS t ORDER BY period ASC"
        )

    # ──────────────────────────────────────────────────────────────────────────

    async def _resolve_time_spec_sa(self, data_product_id: Optional[str]) -> dict:
        """Return the TimeDimensionSpec dict for a data product (SA-side lookup).

        Always does a fresh load from Supabase so the in-memory provider cache
        cannot return stale data (e.g. after a seed run without a server restart).
        Falls back to a generic date-column spec on any error.
        """
        _fallback = {"type": "date", "column": "transaction_date"}
        if not data_product_id:
            return _fallback
        try:
            registry_factory = self.config.get("registry_factory")
            if not registry_factory:
                from src.registry.factory import RegistryFactory
                registry_factory = RegistryFactory()
            dp_provider = registry_factory.get_provider("data_product")
            if not dp_provider:
                return _fallback
            # Force a fresh Supabase fetch so we never read a stale startup cache
            try:
                await dp_provider.load()
            except Exception as _le:
                self.logger.debug(f"[SA] time_spec provider reload failed (using cache): {_le}")
            dp = dp_provider.get(data_product_id)
            if not dp:
                return _fallback
            time_dims = getattr(dp, "time_dimensions", None)
            if not time_dims:
                return _fallback
            # time_dimensions may be a list of dicts or objects
            first = time_dims[0] if isinstance(time_dims, list) else time_dims
            if hasattr(first, "model_dump"):
                return first.model_dump()
            if isinstance(first, dict):
                return first
            return _fallback
        except Exception as e:
            self.logger.debug(f"[SA] Could not resolve time spec for {data_product_id}: {e}")
            return _fallback

    # ──────────────────────────────────────────────────────────────────────────

    def _resolve_source_system(self, data_product_id: Optional[str]) -> Optional[str]:
        """
        Look up source_system for a data product from the registry.

        Tier 1 routing: direct registry lookup via data_product_id.
        Used to route SQL execution to the correct backend (BigQuery, Snowflake, SQL Server, DuckDB).

        Args:
            data_product_id: The data product ID to look up

        Returns:
            The source_system (bigquery, snowflake, sqlserver, duckdb) or None if not found
        """
        if not data_product_id:
            return None
        try:
            registry_factory = self.config.get("registry_factory")
            if not registry_factory:
                from src.registry.factory import RegistryFactory
                registry_factory = RegistryFactory()
            dp_provider = registry_factory.get_provider("data_product")
            if not dp_provider:
                return None
            dp = dp_provider.get(data_product_id)
            if not dp:
                return None
            # Try direct source_system field first
            ss = getattr(dp, "source_system", None)
            # Fallback to metadata dict if not present as direct attribute
            if not ss and hasattr(dp, "metadata") and isinstance(getattr(dp, "metadata", None), dict):
                ss = dp.metadata.get("source_system")
            return ss.lower() if ss else None
        except Exception as e:
            self.logger.debug(f"Error resolving source_system for {data_product_id}: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────

    def _kpi_matches_domains(self, kpi: KPI, target_domains: List[str]) -> bool:
        """
        Check if a KPI is relevant to any of the specified target domains.
        
        This method works with the canonical KPI model structure and handles
        different ways domains might be specified.
        
        Args:
            kpi: The canonical KPI model instance
            target_domains: List of domain names to match against
            
        Returns:
            True if the KPI matches any of the target domains, False otherwise
        """
        # Dict-based KPIs (used in tests/mocks)
        if isinstance(kpi, dict):
            domain = kpi.get('domain')
            if isinstance(domain, str):
                for d in target_domains:
                    if d.lower() == domain.lower():
                        return True
            # business_process_ids (canonical)
            for bp_id in (kpi.get('business_process_ids') or []):
                for d in target_domains:
                    if isinstance(bp_id, str) and bp_id.lower().startswith(d.lower() + '_'):
                        return True
            # business_processes (display strings)
            for process in (kpi.get('business_processes') or []):
                for d in target_domains:
                    if isinstance(process, str) and process.lower().startswith(f"{d.lower()}:"):
                        return True
            # tags
            for tag in (kpi.get('tags') or []):
                for d in target_domains:
                    if isinstance(tag, str) and d.lower() in tag.lower():
                        return True
            # name heuristic for Finance
            if 'Finance' in target_domains:
                name = kpi.get('name')
                if isinstance(name, str) and 'finance' in name.lower():
                    return True
            return False

        # First check the canonical 'domain' attribute
        if hasattr(kpi, 'domain') and isinstance(kpi.domain, str):
            # Direct domain match
            for domain in target_domains:
                if domain.lower() == kpi.domain.lower():
                    return True
                    
        # Check business_process_ids (canonical model)
        if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
            for bp_id in kpi.business_process_ids:
                # Check if business process ID starts with any target domain
                for domain in target_domains:
                    if bp_id.lower().startswith(domain.lower() + '_'):
                        return True
        
        # Check business_processes (backward compatibility)
        if hasattr(kpi, 'business_processes') and kpi.business_processes:
            for process in kpi.business_processes:
                for domain in target_domains:
                    # Check for "Domain: Process" format
                    if isinstance(process, str) and process.lower().startswith(f"{domain.lower()}:"):
                        return True
        
        # Check tags for domain references
        if hasattr(kpi, 'tags') and kpi.tags:
            for tag in kpi.tags:
                for domain in target_domains:
                    if domain.lower() in tag.lower():
                        return True
        
        # For MVP, include Finance KPIs based on name if Finance is a target domain
        if 'Finance' in target_domains and hasattr(kpi, 'name'):
            if 'finance' in kpi.name.lower():
                return True
                
        return False
            
    def _convert_to_kpi_definition(self, kpi: KPI) -> Optional[KPIDefinition]:
        """
        Convert from canonical KPI model to our internal KPIDefinition model.
        
        Args:
            kpi: The canonical KPI model instance from the registry
            
        Returns:
            KPIDefinition instance or None if conversion fails
        """
        # Handle dict-shaped KPIs used by tests/mocks
        if isinstance(kpi, dict):
            name = kpi.get('name')
            if not name:
                return None
            description = kpi.get('description', '')
            unit = kpi.get('unit')
            dp_id = kpi.get('data_product_id') or "FI_Star_Schema"
            business_processes = kpi.get('business_processes') or []
            dimensions = kpi.get('dimensions') or []
            calc = kpi.get('calculation')
            # Optional thresholds mapping
            thresholds = None
            try:
                th = kpi.get('thresholds') or {}
                if isinstance(th, dict):
                    thresholds = {}
                    if 'warning' in th and isinstance(th['warning'], dict):
                        thresholds[SituationSeverity.HIGH] = th['warning'].get('value')
                    if 'critical' in th and isinstance(th['critical'], dict):
                        thresholds[SituationSeverity.CRITICAL] = th['critical'].get('value')
            except Exception:
                thresholds = None
            return KPIDefinition(
                name=name,
                description=description,
                unit=unit,
                calculation=calc,
                thresholds=thresholds,
                dimensions=dimensions,
                business_processes=business_processes,
                data_product_id=dp_id,
                positive_trend_is_good=True,
                plan_version_value=kpi.get('plan_version_value'),
                kpi_type=kpi.get('kpi_type', 'operational'),
            )

        try:
            # Initialize variables with safe defaults
            dimensions = []
            business_processes = []
            thresholds = {}
            positive_trend = True
            diagnostic_questions = []
            kpi_dp_id = "FI_Star_Schema"  # Default
            sql_query = ""
            unit = getattr(kpi, 'unit', None)  # Extract unit
            
            # Extract dimensions with safe access
            try:
                if hasattr(kpi, 'dimensions') and kpi.dimensions:
                    # Convert KPIDimension objects to dimension names
                    for dimension in kpi.dimensions:
                        if hasattr(dimension, 'name'):
                            dimensions.append(dimension.name)
                        elif isinstance(dimension, str):
                            dimensions.append(dimension)
            except Exception as e:
                logger.warning(f"Error accessing dimensions for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Extract business processes with safe access
            try:
                if hasattr(kpi, 'business_processes') and kpi.business_processes:
                    business_processes = kpi.business_processes
                    
                # Also check business_process_ids (canonical model)
                business_process_ids = []
                if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
                    business_process_ids = kpi.business_process_ids
                    for bp_id in kpi.business_process_ids:
                        # Store raw ID for direct matching when process_strings contains IDs
                        if bp_id not in business_processes:
                            business_processes.append(bp_id)
                        # Also store display name for matching when process_strings contains display names
                        parts = bp_id.split('_', 1)
                        if len(parts) > 1:
                            domain, process = parts
                            formatted_bp = f"{domain.capitalize()}: {process.replace('_', ' ').title()}"
                            if formatted_bp not in business_processes:
                                business_processes.append(formatted_bp)
            except Exception as e:
                logger.warning(f"Error accessing business_processes for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Extract thresholds with safe access
            try:
                if hasattr(kpi, 'thresholds') and kpi.thresholds:
                    for threshold in kpi.thresholds:
                        # Format A: severity/value style (YAML KPIs)
                        if hasattr(threshold, 'severity') and hasattr(threshold, 'value'):
                            severity_str = threshold.severity.lower()
                            if severity_str == 'warning':
                                thresholds[SituationSeverity.HIGH] = threshold.value
                            elif severity_str == 'critical':
                                thresholds[SituationSeverity.CRITICAL] = threshold.value
                            if hasattr(threshold, 'inverse_logic') and threshold.inverse_logic:
                                thresholds['_inverse_logic'] = threshold.inverse_logic

                        # Format B: comparison_type/green_threshold style (Supabase KPIs)
                        # These thresholds are percent-change values, NOT absolute values.
                        # Only copy _inverse_logic — numeric thresholds are stored separately
                        # in kpi_def.metadata['variance_thresholds'] by the variance threshold
                        # mapping block below, and are consumed via percent_change comparisons.
                        _is_format_b = (
                            isinstance(threshold, dict) and 'comparison_type' in threshold
                        ) or (
                            not isinstance(threshold, dict)
                            and hasattr(threshold, 'comparison_type')
                            and not (hasattr(threshold, 'severity') and hasattr(threshold, 'value'))
                        )
                        if _is_format_b:
                            _inv = threshold.get('inverse_logic') if isinstance(threshold, dict) else getattr(threshold, 'inverse_logic', None)
                            if _inv:
                                thresholds['_inverse_logic'] = True
            except Exception as e:
                logger.warning(f"Error accessing thresholds for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
            
            # Extract filters with safe access
            filters = {}
            try:
                if hasattr(kpi, 'filters') and kpi.filters:
                    filters = kpi.filters
            except Exception as e:
                logger.warning(f"Error accessing filters for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                            
            # Determine if positive trend is good with safe access
            try:
                if hasattr(kpi, 'positive_trend_is_good'):
                    positive_trend = kpi.positive_trend_is_good
                elif hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict):
                    if 'positive_trend_is_good' in kpi.metadata:
                        # Parse boolean value from metadata
                        value = kpi.metadata['positive_trend_is_good']
                        if isinstance(value, bool):
                            positive_trend = value
                        elif isinstance(value, str):
                            positive_trend = value.lower() == 'true'
                elif hasattr(kpi, 'name'):
                    # Infer from name for common financial metrics
                    kpi_name_lower = kpi.name.lower()
                    if ('cost' in kpi_name_lower or 'expense' in kpi_name_lower or 
                        'debt' in kpi_name_lower or 'deficit' in kpi_name_lower):
                        positive_trend = False
            except Exception as e:
                logger.warning(f"Error determining positive_trend for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                    
            # Get SQL query with safe access
            try:
                if hasattr(kpi, 'sql_query') and kpi.sql_query:
                    sql_query = kpi.sql_query
            except Exception as e:
                logger.warning(f"Error accessing sql_query for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Get diagnostic questions with safe access
            try:
                if hasattr(kpi, 'diagnostic_questions') and kpi.diagnostic_questions:
                    diagnostic_questions = kpi.diagnostic_questions
                elif hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict):
                    if 'diagnostic_questions' in kpi.metadata:
                        questions = kpi.metadata['diagnostic_questions']
                        if isinstance(questions, list):
                            diagnostic_questions = questions
                        elif isinstance(questions, str):
                            # Split by newlines or semicolons if it's a string
                            diagnostic_questions = [q.strip() for q in re.split(r'[\n;]', questions) if q.strip()]
            except Exception as e:
                logger.warning(f"Error accessing diagnostic_questions for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Get data product ID with safe access
            try:
                if hasattr(kpi, 'data_product_id') and kpi.data_product_id:
                    kpi_dp_id = kpi.data_product_id
            except Exception as e:
                logger.warning(f"Error accessing data_product_id for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
            
            # Get filters with safe access
            kpi_filters = {}
            try:
                if hasattr(kpi, 'filters') and kpi.filters:
                    kpi_filters = kpi.filters
            except Exception as e:
                logger.warning(f"Error accessing filters for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")

            # Create KPI definition with all mapped fields
            # First safely get all required attributes
            kpi_name = kpi.name if hasattr(kpi, 'name') else "unknown"
            kpi_desc = kpi.description if hasattr(kpi, 'description') and kpi.description else ""
            kpi_unit = kpi.unit if hasattr(kpi, 'unit') and kpi.unit else ""

            # Propagate registry metadata (including line/altitude) when present
            kpi_metadata = {}
            try:
                if hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict):
                    kpi_metadata = dict(kpi.metadata)
            except Exception:
                kpi_metadata = {}

            kpi_def = KPIDefinition(
                id=getattr(kpi, 'id', None),
                name=kpi_name,
                description=kpi_desc,
                unit=kpi_unit,
                client_id=getattr(kpi, 'client_id', None),
                calculation=sql_query,
                filters=kpi_filters,
                thresholds=thresholds,
                dimensions=dimensions,
                business_processes=business_processes,
                business_process_ids=business_process_ids,
                data_product_id=kpi_dp_id,
                positive_trend_is_good=positive_trend,
                diagnostic_questions=diagnostic_questions,
                metadata=kpi_metadata or None,
                plan_version_value=getattr(kpi, 'plan_version_value', None),
                kpi_type=getattr(kpi, 'kpi_type', 'operational'),
            )
            # Map registry KPIThreshold (comparison-based) into variance thresholds metadata for downstream evaluation
            try:
                if hasattr(kpi, 'thresholds') and kpi.thresholds:
                    variance_thresholds = {}
                    for t in kpi.thresholds:
                        try:
                            comp = getattr(t, 'comparison_type', None)
                            comp_val = comp.value if hasattr(comp, 'value') else (str(comp) if comp is not None else None)
                            if not comp_val:
                                continue
                            ct = str(comp_val).strip().lower()
                            # Normalize keys commonly used in registry
                            if ct in ("qoq", "quarter_over_quarter", "quarter-over-quarter"):
                                key = "qoq"
                            elif ct in ("yoy", "year_over_year", "year-over-year"):
                                key = "yoy"
                            elif ct in ("mom", "month_over_month", "month-over-month"):
                                key = "mom"
                            elif "budget" in ct:
                                key = "budget"
                            elif "target" in ct:
                                key = "target"
                            else:
                                key = ct
                            entry = {}
                            gv = getattr(t, 'green_threshold', None)
                            yv = getattr(t, 'yellow_threshold', None)
                            rv = getattr(t, 'red_threshold', None)
                            inv = getattr(t, 'inverse_logic', False)
                            if gv is not None:
                                entry['green'] = float(gv)
                            if yv is not None:
                                entry['yellow'] = float(yv)
                            if rv is not None:
                                entry['red'] = float(rv)
                            entry['inverse_logic'] = bool(inv)
                            variance_thresholds[key] = entry
                        except Exception:
                            continue
                    if variance_thresholds:
                        if not getattr(kpi_def, 'metadata', None):
                            kpi_def.metadata = {}
                        kpi_def.metadata['variance_thresholds'] = variance_thresholds
            except Exception as _vt_err:
                logger.warning(f"Error mapping variance thresholds for KPI {kpi_name}: {_vt_err}")
            # Inject contract-level filters and metadata (GL accounts, timeframe hints, base column, etc.)
            contract = getattr(self, 'contract', None)
            if isinstance(contract, dict):
                kpis_data = contract.get('kpis', []) or []
                contract_views = contract.get('views') or []
                for kpi_entry in kpis_data:
                    if not isinstance(kpi_entry, dict):
                        continue
                    entry_name = kpi_entry.get('name')
                    if not isinstance(entry_name, str):
                        continue
                    if entry_name.strip().lower() != kpi_name.strip().lower():
                        continue
                    # Found matching KPI in contract
                    calc = kpi_entry.get('calculation')
                    if isinstance(calc, dict):
                        # Merge static filters (e.g., GL account restrictions)
                        if isinstance(calc.get('filters'), dict):
                            kpi_def.filters = {
                                **(kpi_def.filters or {}),
                                **(calc.get('filters') or {})
                            }
                        # Try to derive base_column from query_template if not explicitly set later
                        qt = calc.get('query_template') or calc.get('template')
                        if (not getattr(kpi_def, 'base_column', None)) and isinstance(qt, str):
                            # Extract first quoted or bracketed column
                            m = re.search(r'"([^\"]+)"', qt)
                            if m and m.group(1):
                                kpi_def.base_column = m.group(1)
                            else:
                                m2 = re.search(r'\[([^\]]+)\]', qt)
                                if m2 and m2.group(1):
                                    kpi_def.base_column = m2.group(1)
                    # Explicit base_column at top level takes precedence
                    if isinstance(kpi_entry.get('base_column'), str) and kpi_entry.get('base_column').strip():
                        kpi_def.base_column = kpi_entry.get('base_column')

                    # Simple mapping for grouping/ordering/limit when present
                    if isinstance(kpi_entry.get('partition_by'), list):
                        kpi_def.group_by = kpi_entry.get('partition_by')
                    if isinstance(kpi_entry.get('order_by'), list):
                        kpi_def.order_by = kpi_entry.get('order_by')
                    if kpi_entry.get('top_n') is not None:
                        try:
                            kpi_def.limit = int(kpi_entry.get('top_n'))
                        except Exception:
                            pass

                    # View resolution hint from contract (will still be resolved by DPA/Governance)
                    join_tables = kpi_entry.get('join_tables')
                    if isinstance(join_tables, list) and join_tables:
                        jt0 = join_tables[0]
                        if isinstance(jt0, str) and jt0.strip():
                            kpi_def.view_name = jt0.strip()
                    elif isinstance(contract_views, list) and contract_views:
                        v0 = contract_views[0]
                        if isinstance(v0, dict) and isinstance(v0.get('name'), str):
                            kpi_def.view_name = v0.get('name')

                    # Timeframe hints (date column)
                    # In FI Star View, the canonical alias is "Transaction Date"
                    if not getattr(kpi_def, 'date_column', None):
                        # Allow override via contract if present
                        if isinstance(kpi_entry.get('date_column'), str) and kpi_entry.get('date_column').strip():
                            kpi_def.date_column = kpi_entry.get('date_column').strip()
                        else:
                            kpi_def.date_column = "Transaction Date"

                    # Optional explicit time_filter injection if contract provides one later
                    if isinstance(kpi_entry.get('time_filter'), dict):
                        kpi_def.time_filter = kpi_entry.get('time_filter')

                    break  # done with matching entry

            return kpi_def
        except Exception as e:
            logger.error(f"Error converting KPI to KPIDefinition: {str(e)}")
            return None
    
    def _get_relevant_kpis(
        self,
        principal_context: PrincipalContext,
        business_processes: Optional[List[str]] = None,
        client_id: Optional[str] = None,
        accountable_kpi_ids: Optional[Set[str]] = None,
    ) -> Dict[str, KPIDefinition]:
        """Get KPIs relevant to the principal's business processes.
        
        This method now also applies *principal-specific KPI preferences* based on
        line (top_line/bottom_line) and altitude (strategic/operational), using
        metadata on both the principal profile and the KPIDefinition metadata.
        
        Args:
            principal_context: Principal context with business processes
            business_processes: Optional list of business processes to filter by
            
        Returns:
            Dictionary of relevant KPI definitions, ordered by principal
            preferences when metadata is available.
        """

        # Collect KPIs that match the requested business processes
        relevant_kpis: Dict[str, KPIDefinition] = {}

        # Use explicit business processes if provided, otherwise from principal context
        processes = business_processes if business_processes else (
            principal_context.business_processes if hasattr(principal_context, 'business_processes') else []
        )

        # Normalize selected processes: handle both display names (e.g., "Finance: Expense Management")
        # and canonical IDs (e.g., "finance_expense_management") for robust matching.
        def _to_bp_id(bp_str: str) -> str:
            try:
                s = (bp_str or "").strip().lower()
                # If already looks like an id (no colon and contains underscores), use as-is
                if ':' not in s and '_' in s:
                    return s
                # Drop domain prefix like "finance:" if present
                if ':' in s:
                    s = s.split(':', 1)[1]
                # Replace non-alphanum with spaces, then collapse to underscores
                import re as _re
                s = _re.sub(r"[^a-z0-9]+", " ", s).strip()
                s = "_".join([tok for tok in s.split() if tok])
                # Prepend domain when known from original input
                domain_prefix = None
                if isinstance(bp_str, str) and ':' in bp_str:
                    domain_prefix = bp_str.split(':', 1)[0].strip().lower()
                if domain_prefix:
                    return f"{domain_prefix}_{s}"
                # Fallback to finance domain for MVP if no domain present
                return f"finance_{s}" if not s.startswith("finance_") else s
            except Exception:
                return (bp_str or "").strip().lower()

        selected_bp_names = set(str(bp).strip() for bp in processes if isinstance(bp, str))
        selected_bp_ids = set(_to_bp_id(str(bp)) for bp in selected_bp_names)

        # For domain-level business processes, we just use the processes directly
        # since they're already at the domain level (e.g., "Finance")
        process_strings = []
        
        # Handle both domain-level strings and more specific business processes
        for bp in processes:
            # If it's already a domain name (e.g., "Finance"), use it directly
            if isinstance(bp, str) and ":" not in bp:
                process_strings.append(bp)
            # If it has a domain prefix (e.g., "Finance: Profitability Analysis"), use it as is
            elif isinstance(bp, str) and ":" in bp:
                process_strings.append(bp)
            # Handle enum values or objects
            elif hasattr(bp, 'value'):
                process_name = bp.value.replace('_', ' ').title()
                process_strings.append(process_name)
            else:
                # For any other string business processes
                process_strings.append(str(bp))
        
        # Also try to resolve client_id from PrincipalContext if not explicitly passed
        if not client_id and hasattr(principal_context, 'client_id'):
            client_id = getattr(principal_context, 'client_id', None)

        # Filter KPIs by business process.
        # When client_id is known, iterate only the client-qualified keys
        # (stored as "{client_id}:{kpi_name}") so that name collisions between
        # clients (e.g. both "lubricants" and "apex_lubricants" having "Net Revenue")
        # do not cause one tenant's KPIs to silently overwrite another's.
        if client_id:
            registry_items = [
                (key.split(':', 1)[1], kpi_def)
                for key, kpi_def in self.kpi_registry.items()
                if key.startswith(f"{client_id}:")
            ]
        else:
            # No client scoping — iterate name-keyed entries only (skip qualified duplicates)
            registry_items = [
                (key, kpi_def)
                for key, kpi_def in self.kpi_registry.items()
                if ':' not in key
            ]

        for kpi_name, kpi_def in registry_items:
            # Secondary client guard (defensive — should already be satisfied by key prefix)
            if client_id:
                kpi_client = getattr(kpi_def, 'client_id', None)
                if kpi_client != client_id:
                    continue

            # Include KPIs without business processes defined (test/dev data)
            # Client filter above still applies — no cross-client leak here.
            if not kpi_def.business_processes:
                relevant_kpis[kpi_name] = kpi_def
                continue
                
            # Check if KPI matches any of the relevant business processes
            for bp in process_strings:
                # 1. Check for normalized business process IDs (Exact Match) - High Priority
                if getattr(kpi_def, 'business_process_ids', None) and _to_bp_id(bp) in kpi_def.business_process_ids:
                    relevant_kpis[kpi_name] = kpi_def
                    break
                    
                # 2. Domain-level matching (e.g., "Finance" matches any "Finance: *" or "finance_*")
                elif isinstance(bp, str) and ":" not in bp:
                    # Check if any KPI business process starts with this domain
                    for kpi_bp in kpi_def.business_processes:
                        if isinstance(kpi_bp, str) and (kpi_bp.startswith(f"{bp}:") or 
                                                      kpi_bp.lower().startswith(f"{bp.lower()}_")):
                            relevant_kpis[kpi_name] = kpi_def
                            break
                    # Also check business_process_ids if available
                    if kpi_name not in relevant_kpis and getattr(kpi_def, 'business_process_ids', None):
                        for kpi_bp_id in kpi_def.business_process_ids:
                            if isinstance(kpi_bp_id, str) and kpi_bp_id.lower().startswith(f"{bp.lower()}_"):
                                relevant_kpis[kpi_name] = kpi_def
                                break
                    if kpi_name in relevant_kpis:
                        break
                        
                # 3. Exact matching for fully qualified business processes (Display Name)
                elif bp in kpi_def.business_processes:
                    relevant_kpis[kpi_name] = kpi_def
                    break

        # Apply principal KPI preferences (line/altitude) to ordering when possible
        ordered_kpis = self._apply_principal_kpi_preferences(principal_context, relevant_kpis)

        # Restrict to accountable KPIs when assignments were loaded for this principal.
        # kpi.id is the registry machine ID (e.g. "net_revenue") matching kpi_accountability.kpi_id.
        if accountable_kpi_ids:
            before = len(ordered_kpis)
            ordered_kpis = {
                name: kpi for name, kpi in ordered_kpis.items()
                if getattr(kpi, "id", None) in accountable_kpi_ids
            }
            logger.debug(
                "_get_relevant_kpis: accountability filter %d → %d KPIs "
                "for principal_id=%s",
                before, len(ordered_kpis),
                getattr(principal_context, "principal_id", None),
            )

        logger.debug(
            f"Found {len(ordered_kpis)} KPIs relevant to {len(processes)} business processes "
            f"for principal_id={getattr(principal_context, 'principal_id', None)}"
        )
        return ordered_kpis

    def _apply_principal_kpi_preferences(
        self,
        principal_context: PrincipalContext,
        kpis: Dict[str, KPIDefinition],
    ) -> Dict[str, KPIDefinition]:
        """Reorder KPIs based on principal KPI preferences and KPI metadata.

        Preferences are sourced from the principal profile registry via
        ``self.principal_profiles`` (loaded during ``connect``) using the
        principal's ``principal_id`` or ``role``. KPI semantics come from
        ``KPIDefinition.metadata`` (line/altitude) which were populated from
        the KPI registry.
        """

        if not kpis:
            return kpis

        # Default preferences if none are configured
        line_pref = "balanced"          # top_line_first | bottom_line_first | balanced
        altitude_pref = "balanced"      # strategic_first | operational_first | balanced

        # Look up the full principal profile (dict) by principal_id or role
        try:
            principal_id = getattr(principal_context, "principal_id", None)
            principal_role = getattr(principal_context, "role", None)
            profile = None

            if isinstance(self.principal_profiles, dict):
                # Direct key lookup first
                if principal_id and principal_id in self.principal_profiles:
                    profile = self.principal_profiles[principal_id]
                elif principal_role and principal_role in self.principal_profiles:
                    profile = self.principal_profiles[principal_role]
                # Fallback: search values by id/role fields
                if profile is None:
                    for value in self.principal_profiles.values():
                        try:
                            pdata = (
                                value.model_dump() if hasattr(value, "model_dump")
                                else (dict(value) if isinstance(value, dict) else getattr(value, "__dict__", {}))
                            )
                        except Exception:
                            pdata = {}
                        if not isinstance(pdata, dict):
                            continue
                        if principal_id and pdata.get("id") == principal_id:
                            profile = pdata
                            break
                        if principal_role and (
                            pdata.get("role") == principal_role
                            or pdata.get("name") == principal_role
                        ):
                            profile = pdata
                            break

            # Normalize profile to a dict and extract preferences from profile.metadata if present
            if profile:
                if not isinstance(profile, dict):
                    try:
                        if hasattr(profile, "model_dump"):
                            profile = profile.model_dump()
                        elif hasattr(profile, "__dict__"):
                            profile = dict(profile.__dict__)
                    except Exception:
                        profile = None

            if profile and isinstance(profile, dict):
                meta = profile.get("metadata") or {}
                if isinstance(meta, dict):
                    line_pref = meta.get("kpi_line_preference", line_pref) or line_pref
                    altitude_pref = meta.get("kpi_altitude_preference", altitude_pref) or altitude_pref
        except Exception:
            # If anything goes wrong, fall back to original ordering
            return kpis

        # If no preferences are set, keep original ordering
        if line_pref == "balanced" and altitude_pref == "balanced":
            return kpis

        def _score_kpi(defn: KPIDefinition) -> int:
            """Compute a simple preference score for a KPI based on metadata."""
            score = 0
            try:
                md = getattr(defn, "metadata", None) or {}
                if not isinstance(md, dict):
                    return score
                line = (md.get("line") or "").lower()
                altitude = (md.get("altitude") or "").lower()

                # Line preference: strong signal
                if line_pref == "top_line_first" and line == "top_line":
                    score += 20
                elif line_pref == "bottom_line_first" and line == "bottom_line":
                    score += 20

                # Altitude preference: secondary signal
                if altitude_pref == "strategic_first" and altitude == "strategic":
                    score += 10
                elif altitude_pref == "operational_first" and altitude == "operational":
                    score += 10
            except Exception:
                return score
            return score

        # Sort items by descending score, preserving original order for ties
        scored_items: List[Tuple[str, KPIDefinition]] = list(kpis.items())
        scored_items.sort(key=lambda item: _score_kpi(item[1]), reverse=True)

        # Rebuild ordered dict so downstream iteration respects preferences
        ordered: Dict[str, KPIDefinition] = {}
        for name, defn in scored_items:
            ordered[name] = defn
        try:
            top_names = [name for name, _ in scored_items[:10]]
            self.logger.info(
                "[SA KPI-PREF] principal_id=%s role=%s line_pref=%s altitude_pref=%s ordered_kpis=%s",
                getattr(principal_context, "principal_id", None),
                getattr(principal_context, "role", None),
                line_pref,
                altitude_pref,
                top_names,
            )
        except Exception:
            pass
        return ordered

    # ─── Phase 11I-A: Advanced Alert Intelligence helpers ────────────────────

    def _derive_plan_sql(self, sql_query: str, plan_version_value: str):
        """Substitute the version filter in the actuals SQL to produce a plan/budget SQL.

        Handles double-quoted ("Version"), bracket-quoted ([version]), and unquoted (version)
        column name styles. Returns None when no version filter is found in the query.
        """
        import re as _re
        if not sql_query or not plan_version_value:
            return None
        # Matches: "version", [version], `version`, or bare version — all case-insensitive
        pattern = r'((?:"version"|\[version\]|`version`|version))\s*=\s*\'Actual\''
        # Build replacement without backslash-escaped quotes — re.sub passes \' through as
        # literal backslash+quote which SQL Server rejects as invalid T-SQL.
        replacement = r'\1' + f" = '{plan_version_value}'"
        result, count = _re.subn(pattern, replacement, sql_query, flags=_re.IGNORECASE)
        if count == 0:
            self.logger.debug(
                "_derive_plan_sql: no version filter found in SQL — cannot derive plan SQL"
            )
            return None
        return result

    def _merge_compound_kpi_situations(self, situations: List['Situation']) -> List['Situation']:
        """Fold multiple 'problem' alert_types for the same kpi_name into one card.

        A KPI can trigger any number of 11I-A/11I-B patterns in a single scan
        (threshold_breach, plan_variance, projected_breach, acceleration, compound).
        Without consolidation each pattern becomes its own Situation, so the same
        KPI shows up repeatedly in the UI and inflates finding counts. This groups
        by kpi_name, keeps the most-severe member as the base card, and folds every
        other member's alert_type/narrative into it — capped so a KPI with many
        simultaneous patterns still produces a readable card. 'opportunity' cards
        and KPIs with only one problem alert are passed through unchanged.
        """
        _MAX_OBSERVATIONS = 6
        _MAX_IMPACT_BULLETS = 4
        _severity_order = {s: i for i, s in enumerate(SituationSeverity)}

        # KPIs that have at least one problem card. A plan_variance situation folds into
        # these even if it resolved to 'opportunity' (actual ahead of a conservative plan),
        # so a KPI that is down vs prior period does not ALSO render a contradictory green
        # 'ahead of plan' card. The two comparison bases belong on ONE card — DA renders them
        # together as the segment × basis matrix (Phase 11I-D).
        _problem_kpis = {s.kpi_name for s in situations if s.card_type == "problem"}
        groups: Dict[str, List['Situation']] = {}
        passthrough: List['Situation'] = []
        for sit in situations:
            _folds_in = (sit.card_type == "problem") or (
                sit.alert_type == "plan_variance" and sit.kpi_name in _problem_kpis
            )
            if _folds_in:
                groups.setdefault(sit.kpi_name, []).append(sit)
            else:
                passthrough.append(sit)

        merged: List['Situation'] = []
        for members in groups.values():
            if len(members) == 1:
                merged.append(members[0])
                continue

            members_sorted = sorted(members, key=lambda s: _severity_order.get(s.severity, 99))
            # Primary is always a PROBLEM card — never the folded-in plan_variance 'opportunity',
            # so the merged card keeps problem framing/direction while still absorbing the
            # plan_variance member's alert_type + plan_value via the field collection below.
            primary = next((m for m in members_sorted if m.card_type == "problem"), members_sorted[0])

            alert_types: List[str] = []
            impact_bullets: List[str] = []
            observations: List[str] = []
            tags: List[str] = []
            for m in members_sorted:
                at = m.alert_type or "threshold_breach"
                if at not in alert_types:
                    alert_types.append(at)
                if m.business_impact and m.business_impact not in impact_bullets:
                    impact_bullets.append(m.business_impact)
                for obs in (m.key_observations or []):
                    if obs not in observations:
                        observations.append(obs)
                for t in (m.tags or []):
                    if t not in tags:
                        tags.append(t)
            if "compound_multi_alert" not in tags:
                tags.append("compound_multi_alert")

            # Pattern-specific fields (plan_value, projected_breach_*, acceleration_signal,
            # compound_*) are each set by exactly ONE member — whichever situation matches
            # that alert_type — never by all of them at once. Taking these only from
            # `primary` silently drops them whenever a different pattern (typically
            # threshold_breach, which is detected first and therefore usually wins ties)
            # ends up as primary. Scan all members instead, so e.g. a merged card whose
            # primary is threshold_breach still carries the plan_variance member's
            # plan_value through to VA registration and the frontend alert badge.
            def _first(attr: str):
                for m in members_sorted:
                    v = getattr(m, attr, None)
                    if v is not None:
                        return v
                return None

            combined = primary.model_copy(update={
                "merged_alert_types": alert_types,
                "business_impact": " • ".join(impact_bullets[:_MAX_IMPACT_BULLETS]),
                "key_observations": observations[:_MAX_OBSERVATIONS] or primary.key_observations,
                "hitl_required": any(m.hitl_required for m in members_sorted),
                "tags": tags,
                "plan_value": _first("plan_value"),
                "projected_breach_at_period": _first("projected_breach_at_period"),
                "projection_confidence": _first("projection_confidence"),
                "periods_until_breach": _first("periods_until_breach"),
                "acceleration_signal": _first("acceleration_signal"),
                "compound_alert": any(m.compound_alert for m in members_sorted),
                "related_kpi_id": _first("related_kpi_id"),
                "compound_pattern": _first("compound_pattern"),
            })
            merged.append(combined)

        return merged + passthrough

    async def _fetch_plan_value(self, kpi_def, timeframe, filters, principal_context):
        """Execute plan SQL and return the scalar plan value, or None on any error."""
        plan_version = getattr(kpi_def, 'plan_version_value', None)
        original_sql = getattr(kpi_def, 'calculation', None) or ''
        if not plan_version or not original_sql:
            return None
        plan_sql = self._derive_plan_sql(original_sql, plan_version)
        if not plan_sql:
            return None
        try:
            plan_def = kpi_def.model_copy(update={'calculation': plan_sql})
            plan_kpi_value = await self._get_kpi_value(plan_def, timeframe, None, filters, principal_context)
            if plan_kpi_value is not None:
                return plan_kpi_value.value
        except Exception as e:
            self.logger.warning(f"_fetch_plan_value failed for {kpi_def.name}: {e}")
        return None

    def _project_trend(self, monthly_values, thresholds, inverse_logic, lookback=6, horizon=3):
        """Return projection dict if trend will breach a threshold within `horizon` periods, else None.

        Uses linear regression over the trailing `lookback` periods. Requires R² >= 0.4.
        """
        if not monthly_values or len(monthly_values) < 3:
            return None
        try:
            series = [float(m['value']) for m in monthly_values if m.get('value') is not None]
            if len(series) < 3:
                return None
            tail = series[-lookback:] if len(series) >= lookback else series
            n = len(tail)
            x = list(range(n))
            x_mean = sum(x) / n
            y_mean = sum(tail) / n
            ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, tail))
            ss_xx = sum((xi - x_mean) ** 2 for xi in x)
            if ss_xx == 0:
                return None
            slope = ss_xy / ss_xx
            intercept = y_mean - slope * x_mean
            # R²
            ss_tot = sum((yi - y_mean) ** 2 for yi in tail)
            if ss_tot == 0:
                return None
            ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, tail))
            r2 = 1 - ss_res / ss_tot
            if r2 < 0.4:
                return None  # noisy data — projection unreliable
            # Project values at t+1 … t+horizon
            projections = [slope * (n - 1 + h) + intercept for h in range(1, horizon + 1)]
            # Find the most restrictive threshold (red > yellow)
            threshold_value = None
            for key in ('red', 'yellow', 'critical', 'warning'):
                v = thresholds.get(key) if isinstance(thresholds, dict) else None
                if v is not None:
                    threshold_value = float(v)
                    break
            if threshold_value is None:
                return None
            # Check if any projected value crosses the threshold
            for h, proj in enumerate(projections, start=1):
                crossed = (proj < threshold_value) if not inverse_logic else (proj > threshold_value)
                if crossed:
                    return {
                        'projected_breach_at_period': f"t+{h}",
                        'projection_confidence': round(r2, 3),
                        'periods_until_breach': h,
                        'projected_value': round(proj, 2),
                        'threshold_value': threshold_value,
                        'slope': round(slope, 4),
                    }
            return None
        except Exception as e:
            self.logger.debug(f"_project_trend error: {e}")
            return None

    def _compute_acceleration(self, monthly_values, fire_multiplier=2.0):
        """Return acceleration signal if second derivative exceeds `fire_multiplier`× rolling std of velocity, else None.

        The returned value is the normalised signal magnitude (|acceleration| / velocity_std).
        `fire_multiplier` is sourced from the KPI's registry 'acceleration' threshold (yellow band);
        defaults to 2.0 when unset.
        """
        if not monthly_values or len(monthly_values) < 4:
            return None
        try:
            series = [float(m['value']) for m in monthly_values if m.get('value') is not None]
            if len(series) < 4:
                return None
            # First derivative (velocity): period-over-period delta
            velocity = [series[i] - series[i - 1] for i in range(1, len(series))]
            # Second derivative (acceleration): change in velocity
            acceleration = [velocity[i] - velocity[i - 1] for i in range(1, len(velocity))]
            if not acceleration:
                return None
            latest_accel = acceleration[-1]
            # Rolling std of velocity
            v_mean = sum(velocity) / len(velocity)
            v_variance = sum((v - v_mean) ** 2 for v in velocity) / len(velocity)
            v_std = v_variance ** 0.5
            if v_std == 0:
                return None
            # Only signal if |acceleration| > fire_multiplier × std dev of velocity
            threshold = fire_multiplier * v_std
            if abs(latest_accel) > threshold:
                return round(abs(latest_accel) / v_std, 3)  # normalised signal
            return None
        except Exception as e:
            self.logger.debug(f"_compute_acceleration error: {e}")
            return None

    @staticmethod
    def _timeframe_month_count(timeframe) -> int:
        """Number of whole months spanned by a timeframe — used to convert an aggregate
        budget into a monthly run-rate for budget-anchored projected_breach detection.

        Falls back to 12 if the timeframe can't be resolved (annual assumption).
        """
        try:
            start, end = A9_Situation_Awareness_Agent._bq_get_period_dates(timeframe)
            from datetime import date as _date
            sy, sm, sd = (int(x) for x in str(start).split("-")[:3])
            ey, em, ed = (int(x) for x in str(end).split("-")[:3])
            months = (ey - sy) * 12 + (em - sm) + 1
            return months if months >= 1 else 1
        except Exception:
            return 12

    # ─── End Phase 11I-A helpers ─────────────────────────────────────────────

    async def _get_kpi_value(
        self,
        kpi_definition: KPIDefinition,
        timeframe: TimeFrame,
        comparison_type: Optional[ComparisonType],
        filters: Optional[Dict[str, Any]],
        principal_context: Optional[PrincipalContext] = None
    ) -> Optional[KPIValue]:
        """
        Get KPI value from the Data Product MCP Service Agent.
        Uses Data Governance Agent for view name resolution when available.
        
        Args:
            kpi_name: Name of the KPI
            timeframe: Time frame for analysis
            comparison_type: Type of comparison
            filters: Additional filters
            
        Returns:
            KPI value with comparison if applicable
        """
        try:
            # View resolution is owned by the Data Product Agent. Do not resolve here.
            
            # Get KPI name from definition for logging
            kpi_name = kpi_definition.name
                
            if not kpi_definition:
                self.logger.warning(f"KPI definition is None")
                return None
                
            # Verify data product agent is available
            if not self.data_product_agent:
                logger.error(f"Data Product MCP Service Agent not initialized for KPI {kpi_name}")
                return None
            
            # Merge principal default filters with provided filters
            merged_filters: Dict[str, Any] = {}
            try:
                if principal_context and hasattr(principal_context, 'default_filters') and isinstance(principal_context.default_filters, dict):
                    merged_filters.update(principal_context.default_filters)
            except Exception:
                pass
            try:
                if isinstance(filters, dict):
                    merged_filters.update(filters)
            except Exception:
                pass

            # Single-source SQL generation (for both execution and later UI display)
            # Tier 1: Look up source_system from data product registry
            # Tier 2: Fallback to regex detection if data_product_id is missing or unresolvable
            # Tier 3: Default to DuckDB path
            _raw_kpi_sql = (getattr(kpi_definition, 'calculation', None) or
                            getattr(kpi_definition, 'sql_query', None) or '')
            _gen_dp_id = getattr(kpi_definition, 'data_product_id', None)
            _source_system = self._resolve_source_system(_gen_dp_id)

            if _source_system:
                _is_bq_kpi = _source_system == 'bigquery'
                _is_ss_kpi = _source_system in ('sqlserver', 'sql_server', 'mssql')
                _is_sf_kpi = _source_system == 'snowflake'
            else:
                # Tier 2 fallback: regex detection for unlinked queries
                _is_bq_kpi = bool(re.search(r'`[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+`', _raw_kpi_sql))
                _is_ss_kpi = (not _is_bq_kpi) and bool(re.search(r'\[[A-Za-z][\w\s]*\]', _raw_kpi_sql))
                _is_sf_kpi = False
            _bq_date_col = (
                (kpi_definition.metadata or {}).get('date_column', 'transaction_date')
                if hasattr(kpi_definition, 'metadata') and isinstance(getattr(kpi_definition, 'metadata', None), dict)
                else 'transaction_date'
            )

            # 1) Generate Base SQL via DPA (or directly for BigQuery / SQL Server KPIs)
            base_sql = ""
            _gen_dp_id = getattr(kpi_definition, 'data_product_id', None)
            if _is_bq_kpi:
                base_sql = self._bq_apply_period(_raw_kpi_sql, timeframe, is_comparison=False, date_col=_bq_date_col)
                self.logger.info(f"[BQ path] base_sql for '{kpi_name}': {base_sql[:140]}")
                if not base_sql:
                    self.logger.error(f"[BQ path] Failed to build base SQL for {kpi_name}")
                    return None
            elif _is_ss_kpi:
                # SQL Server path: apply ISO date filter directly (T-SQL accepts BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD').
                # DPA's generate_sql_for_kpi_comparison cannot inject a date filter when the stored T-SQL
                # has no pre-existing timeframe condition, so we mirror the BigQuery pattern here.
                base_sql = self._bq_apply_period(_raw_kpi_sql, timeframe, is_comparison=False, date_col=_bq_date_col)
                self.logger.info(f"[SS path] base_sql for '{kpi_name}': {base_sql[:140]}")
                if not base_sql:
                    self.logger.error(f"[SS path] Failed to build base SQL for {kpi_name}")
                    return None
            elif _is_sf_kpi:
                # Snowflake path: apply ISO date filter directly (Snowflake accepts BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD').
                # Similar to SQL Server, we apply the date filter here since DPA's generate_sql_for_kpi
                # is DuckDB-centric and cannot reliably inject filters into Snowflake SQL.
                base_sql = self._bq_apply_period(_raw_kpi_sql, timeframe, is_comparison=False, date_col=_bq_date_col)
                self.logger.info(f"[SF path] base_sql for '{kpi_name}': {base_sql[:140]}")
                if not base_sql:
                    self.logger.error(f"[SF path] Failed to build base SQL for {kpi_name}")
                    return None
            else:
                try:
                    gen_resp = await self.data_product_agent.generate_sql_for_kpi(
                        kpi_definition=kpi_definition,
                        timeframe=timeframe,
                        filters=merged_filters
                    )
                    if isinstance(gen_resp, dict) and gen_resp.get('success') and isinstance(gen_resp.get('sql', ''), str):
                        base_sql = gen_resp['sql']
                        # Propagate data_product_id for SQL Server backend routing
                        _gen_dp_id = gen_resp.get('data_product_id') or getattr(kpi_definition, 'data_product_id', None)
                    else:
                        self.logger.error(f"Failed to generate base SQL for KPI {kpi_name}: {gen_resp}")
                        return None
                except Exception as ge:
                    self.logger.error(f"Error generating base SQL for KPI {kpi_name}: {ge}")
                    return None

            # Cache base SQL for UI
            try:
                if kpi_name not in self._last_sql_cache:
                    self._last_sql_cache[kpi_name] = {}
                self._last_sql_cache[kpi_name]['base_sql'] = base_sql
                self.logger.info(f"[SA SQL-DEBUG] cached base_sql for '{kpi_name}', length={len(base_sql)}")
            except Exception:
                pass

            # 2) Execute Base SQL via DPA to obtain current KPI value
            current_value = None
            try:
                exec_resp = await self.data_product_agent.execute_sql(base_sql, parameters=None, principal_context=principal_context, data_product_id=_gen_dp_id)
                rows = exec_resp.get('rows') or exec_resp.get('data') or []
                if rows:
                    first = rows[0]
                    if isinstance(first, (list, tuple)) and len(first) > 0:
                        v = first[0]
                        current_value = float(v) if v is not None else None
                    elif isinstance(first, dict):
                        # Prefer common alias if present
                        if 'total_value' in first:
                            v = first['total_value']
                            current_value = float(v) if v is not None else None
                        elif len(first.values()) > 0:
                            v = list(first.values())[0]
                            current_value = float(v) if v is not None else None
                if current_value is None:
                    current_value = 0.0
                self.logger.info(f"Extracted KPI value for {kpi_name}: {current_value}")
            except Exception as e:
                self.logger.error(f"Error executing base SQL for {kpi_name}: {e}")
                return None
            # ── Build monthly series SQL (sync, no I/O) ──
            # BQ/SF: use _raw_kpi_sql; SS: T-SQL fiscal period builder; DPA-path: use base_sql
            monthly_source = _raw_kpi_sql if (_is_bq_kpi or _is_sf_kpi or _is_ss_kpi) else base_sql
            monthly_sql = ""
            if monthly_source:
                if _is_ss_kpi or _is_sf_kpi:
                    _ts = await self._resolve_time_spec_sa(_gen_dp_id)
                    if _ts.get("type") == "fiscal_year_period":
                        _yr = _ts.get("year_column", "fiscal_year")
                        _pr = _ts.get("period_column", "fiscal_period")
                        if _is_ss_kpi:
                            monthly_sql = self._ss_monthly_series_sql(
                                monthly_source, year_col=_yr, period_col=_pr, num_months=9,
                            )
                        else:
                            monthly_sql = self._sf_monthly_series_sql(
                                monthly_source, year_col=_yr, period_col=_pr, num_months=9,
                            )
                    if not monthly_sql:
                        monthly_sql = self._bq_monthly_series_sql(monthly_source, date_col=_bq_date_col, num_months=9)
                else:
                    monthly_sql = self._bq_monthly_series_sql(monthly_source, date_col=_bq_date_col, num_months=9)

            # ── Build comparison SQL (sync for BQ/SS-native, async for DPA-path) ──
            comp_sql = ""
            if comparison_type:
                if _is_bq_kpi:
                    comp_sql = self._bq_apply_period(
                        _raw_kpi_sql, timeframe,
                        is_comparison=True, comparison_type=comparison_type,
                        date_col=_bq_date_col
                    )
                    self.logger.info(f"[BQ path] comp_sql for '{kpi_name}': {comp_sql[:140]}")
                elif _is_ss_kpi:
                    # SQL Server: apply comparison period date filter directly to raw T-SQL.
                    # ISO date strings work in T-SQL, so _bq_apply_period is reusable.
                    comp_sql = self._bq_apply_period(
                        _raw_kpi_sql, timeframe,
                        is_comparison=True, comparison_type=comparison_type,
                        date_col=_bq_date_col
                    )
                    self.logger.info(f"[SS path] comp_sql for '{kpi_name}': {comp_sql[:140]}")
                elif _is_sf_kpi:
                    # Snowflake: apply comparison period date filter directly.
                    # ISO date strings work in Snowflake, so _bq_apply_period is reusable.
                    comp_sql = self._bq_apply_period(
                        _raw_kpi_sql, timeframe,
                        is_comparison=True, comparison_type=comparison_type,
                        date_col=_bq_date_col
                    )
                    self.logger.info(f"[SF path] comp_sql for '{kpi_name}': {comp_sql[:140]}")
                else:
                    try:
                        comp_sql_resp = await self.data_product_agent.generate_sql_for_kpi_comparison(
                            kpi_definition=kpi_definition,
                            timeframe=timeframe,
                            comparison_type=comparison_type,
                            filters=merged_filters
                        )
                        if isinstance(comp_sql_resp, dict) and comp_sql_resp.get('success') and isinstance(comp_sql_resp.get('sql', ''), str):
                            comp_sql = comp_sql_resp['sql']
                        else:
                            self.logger.warning(f"No comparison SQL generated for KPI {kpi_name}: {comp_sql_resp}")
                    except Exception as _ce:
                        self.logger.warning(f"Could not generate comparison SQL for {kpi_name}: {_ce}")

            # Cache comparison SQL for UI debug
            if comp_sql:
                try:
                    if kpi_name not in self._last_sql_cache:
                        self._last_sql_cache[kpi_name] = {}
                    self._last_sql_cache[kpi_name]['comparison_sql'] = comp_sql
                    self.logger.info(f"[SA SQL-DEBUG] cached comparison_sql for '{kpi_name}', length={len(comp_sql)}")
                except Exception:
                    pass

            # ── Fire monthly series + comparison queries concurrently ──
            import asyncio as _asyncio

            async def _fetch_monthly():
                if not monthly_sql:
                    return None
                self.logger.info(f"[Monthly] Executing monthly series for {kpi_name}")
                try:
                    result = await self.data_product_agent.execute_sql(monthly_sql, parameters=None, principal_context=principal_context, data_product_id=_gen_dp_id)
                    if not result or not (result.get("rows") or result.get("data")):
                        self.logger.info(f"[Monthly] No rows returned for {kpi_name}")
                        return None
                    raw_rows = result.get("rows") or result.get("data") or []
                    vals = []
                    for row in raw_rows:
                        if isinstance(row, dict):
                            # Snowflake returns uppercase column names; normalize to lowercase
                            row = {k.lower(): v for k, v in row.items()}
                            period = row.get("period", "")
                            val = row.get("value")
                        elif isinstance(row, (list, tuple)) and len(row) >= 2:
                            period = str(row[0])
                            val = row[1]
                        else:
                            continue
                        if val is not None:
                            try:
                                vals.append({"period": period, "value": float(val)})
                            except (ValueError, TypeError):
                                pass
                    self.logger.info(f"[Monthly] Got {len(vals)} monthly values for {kpi_name}")
                    return vals or None
                except Exception as _me:
                    self.logger.warning(f"[Monthly] Failed to get monthly series for {kpi_name}: {_me}")
                    return None

            async def _fetch_comparison():
                if not comp_sql:
                    return None
                try:
                    return await self.data_product_agent.execute_sql(comp_sql, parameters=None, principal_context=principal_context, data_product_id=_gen_dp_id)
                except Exception as _ce:
                    self.logger.warning(f"Comparison query failed for {kpi_name}: {_ce}")
                    return None

            # SQL Server ODBC cannot handle concurrent queries on the same connection;
            # run monthly + comparison sequentially to avoid "Connection is busy" errors.
            if _is_ss_kpi:
                monthly_values = await _fetch_monthly()
                exec_comp_result = await _fetch_comparison()
            else:
                monthly_values, exec_comp_result = await _asyncio.gather(
                    _fetch_monthly(),
                    _fetch_comparison(),
                )

            # For testing/MVP when comparison not available, return basic KPI value
            if not comparison_type:
                return KPIValue(
                    kpi_name=kpi_name,
                    value=current_value,
                    comparison_value=None,
                    comparison_type=None,
                    timeframe=timeframe,
                    dimensions=merged_filters,
                    percent_change=None,
                    monthly_values=monthly_values
                )

            comparison_value = None
            exec_comp = exec_comp_result or {}
            try:
                if comp_sql:
                    crows = exec_comp.get('rows') or exec_comp.get('data') or []
                    if crows:
                        cfirst = crows[0]
                        if isinstance(cfirst, (list, tuple)) and len(cfirst) > 0:
                            cv = cfirst[0]
                            comparison_value = float(cv) if cv is not None else None
                        elif isinstance(cfirst, dict):
                            if 'total_value' in cfirst:
                                cv = cfirst['total_value']
                            elif cfirst:
                                cv = list(cfirst.values())[0]
                            else:
                                cv = None
                            comparison_value = float(cv) if cv is not None else None
            except Exception as comp_error:
                self.logger.warning(f"Error generating/executing comparison SQL for {kpi_name}: {str(comp_error)}")
                # Continue without comparison value
            
            # Calculate percent change if we have both values
            percent_change = None
            if current_value is not None and comparison_value is not None and comparison_value != 0:
                percent_change = ((current_value - comparison_value) / abs(comparison_value)) * 100

            # Read inverse_logic from KPI threshold config (cost/expense KPIs).
            # Thresholds may be a list of per-comparison-type objects (Supabase KPIs)
            # or a flat dict with '_inverse_logic' key (YAML KPIs). Handle both.
            _inverse_logic = False
            if hasattr(kpi_definition, 'thresholds'):
                _thresholds = kpi_definition.thresholds
                if isinstance(_thresholds, list):
                    # Supabase path: list of threshold objects/dicts — any entry with inverse_logic=True
                    for _t in _thresholds:
                        if isinstance(_t, dict):
                            if _t.get('inverse_logic', False):
                                _inverse_logic = True
                                break
                        elif getattr(_t, 'inverse_logic', False):
                            _inverse_logic = True
                            break
                elif isinstance(_thresholds, dict):
                    # YAML path: flat dict with '_inverse_logic' sentinel key
                    _inverse_logic = bool(_thresholds.get('_inverse_logic', False))
                    if not _inverse_logic:
                        _ptg = _thresholds.get('positive_trend_is_good', None)
                        if _ptg is not None:
                            _inverse_logic = not bool(_ptg)

            # For inverse_logic KPIs where costs are stored as negative debits (e.g. raw
            # SUM(amount) returns a negative number), normalise percent_change so that
            # "costs went up" always shows as a positive number.
            # IMPORTANT: Only flip when current_value is actually negative.  Many KPI SQL
            # queries already negate at the SQL level (SUM(-amount)), making the value
            # positive — applying a second flip here would produce double-negation and
            # incorrectly invert the sign, causing threshold comparisons to evaluate the
            # wrong direction (a cost increase would appear as a decrease).
            if _inverse_logic and percent_change is not None and current_value is not None and current_value < 0:
                percent_change = -percent_change

            return KPIValue(
                kpi_name=kpi_name,
                value=current_value,
                comparison_value=comparison_value,
                comparison_type=comparison_type,
                timeframe=timeframe,
                dimensions=merged_filters,
                percent_change=percent_change,
                monthly_values=monthly_values,
                inverse_logic=_inverse_logic,
            )
        except Exception as e:
            logger.error(f"Error getting KPI value for {kpi_name}: {e}")
            return None

    async def _get_sql_for_kpi(
        self,
        kpi: Any,
        filters: Optional[Dict[str, Any]] = None,
        principal_context: Optional[PrincipalContext] = None,
        timeframe: Optional[TimeFrame] = None
    ) -> str:
        """
        Delegator that returns SQL for a KPI by calling the Data Product Agent.

        Args:
            kpi: KPI name/id (str), dict payload, or a `KPIDefinition` instance
            filters: Optional filter dict
            timeframe: Optional `TimeFrame`

        Returns:
            SQL string if generated, else empty string
        """
        try:
            # Resolve KPI definition
            kpi_def: Optional[KPIDefinition] = None
            if hasattr(kpi, '__dict__'):
                kpi_def = kpi
            elif isinstance(kpi, dict):
                try:
                    kpi_def = KPIDefinition(**kpi)
                except Exception:
                    kpi_def = None
            elif isinstance(kpi, str):
                if kpi in self.kpi_registry:
                    kpi_def = self.kpi_registry[kpi]
                else:
                    k_lower = kpi.strip().lower()
                    for name, kd in self.kpi_registry.items():
                        if str(name).strip().lower() == k_lower:
                            kpi_def = kd
                            break

            if not kpi_def:
                self.logger.warning("_get_sql_for_kpi: KPI definition not found")
                return ""

            if not self.data_product_agent:
                self.logger.error("_get_sql_for_kpi: Data Product Agent not available")
                return ""

            # If available, serve the cached SQL used during detection (avoids re-generation)
            try:
                kpi_name = getattr(kpi_def, 'name', None)
                if isinstance(kpi_name, str) and kpi_name in getattr(self, '_last_sql_cache', {}):
                    cached = self._last_sql_cache[kpi_name].get('base_sql')
                    if isinstance(cached, str) and cached.strip():
                        return cached
            except Exception:
                pass

            # Merge principal default filters with provided filters for SQL generation
            merged_filters: Dict[str, Any] = {}
            try:
                if principal_context is not None:
                    if isinstance(principal_context, dict):
                        pc_df = principal_context.get('default_filters', {})
                    else:
                        pc_df = getattr(principal_context, 'default_filters', {})
                    if isinstance(pc_df, dict):
                        merged_filters.update(pc_df)
            except Exception:
                pass
            try:
                if isinstance(filters, dict):
                    merged_filters.update(filters)
            except Exception:
                pass

            # Debug: log merged filters for per-KPI base SQL
            try:
                self.logger.info(f"[SA SQL-DEBUG] merged_filters for per-KPI base SQL: {merged_filters}")
            except Exception:
                pass

            resp = await self.data_product_agent.generate_sql_for_kpi(
                kpi_definition=kpi_def,
                timeframe=timeframe,
                filters=merged_filters
            )
            if isinstance(resp, dict) and resp.get('success') and isinstance(resp.get('sql', ''), str):
                return resp['sql']
            if hasattr(self.data_product_agent, 'generate_sql_for_query') and isinstance(resp, dict):
                alt = await self.data_product_agent.generate_sql_for_query(resp.get('sql', ''))
                if isinstance(alt, dict) and alt.get('success') and isinstance(alt.get('sql', ''), str):
                    return alt['sql']
            return ""
        except Exception as e:
            self.logger.warning(f"_get_sql_for_kpi error: {e}")
            return ""

    async def _get_comparison_sql_for_kpi(
        self,
        kpi: Any,
        comparison_type: Optional[ComparisonType] = None,
        filters: Optional[Dict[str, Any]] = None,
        principal_context: Optional[PrincipalContext] = None,
        timeframe: Optional[TimeFrame] = None
    ) -> str:
        """
        Delegator that returns Comparison SQL for a KPI by calling the Data Product Agent.

        Args:
            kpi: KPI name/id (str), dict payload, or a `KPIDefinition` instance
            comparison_type: Comparison type (e.g., Budget Vs Actual, QoQ, YoY)
            filters: Optional filter dict
            timeframe: Optional `TimeFrame`

        Returns:
            SQL string if generated, else empty string
        """
        try:
            # Resolve KPI definition
            kpi_def: Optional[KPIDefinition] = None
            if hasattr(kpi, '__dict__'):
                kpi_def = kpi
            elif isinstance(kpi, dict):
                try:
                    kpi_def = KPIDefinition(**kpi)
                except Exception:
                    kpi_def = None
            elif isinstance(kpi, str):
                if kpi in self.kpi_registry:
                    kpi_def = self.kpi_registry[kpi]
                else:
                    k_lower = kpi.strip().lower()
                    for name, kd in self.kpi_registry.items():
                        if str(name).strip().lower() == k_lower:
                            kpi_def = kd
                            break

            if not kpi_def:
                self.logger.warning("_get_comparison_sql_for_kpi: KPI definition not found")
                return ""

            if not self.data_product_agent:
                self.logger.error("_get_comparison_sql_for_kpi: Data Product Agent not available")
                return ""

            # If available, serve the cached comparison SQL used during detection
            try:
                kpi_name = getattr(kpi_def, 'name', None)
                if isinstance(kpi_name, str) and kpi_name in getattr(self, '_last_sql_cache', {}):
                    cached = self._last_sql_cache[kpi_name].get('comparison_sql')
                    if isinstance(cached, str) and cached.strip():
                        return cached
            except Exception:
                pass

            # Merge principal default filters with provided filters for SQL generation
            merged_filters: Dict[str, Any] = {}
            try:
                if principal_context is not None:
                    if isinstance(principal_context, dict):
                        pc_df = principal_context.get('default_filters', {})
                    else:
                        pc_df = getattr(principal_context, 'default_filters', {})
                    if isinstance(pc_df, dict):
                        merged_filters.update(pc_df)
            except Exception:
                pass
            try:
                if isinstance(filters, dict):
                    merged_filters.update(filters)
            except Exception:
                pass

            # Debug: log merged filters for per-KPI comparison SQL
            try:
                self.logger.info(f"[SA SQL-DEBUG] merged_filters for per-KPI comparison SQL: {merged_filters}")
            except Exception:
                pass

            resp = await self.data_product_agent.generate_sql_for_kpi_comparison(
                kpi_definition=kpi_def,
                timeframe=timeframe,
                comparison_type=comparison_type,
                filters=merged_filters
            )
            if isinstance(resp, dict) and isinstance(resp.get('sql', ''), str) and resp.get('sql'):
                return resp['sql']
            return ""
        except Exception as e:
            self.logger.warning(f"_get_comparison_sql_for_kpi error: {e}")
            return ""

    def _detect_opportunities(
        self,
        kpi_definition: KPIDefinition,
        kpi_value: KPIValue,
    ) -> List[OpportunitySignal]:
        """
        Detect positive KPI opportunity signals for a single KPI.

        Three opportunity types are recognised:

        1. **outperformance** — the current value exceeds the highest defined
           threshold multiplied by ``_opportunity_threshold_multiplier``.  This
           applies when positive trend is good and the metric is performing well
           above its own warning/critical bar.

        2. **recovery** — the KPI previously sat below a warning/critical
           threshold but the current value is now above it, AND the period-on-
           period improvement is at least
           ``_opportunity_recovery_min_delta_pct`` percent.

        3. **trend_reversal** — no absolute threshold is defined but the KPI has
           improved by at least ``_opportunity_threshold_multiplier * 10`` percent
           vs the comparison period (e.g. a 15 % improvement when the multiplier
           is 1.5).

        Args:
            kpi_definition: KPI definition with thresholds and directional flag.
            kpi_value:       Current KPI value, optionally with comparison data.

        Returns:
            List of ``OpportunitySignal`` objects (may be empty).
        """
        signals: List[OpportunitySignal] = []

        current = kpi_value.value
        kpi_name = kpi_definition.name
        positive_trend_is_good = getattr(kpi_definition, "positive_trend_is_good", True)

        # ── helpers ───────────────────────────────────────────────────────────

        def _pct_change(new_val: float, old_val: float) -> Optional[float]:
            if old_val is None or old_val == 0:
                return None
            return ((new_val - old_val) / abs(old_val)) * 100.0

        def _make_signal(
            opportunity_type: str,
            headline: str,
            delta_pct: float,
            baseline: float,
            confidence: float = 0.7,
        ) -> OpportunitySignal:
            return OpportunitySignal(
                kpi_name=kpi_name,
                kpi_display_name=kpi_name,
                current_value=current,
                baseline_value=baseline,
                delta_pct=delta_pct,
                opportunity_type=opportunity_type,
                headline=headline,
                confidence=confidence,
            )

        # ── outperformance check (threshold-based) ────────────────────────────
        if kpi_definition.thresholds:
            # Collect the highest threshold value defined (warning or critical)
            threshold_values = []
            for th_key, th_val in kpi_definition.thresholds.items():
                if th_key == "_inverse_logic":
                    continue
                if isinstance(th_val, (int, float)):
                    threshold_values.append(float(th_val))

            if threshold_values:
                # For positive metrics use the max threshold; for inverse metrics
                # (lower is better) treat the minimum threshold as the reference.
                inverse_logic = kpi_definition.thresholds.get("_inverse_logic", False)
                if not isinstance(inverse_logic, bool):
                    inverse_logic = bool(not positive_trend_is_good)

                ref_threshold = min(threshold_values) if inverse_logic else max(threshold_values)

                # For positive-trend metrics: outperformance = current > threshold * multiplier
                # For inverse-trend metrics:  outperformance = current < threshold / multiplier
                if not inverse_logic:
                    target_bar = ref_threshold * self._opportunity_threshold_multiplier
                    if current > target_bar:
                        delta = _pct_change(current, ref_threshold)
                        if delta is not None:
                            signals.append(_make_signal(
                                opportunity_type="outperformance",
                                headline=(
                                    f"{kpi_name} is {abs(delta):.1f}% above its performance threshold "
                                    f"(threshold: {ref_threshold:,.2f}, current: {current:,.2f})"
                                ),
                                delta_pct=delta,
                                baseline=ref_threshold,
                                confidence=0.8,
                            ))
                else:
                    # Lower is better — outperformance = metric is well below threshold
                    target_bar = ref_threshold / self._opportunity_threshold_multiplier
                    if current < target_bar:
                        delta = _pct_change(ref_threshold, current)  # positive = improvement
                        if delta is not None:
                            signals.append(_make_signal(
                                opportunity_type="outperformance",
                                headline=(
                                    f"{kpi_name} is {abs(delta):.1f}% below its performance threshold "
                                    f"(threshold: {ref_threshold:,.2f}, current: {current:,.2f})"
                                ),
                                delta_pct=delta,
                                baseline=ref_threshold,
                                confidence=0.8,
                            ))

        # ── recovery and trend-reversal checks (comparison-based) ────────────
        comparison = kpi_value.comparison_value
        if comparison is not None:
            # Use the sign-normalized percent_change from KPIValue so that cost KPIs
            # stored as negative debits (e.g. SG&A, COGS) are evaluated correctly.
            # Raw _pct_change(current, comparison) would have the wrong sign for those KPIs,
            # causing cost decreases to appear as worsening and triggering an early return.
            pct = kpi_value.percent_change if kpi_value.percent_change is not None else _pct_change(current, comparison)
            if pct is None:
                return signals

            # Determine whether the change is an improvement
            if positive_trend_is_good:
                is_improvement = pct > 0
                improvement_pct = pct
            else:
                is_improvement = pct < 0
                improvement_pct = abs(pct)  # magnitude of improvement

            if not is_improvement:
                return signals  # worsening — not an opportunity

            # Recovery: KPI was previously below a threshold and is now above it.
            # We infer "was previously below threshold" from comparison < threshold.
            if kpi_definition.thresholds:
                threshold_values_all = [
                    float(v) for k, v in kpi_definition.thresholds.items()
                    if k != "_inverse_logic" and isinstance(v, (int, float))
                ]
                if threshold_values_all:
                    inverse_logic = kpi_definition.thresholds.get("_inverse_logic", False)
                    if not isinstance(inverse_logic, bool):
                        inverse_logic = bool(not positive_trend_is_good)

                    # For positive metrics use min threshold as the "floor to recover above"
                    recovery_threshold = min(threshold_values_all) if not inverse_logic else max(threshold_values_all)

                    previously_below = (
                        (not inverse_logic and comparison < recovery_threshold and current >= recovery_threshold)
                        or (inverse_logic and comparison > recovery_threshold and current <= recovery_threshold)
                    )

                    if previously_below and improvement_pct >= self._opportunity_recovery_min_delta_pct:
                        # Avoid duplicating with an outperformance signal already emitted above
                        already_outperformance = any(
                            s.opportunity_type == "outperformance" for s in signals
                        )
                        if not already_outperformance:
                            signals.append(_make_signal(
                                opportunity_type="recovery",
                                headline=(
                                    f"{kpi_name} recovered — up {improvement_pct:.1f}% vs prior period, "
                                    f"now above performance threshold ({recovery_threshold:,.2f})"
                                ),
                                delta_pct=improvement_pct,
                                baseline=comparison,
                                confidence=0.75,
                            ))
                        return signals  # recovery already captured; skip trend_reversal

            # Trend reversal: no absolute threshold but strong % improvement.
            # Skip for Supabase KPIs that have variance_thresholds — the Format-B check
            # below will evaluate them at confidence 0.75 (above the 0.7 Situation threshold).
            # trend_reversal fires at 0.65 which is below the threshold, and its presence
            # in `signals` blocks the Format-B check via the `not signals` guard.
            _has_vt = (
                isinstance(getattr(kpi_definition, 'metadata', None), dict)
                and bool(kpi_definition.metadata.get('variance_thresholds'))
            )
            reversal_bar = self._opportunity_threshold_multiplier * 10.0  # e.g. 1.5 * 10 = 15 %
            if improvement_pct >= reversal_bar and not _has_vt:
                # Do not emit if we already have a signal for this KPI
                if not signals:
                    signals.append(_make_signal(
                        opportunity_type="trend_reversal",
                        headline=(
                            f"{kpi_name} up {improvement_pct:.1f}% vs prior period "
                            f"— significant positive trend reversal"
                        ),
                        delta_pct=improvement_pct,
                        baseline=comparison,
                        confidence=0.65,
                    ))

        # ── percent_change-based opportunity check (Format B / Supabase KPIs) ──────
        # YAML KPIs use absolute-value thresholds (handled above). Supabase KPIs
        # store percent-change thresholds in metadata['variance_thresholds'].
        # We compare kpi_value.percent_change directly against green_threshold here.
        if (
            not signals
            and kpi_value.percent_change is not None
            and hasattr(kpi_definition, 'metadata')
            and isinstance(getattr(kpi_definition, 'metadata', None), dict)
        ):
            vt = kpi_definition.metadata.get('variance_thresholds', {})
            inverse_logic = kpi_definition.thresholds.get('_inverse_logic', False) if isinstance(kpi_definition.thresholds, dict) else False
            for _ct, _entry in vt.items():
                if not isinstance(_entry, dict):
                    continue
                _green = _entry.get('green')
                if _green is None:
                    continue
                pct = kpi_value.percent_change
                # For inverse_logic KPIs: percent_change is already sign-flipped so
                # positive = bad (costs up). Opportunity = costs actually fell (pct < 0).
                # For positive-trend KPIs: opportunity = pct > green_threshold (above target).
                if inverse_logic:
                    if pct < 0:
                        signals.append(_make_signal(
                            opportunity_type="outperformance",
                            headline=(
                                f"{kpi_name} is {abs(pct):.1f}% below prior year "
                                f"— cost reduction above green threshold"
                            ),
                            delta_pct=abs(pct),
                            baseline=kpi_value.comparison_value or kpi_value.value,
                            confidence=0.75,
                        ))
                        break
                else:
                    if pct > _green:
                        signals.append(_make_signal(
                            opportunity_type="outperformance",
                            headline=(
                                f"{kpi_name} grew {pct:.1f}% vs prior year "
                                f"— above {_green:.1f}% target"
                            ),
                            delta_pct=pct,
                            baseline=kpi_value.comparison_value or kpi_value.value,
                            confidence=0.75,
                        ))
                        break

        return signals

    async def _detect_compound_alerts(
        self,
        situations: List[Situation],
        client_id: Optional[str],
    ) -> List[Situation]:
        """Post-processing: flag compound cross-KPI patterns using declared KPI relationships.

        Mutates situations in-place (sets compound_alert, related_kpi_id, compound_pattern).
        Returns the same list.
        """
        if not situations or not client_id:
            return situations
        try:
            from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
            provider = KPIRelationshipProvider()

            # Build a quick lookup: kpi_id → (situation, normalised_direction)
            # normalised_direction: +1 = KPI moving in good direction, -1 = bad direction
            kpi_sit_map: Dict[str, Situation] = {}
            kpi_dir_map: Dict[str, int] = {}
            for sit in situations:
                kid = sit.kpi_id
                if not kid:
                    continue
                kpi_sit_map[kid] = sit
                pct = (sit.kpi_value.percent_change or 0) if sit.kpi_value else 0
                inverse = (sit.kpi_value.inverse_logic if sit.kpi_value else False)
                # +1 = value moving UP (good for revenue, bad for costs)
                raw_dir = 1 if pct >= 0 else -1
                # For inverse KPIs (costs), flip: up is bad
                kpi_dir_map[kid] = raw_dir if not inverse else -raw_dir

            # Check each KPI's declared relationships
            checked_pairs: set = set()
            for kpi_id, sit in kpi_sit_map.items():
                if kpi_id in checked_pairs:
                    continue
                try:
                    relationships = await provider.get_relationships_for_kpi(kpi_id, client_id)
                except Exception as _e:
                    self.logger.debug(f"[Compound] Relationship lookup failed for {kpi_id}: {_e}")
                    continue
                for rel in relationships:
                    # Ensure we always use the canonical pair order
                    primary_id = rel.kpi_id
                    related_id = rel.related_kpi_id
                    pair = tuple(sorted([primary_id, related_id]))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    if primary_id not in kpi_dir_map or related_id not in kpi_dir_map:
                        continue  # one or both KPIs have no situation this run

                    dir_primary = kpi_dir_map[primary_id]
                    dir_related = kpi_dir_map[related_id]

                    conflict = (
                        (rel.conflict_direction == "diverging" and dir_primary != dir_related) or
                        (rel.conflict_direction == "converging" and dir_primary == dir_related)
                    )
                    if not conflict:
                        continue

                    # Build a human-readable compound_pattern
                    def _dir_word(kpi_id_: str) -> str:
                        d = kpi_dir_map.get(kpi_id_, 0)
                        sit_ = kpi_sit_map.get(kpi_id_)
                        name = (sit_.kpi_name if sit_ else kpi_id_)
                        return f"{name} {'UP' if d > 0 else 'DOWN'}"

                    pattern = f"{_dir_word(primary_id)} / {_dir_word(related_id)}"
                    if rel.description:
                        pattern += f" — {rel.description}"

                    # Flag BOTH situations as compound
                    for kid in (primary_id, related_id):
                        other_id = related_id if kid == primary_id else primary_id
                        if kid in kpi_sit_map:
                            kpi_sit_map[kid].compound_alert = True
                            kpi_sit_map[kid].related_kpi_id = other_id
                            kpi_sit_map[kid].compound_pattern = pattern
                            self.logger.info(
                                f"[Compound] Flagged {kid} ↔ {other_id}: {rel.conflict_direction} / {pattern}"
                            )
        except Exception as e:
            self.logger.warning(f"[Compound] Compound alert detection failed: {e}")
        return situations

    def _detect_kpi_situations(
        self,
        kpi_definition: KPIDefinition,
        kpi_value: KPIValue,
        principal_context: PrincipalContext
    ) -> List[Situation]:
        """
        Detect situations for a KPI based on its value and thresholds.
        
        This method uses the canonical KPI model thresholds structure and
        evaluates KPI values against defined thresholds to detect situations.
        
        Args:
            kpi_definition: KPI definition with thresholds
            kpi_value: Current KPI value
            principal_context: Principal context for personalization
            
        Returns:
            List of detected situations
        """
        situations = []
        
        # Check if we have thresholds defined
        if kpi_definition.thresholds:
            # Get the current value for comparison
            current_value = kpi_value.value
            
            # Check if we have inverse logic flag (lower values are better)
            inverse_logic = False
            if '_inverse_logic' in kpi_definition.thresholds:
                inverse_logic = kpi_definition.thresholds['_inverse_logic']
            elif not kpi_definition.positive_trend_is_good:
                # If positive trend is not good, then lower values are better
                inverse_logic = True
                
            # Process thresholds based on severity
            for threshold_key, threshold_value in kpi_definition.thresholds.items():
                # Skip special keys
                if threshold_key == '_inverse_logic':
                    continue
                    
                # Handle different threshold types based on severity
                if threshold_key == SituationSeverity.CRITICAL or threshold_key == "critical":
                    if (inverse_logic and current_value > threshold_value) or \
                       (not inverse_logic and current_value < threshold_value):
                        situations.append(self._create_threshold_situation(
                            kpi_definition,
                            kpi_value,
                            SituationSeverity.CRITICAL,
                            f"{kpi_definition.name} is at a critical level",
                            principal_context
                        ))
                        
                elif threshold_key == SituationSeverity.HIGH or threshold_key == "warning" or threshold_key == "high":
                    if (inverse_logic and current_value > threshold_value) or \
                       (not inverse_logic and current_value < threshold_value):
                        situations.append(self._create_threshold_situation(
                            kpi_definition,
                            kpi_value,
                            SituationSeverity.HIGH,
                            f"{kpi_definition.name} requires attention",
                            principal_context
                        ))
                        
                elif threshold_key == SituationSeverity.INFORMATION or threshold_key == "information" or threshold_key == "low":
                    if (inverse_logic and current_value > threshold_value) or \
                       (not inverse_logic and current_value < threshold_value):
                        situations.append(self._create_threshold_situation(
                            kpi_definition,
                            kpi_value,
                            SituationSeverity.INFORMATION,
                            f"{kpi_definition.name} is outside normal range",
                            principal_context
                        ))
        
        # Check for significant changes if comparison value exists
        if kpi_value.value is not None and kpi_value.comparison_value is not None and kpi_value.comparison_value != 0:
            # Use the sign-normalized percent_change from KPIValue — it has the inverse_logic
            # sign flip already applied for cost KPIs with negatively stored values (e.g. SUM(amount)
            # returns negative for expenses). Recomputing here would use raw values and produce the
            # wrong sign, causing cost decreases to appear as increases and trigger false CRITICAL flags.
            if kpi_value.percent_change is not None:
                percent_change = kpi_value.percent_change
            else:
                percent_change = (kpi_value.value - kpi_value.comparison_value) / abs(kpi_value.comparison_value) * 100

            # Prefer registry-defined variance thresholds when available
            vt_cfg = None
            try:
                meta = getattr(kpi_definition, 'metadata', None) or {}
                vt_all = meta.get('variance_thresholds') or {}
                comp_key = None
                ct = getattr(kpi_value, 'comparison_type', None)
                if ct is not None:
                    ct_val = ct.value if hasattr(ct, 'value') else str(ct)
                    ct_l = str(ct_val).lower()
                    if 'year' in ct_l or ct_l == 'yoy':
                        comp_key = 'yoy'
                    elif 'quarter' in ct_l or ct_l == 'qoq':
                        comp_key = 'qoq'
                    elif 'month' in ct_l or ct_l == 'mom':
                        comp_key = 'mom'
                    elif 'budget' in ct_l:
                        comp_key = 'budget'
                    elif 'target' in ct_l:
                        comp_key = 'target'
                vt_cfg = vt_all.get(comp_key) if comp_key else None
            except Exception:
                vt_cfg = None

            if vt_cfg:
                inv = bool(vt_cfg.get('inverse_logic', False))
                g = vt_cfg.get('green')
                y = vt_cfg.get('yellow')
                r = vt_cfg.get('red')

                # Emulate registry KPI.evaluate() semantics
                evaluation = 'red'
                if not inv:
                    if g is not None and percent_change >= g:
                        evaluation = 'green'
                    elif y is not None and percent_change >= y:
                        evaluation = 'yellow'
                    elif r is not None and percent_change >= r:
                        evaluation = 'red'
                    else:
                        evaluation = 'red'
                else:
                    if g is not None and percent_change <= g:
                        evaluation = 'green'
                    elif y is not None and percent_change <= y:
                        evaluation = 'yellow'
                    elif r is not None and percent_change <= r:
                        evaluation = 'red'
                    else:
                        evaluation = 'red'

                if evaluation in ('yellow', 'red'):
                    severity = SituationSeverity.HIGH if evaluation == 'yellow' else SituationSeverity.CRITICAL
                    change_direction = "increased" if percent_change > 0 else "decreased"
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        severity,
                        f"{kpi_definition.name} {change_direction} by {abs(percent_change):.1f}% vs prior year",
                        principal_context
                    ))
                # Green-band: KPI is performing within or better than threshold — not a problem.
                # Significant improvements are handled by the opportunity detection path below.
            else:
                # Fallback: heuristic severity based on magnitude and trend direction
                is_positive_change = percent_change > 0
                is_good_change = (is_positive_change and kpi_definition.positive_trend_is_good) or \
                                 (not is_positive_change and not kpi_definition.positive_trend_is_good)
                if abs(percent_change) >= 20:
                    severity = SituationSeverity.CRITICAL if not is_good_change else SituationSeverity.INFORMATION
                elif abs(percent_change) >= 10:
                    severity = SituationSeverity.HIGH if not is_good_change else SituationSeverity.INFORMATION
                elif abs(percent_change) >= 5:
                    severity = SituationSeverity.MEDIUM if not is_good_change else SituationSeverity.INFORMATION
                else:
                    severity = SituationSeverity.INFORMATION

                if abs(percent_change) >= 5:
                    change_direction = "increased" if percent_change > 0 else "decreased"
                    change_quality = "worsened" if not is_good_change else "improved"
                    # Business-specific phrasing rule:
                    # For COGS-like KPIs, when the situation is assessed as worsened
                    # but the numeric change is negative ("decreased"), prefer the
                    # display term "increased" per stakeholder phrasing request.
                    try:
                        kpi_name_lower = (getattr(kpi_definition, 'name', '') or '').lower()
                    except Exception:
                        kpi_name_lower = ''
                    if kpi_name_lower in ("cost of goods sold", "cogs", "cost of sales"):
                        if change_quality == "worsened" and change_direction == "decreased":
                            change_direction = "increased"
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        severity,
                        f"{kpi_definition.name} {change_direction} by {abs(percent_change):.1f}% ({change_quality})",
                        principal_context
                    ))
        
        return situations
    
    def _create_threshold_situation(
        self,
        kpi_definition: KPIDefinition,
        kpi_value: KPIValue,
        severity: SituationSeverity,
        description: str,
        principal_context: PrincipalContext
    ) -> Situation:
        """
        Create a situation object for a threshold breach.
        
        Args:
            kpi_definition: KPI definition
            kpi_value: Current KPI value
            severity: Situation severity
            description: Situation description
            principal_context: Principal context for personalization
            
        Returns:
            Situation object
        """
        # Generate business impact with actual KPI numbers
        _val = kpi_value.value
        _cmp = kpi_value.comparison_value
        _pct = kpi_value.percent_change
        _unit = kpi_value.unit or ""
        _role = getattr(principal_context, "role", None)

        def _fmt(v: float) -> str:
            if abs(v) >= 1_000_000:
                return f"${v/1_000_000:.1f}M"
            if abs(v) >= 1_000:
                return f"${v/1_000:.0f}K"
            return f"{v:,.1f}{(' ' + _unit) if _unit else ''}"

        _val_str = _fmt(_val)
        _cmp_str = _fmt(_cmp) if _cmp is not None else None
        _pct_str = f"{_pct:+.1f}%" if _pct is not None else None

        if severity == SituationSeverity.CRITICAL:
            _vs = f" vs. {_cmp_str}" if _cmp_str else ""
            _chg = f" ({_pct_str})" if _pct_str else ""
            _audience = "shareholder expectations and " if _role == PrincipalRole.CFO else ""
            business_impact = (
                f"Immediate attention required: {kpi_definition.name} is {_val_str}{_vs}{_chg}, "
                f"significantly outside target — at risk of impacting {_audience}financial targets."
            )
        elif severity == SituationSeverity.HIGH:
            _vs = f" vs. target {_cmp_str}" if _cmp_str else ""
            _chg = f" ({_pct_str} variance)" if _pct_str else ""
            business_impact = (
                f"Attention needed: {kpi_definition.name} is {_val_str}{_vs}{_chg}, "
                f"outside normal parameters and may indicate an emerging financial issue."
            )
        elif severity == SituationSeverity.MEDIUM:
            _chg = f" ({_pct_str} from target)" if _pct_str else ""
            business_impact = (
                f"Monitor closely: {kpi_definition.name} is {_val_str}{_chg}, "
                f"showing notable variation from expected values."
            )
        else:
            _chg = f" ({_pct_str} change)" if _pct_str else ""
            business_impact = (
                f"For information: {kpi_definition.name} is {_val_str}{_chg}, "
                f"within expected parameters."
            )
        
        # Get diagnostic questions if available
        diagnostic_questions = kpi_definition.diagnostic_questions
        
        # Generate suggested actions based on severity
        suggested_actions = [
            f"Review {kpi_definition.name} in detail",
            f"Compare {kpi_definition.name} across business dimensions"
        ]
        
        if severity in [SituationSeverity.CRITICAL, SituationSeverity.HIGH]:
            suggested_actions.append("Escalate to appropriate stakeholders")
            suggested_actions.append("Initiate deep analysis")
        
        return Situation(
            situation_id=str(uuid.uuid4()),
            kpi_name=kpi_definition.name,
            kpi_id=kpi_definition.id,
            kpi_value=kpi_value,
            severity=severity,
            direction='down',
            description=description,
            business_impact=business_impact,
            suggested_actions=suggested_actions,
            diagnostic_questions=diagnostic_questions,
            timestamp=datetime.now()
        )
    
    # SQL generation methods have been moved to the Data Product Agent
        
    async def _generate_key_observations(
        self,
        kpi_definition: "KPIDefinition",
        kpi_value: "KPIValue",
        situation: "Situation",
    ) -> List[str]:
        """
        Generate 2–3 plain-language observations for a detected situation using a lightweight
        Haiku LLM call. Returns an empty list if the LLM service is unavailable or if any
        error occurs — this method must never raise.
        """
        if self.llm_service_agent is None:
            return []
        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_Request

            # Build streak description from monthly_values if present
            streak_description = ""
            if kpi_value.monthly_values:
                n = len(kpi_value.monthly_values)
                positive_trend_is_good = getattr(kpi_definition, "positive_trend_is_good", True)
                # Determine the direction of the most-recent movement
                if n >= 2:
                    vals = [
                        m["value"] if isinstance(m, dict) else float(m)
                        for m in kpi_value.monthly_values
                    ]
                    moves = [vals[i] - vals[i - 1] for i in range(1, n)]
                    # Count consecutive periods at the end moving in the same direction as the last move
                    last_direction = 1 if moves[-1] >= 0 else -1
                    streak = 1
                    for move in reversed(moves[:-1]):
                        if (1 if move >= 0 else -1) == last_direction:
                            streak += 1
                        else:
                            break
                    direction_word = "up" if last_direction > 0 else "down"
                    streak_description = f"{streak} of last {n} periods trending {direction_word}"
                else:
                    streak_description = f"{n} period(s) of data available"

            trend_line = (
                f"Trend (last {len(kpi_value.monthly_values)} periods): {streak_description}"
                if streak_description
                else ""
            )

            prompt_lines = [
                "You are a financial analyst assistant. Given these facts about a KPI, write exactly 2-3 short observations (each under 15 words, plain language, no markdown bullets). Return as a JSON array of strings.",
                "",
                f"KPI: {kpi_definition.name}",
                f"Current value: {kpi_value.value} (vs {kpi_value.comparison_value}, {kpi_value.comparison_type})",
                f"Change: {kpi_value.percent_change:+.1f}%" if kpi_value.percent_change is not None else "Change: N/A",
                f"Severity: {situation.severity.value if hasattr(situation.severity, 'value') else situation.severity}",
            ]
            if trend_line:
                prompt_lines.append(trend_line)
            prompt_lines.append("")
            prompt_lines.append('Return ONLY a JSON array, e.g. ["observation 1", "observation 2", "observation 3"]')

            prompt = "\n".join(prompt_lines)

            request = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id="system",
                prompt=prompt,
                operation="generate",
                temperature=0.2,
                # Haiku via routing table — overridable via CLAUDE_MODEL_NLP
                model=get_claude_model_for_task(ClaudeTaskType.NLP_PARSING),
            )

            response = await self.llm_service_agent.generate(request)
            content = response.content if hasattr(response, "content") else str(response)

            array_match = re.search(r'\[[\s\S]*?\]', content)
            if array_match:
                observations = json.loads(array_match.group())
                if isinstance(observations, list):
                    return [str(o) for o in observations[:3]]
            return []
        except Exception as exc:
            self.logger.warning(f"_generate_key_observations failed for {kpi_definition.name}: {exc}")
            return []

    async def _generate_trend_note(
        self,
        kpi_definition: "KPIDefinition",
        kpi_value: "KPIValue",
        situation: "Situation",
    ) -> Optional[str]:
        """
        Generate a single-sentence trend note when the intra-period monthly trend
        contradicts the headline YoY direction. Returns None if no contradiction,
        data is insufficient, or LLM is unavailable. Never raises.
        """
        if self.llm_service_agent is None:
            return None
        try:
            if not kpi_value.monthly_values or len(kpi_value.monthly_values) < 3:
                return None

            vals = [
                m["value"] if isinstance(m, dict) else float(m)
                for m in kpi_value.monthly_values
            ]
            recent = vals[-3:]
            first, last = recent[0], recent[-1]
            if first == 0:
                return None
            recent_pct = ((last - first) / abs(first)) * 100
            if abs(recent_pct) < 2:
                return None

            inverse_logic = getattr(kpi_definition, "inverse_logic", False) or (kpi_value.inverse_logic or False)
            pct_change = kpi_value.percent_change or 0
            # headline_good: the YoY comparison is favourable
            headline_good = (pct_change <= 0) if inverse_logic else (pct_change >= 0)
            # recent_trend_good: the last 3 periods are moving in the favourable direction
            recent_up = recent_pct > 0
            recent_trend_good = (not recent_up) if inverse_logic else recent_up

            # Only generate a note when the directions contradict
            if headline_good == recent_trend_good:
                return None

            from src.agents.new.a9_llm_service_agent import A9_LLM_Request

            direction_word = "rising" if recent_up else "falling"
            kpi_type = "cost" if inverse_logic else "revenue/performance"
            tension = (
                f"Headline is {'favourable' if headline_good else 'unfavourable'} ({pct_change:+.1f}% YoY) "
                f"but monthly values have been {direction_word} over the last 3 periods ({recent_pct:+.1f}%)"
            )

            prompt = "\n".join([
                "You are a financial analyst briefing a CFO. A KPI has a tension between its headline performance and its recent monthly trajectory.",
                "Write ONE sentence (max 18 words) in plain business language that names this tension. No markdown, no quotes, no bullet points.",
                "",
                f"KPI: {kpi_definition.name}",
                f"KPI type: {kpi_type}",
                f"Comparison: {kpi_value.comparison_type or 'year-over-year'}",
                f"Tension: {tension}",
                "",
                "Return only the sentence.",
            ])

            request = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id="system",
                prompt=prompt,
                operation="generate",
                temperature=0.2,
                # Haiku via routing table — overridable via CLAUDE_MODEL_NLP
                model=get_claude_model_for_task(ClaudeTaskType.NLP_PARSING),
            )

            response = await self.llm_service_agent.generate(request)
            content = (response.content if hasattr(response, "content") else str(response)).strip().strip('"').strip("'")
            return content if content else None

        except Exception as exc:
            self.logger.warning(f"_generate_trend_note failed for {kpi_definition.name}: {exc}")
            return None

    async def _detect_situations_from_kpi_values(
        self,
        kpi_values: List[KPIValue],
        principal_context: PrincipalContext
    ) -> List[Situation]:
        """
        Detect situations from a list of KPI values.
        
        This method analyzes real data values from the backend and identifies
        situations based on thresholds, trends, and comparison values.
        
        Args:
            kpi_values: List of KPI values retrieved from the database
            principal_context: Principal context for personalization
            
        Returns:
            List of detected situations
        """
        self.logger.info(f"Detecting situations from {len(kpi_values)} KPI values")
        
        # Store all detected situations
        all_situations = []
        
        # Process each KPI value
        for kpi_value in kpi_values:
            # Get the KPI definition from registry
            kpi_definition = self.kpi_registry.get(kpi_value.kpi_name)
            if not kpi_definition:
                self.logger.warning(f"KPI definition not found for {kpi_value.kpi_name}, skipping situation detection")
                continue
            
            # Detect situations for this KPI
            self.logger.info(f"Analyzing KPI {kpi_value.kpi_name} = {kpi_value.value}")
            kpi_situations = self._detect_kpi_situations(
                kpi_definition,
                kpi_value,
                principal_context
            )
            
            self.logger.info(f"Detected {len(kpi_situations)} situations for KPI {kpi_value.kpi_name}")

            # Enrich each situation with lightweight Haiku observations and trend note
            for sit in kpi_situations:
                sit.key_observations = await self._generate_key_observations(kpi_definition, kpi_value, sit)
                sit.trend_note = await self._generate_trend_note(kpi_definition, kpi_value, sit)

            # Add to all situations
            all_situations.extend(kpi_situations)
        
        # Sort situations by severity (critical first)
        all_situations.sort(key=lambda s: list(SituationSeverity).index(s.severity) if s.severity in SituationSeverity else 99)
        
        self.logger.info(f"Total situations detected: {len(all_situations)}")
        return all_situations
    
    async def _generate_sql_for_query(
        self,
        query: str,
        kpi_values: List[KPIValue]
    ) -> Optional[str]:
        """
        Generate SQL for a natural language query by delegating to the Data Product Agent.
        Centralizes all SQL generation paths (LLM and deterministic) in the Data Product Agent.
        """
        try:
            if not self.data_product_agent:
                self.logger.warning("Data Product Agent not available for SQL generation")
                return None
            # Build a minimal context for DPA (let DPA decide how to use LLM/deterministic paths)
            dp_id = self.config.get("data_product_id", "fi_star_schema")
            context = {
                'data_product_id': dp_id,
                'kpi_values': [kv.model_dump() if hasattr(kv, 'model_dump') else kv.__dict__ for kv in (kpi_values or [])]
            }
            dp_resp = await self.data_product_agent.generate_sql(query, context)
            if isinstance(dp_resp, dict) and dp_resp.get('success') and dp_resp.get('sql'):
                return dp_resp['sql']
            self.logger.warning(f"Data Product Agent returned no SQL: {dp_resp}")
            return None
        except Exception as e:
            self.logger.error(f"Error delegating SQL generation to Data Product Agent: {e}")
            return None


    def _generate_answer_for_query(self, query: str, kpi_values: List[KPIValue]) -> str:
        """
        Deterministic, lightweight answer generator for NL queries.
        Produces a concise summary from available KPI values without LLMs.
        """
        try:
            if not kpi_values:
                return (
                    "I couldn't map your question to a specific KPI. "
                    "Please refine the question or select a KPI from the card."
                )

            def _fmt_timeframe(tf: Any) -> str:
                try:
                    if hasattr(tf, 'name'):
                        return str(tf.name).replace('_', ' ').title()
                    if hasattr(tf, 'value'):
                        return str(tf.value)
                    return str(tf) if tf else "current period"
                except Exception:
                    return "current period"

            lines: List[str] = []
            for kv in kpi_values[:3]:
                name = getattr(kv, 'kpi_name', 'KPI')
                val = getattr(kv, 'value', None)
                tf = _fmt_timeframe(getattr(kv, 'timeframe', None))

                # Optional unit lookup from registry
                unit = ""
                try:
                    if hasattr(self, 'kpi_registry') and isinstance(self.kpi_registry, dict) and name in self.kpi_registry:
                        unit_str = getattr(self.kpi_registry[name], 'unit', None)
                        if unit_str:
                            unit = f" {unit_str}"
                except Exception:
                    unit = ""

                if isinstance(val, (int, float)):
                    val_str = f"{val:,.2f}"
                else:
                    val_str = str(val)
                lines.append(f"{name} for {tf}: {val_str}{unit}")

            if len(kpi_values) > 3:
                lines.append(f"...and {len(kpi_values) - 3} more.")
            return " | ".join(lines)
        except Exception as e:
            # Fail-safe fallback
            try:
                self.logger.warning(f"_generate_answer_for_query fallback due to: {e}")
            except Exception:
                pass
            if kpi_values:
                try:
                    return "; ".join(
                        [f"{getattr(kv, 'kpi_name', 'KPI')}: {getattr(kv, 'value', 'N/A')}" for kv in kpi_values[:3]]
                    )
                except Exception:
                    return "Answer available, but formatting failed."
            return "No KPI values available to answer."


    async def get_recommended_questions(self, principal_context: PrincipalContext, business_process: Optional[BusinessProcess] = None) -> List[str]:
        try:
            kpis = list(self.kpi_registry.keys()) if isinstance(self.kpi_registry, dict) else []
            tf_list = getattr(principal_context, 'preferred_timeframes', None) or []
            def _tf_label(tf):
                try:
                    return getattr(tf, 'value', None) or getattr(tf, 'name', None) or str(tf)
                except Exception:
                    return "current_period"
            tf_label = _tf_label(tf_list[0]) if tf_list else "current_period"
            qs: List[str] = []
            if kpis:
                top = kpis[:3]
                for name in top:
                    qs.append(f"What is {name} for {tf_label}?")
                if len(kpis) > 1:
                    qs.append(f"How does {kpis[0]} compare to budget for {tf_label}?")
            else:
                qs = [
                    f"What are the top KPIs for {tf_label}?",
                    f"Which KPIs deviated most from budget for {tf_label}?",
                ]
            return qs
        except Exception:
            return ["Show me key finance KPIs this period."]

    async def get_kpi_definitions(
        self,
        principal_context: PrincipalContext,
        business_process: Optional[BusinessProcess] = None
    ) -> Dict[str, Any]:
        """
        Get KPI definitions relevant to the principal and business process.

        Args:
            principal_context: Context of the principal
            business_process: Optional specific business process to filter by

        Returns:
            Dictionary of KPI definitions keyed by KPI name
        """
        try:
            # Infra A4-a: refresh KPI registry from Supabase per request so new
            # clients / new KPIs become visible without a service restart.
            await self._load_kpi_registry()

            bp_list: Optional[List[str]] = None
            if business_process is not None:
                bp_name = (
                    getattr(business_process, 'value', None)
                    or getattr(business_process, 'name', None)
                    or str(business_process)
                )
                bp_list = [bp_name]

            _kpi_client_id = getattr(principal_context, 'client_id', None) if hasattr(principal_context, 'client_id') else None
            relevant_kpis: Dict[str, KPIDefinition] = self._get_relevant_kpis(
                principal_context, bp_list, client_id=_kpi_client_id,
            )

            return {
                name: kpi_def.model_dump()
                for name, kpi_def in relevant_kpis.items()
            }
        except Exception as e:
            self.logger.error(f"Error retrieving KPI definitions: {e}")
            return {}


def create_situation_awareness_agent(config: Dict[str, Any]) -> "A9_Situation_Awareness_Agent":
    """
    Factory function to create a Situation Awareness Agent.
    
    Args:
        config: Configuration dictionary with these options:
            - registry_factory: Initialized RegistryFactory instance (injected by bootstrap)
            - target_domains: List of domain prefixes to filter KPIs (optional, defaults to ['Finance'])
            - kpi_thresholds: Custom KPI thresholds (optional)
            - principal_profile_path: Custom principal profile path (optional)
        
    Returns:
        A9_Situation_Awareness_Agent instance
    """
    # Set defaults for optional config
    if "target_domains" not in config:
        config["target_domains"] = ["Finance"]  # Default for MVP
        
    return A9_Situation_Awareness_Agent(config)
