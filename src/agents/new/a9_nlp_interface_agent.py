"""
A9 NLP Interface Agent (MVP Scaffold)

Provides a protocol-compliant interface for natural language parsing in Agent9.
- parse_business_query: extracts business-level intent (KPI/groupings/time/TopN)
- entity_extraction: MVP entity extraction for dates and dimensions

Deterministic path only:
- No business-to-technical translation here (delegated to DGA)
- No SQL generation here (delegated to DPA)

This agent is orchestrator-driven and integrates with the Unified Registry via RegistryFactory.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.agents.models.nlp_models import (
    NLPBusinessQueryInput,
    NLPBusinessQueryResult,
    MatchedView,
    TimeFilterSpec,
    TopNSpec,
    EntityExtractionInput,
    EntityExtractionResult,
    ExtractedEntity,
)
from src.agents.agent_config_models import A9_NLP_Interface_Agent_Config
from src.registry.factory import RegistryFactory


logger = logging.getLogger(__name__)


class A9_NLP_Interface_Agent:
    """
    Agent9 NLP Interface Agent

    Orchestrator-driven agent that parses natural language into business-level
    intent and defers translation (DGA) and SQL/timeframes (DPA).
    """

    def __init__(self, config: Dict[str, Any] | A9_NLP_Interface_Agent_Config | None = None):
        # Store config (accept dict or typed config)
        self.config: Dict[str, Any] = config if isinstance(config, dict) else (
            {} if config is None else config.model_dump()
        )
        self.name = "A9_NLP_Interface_Agent"
        self.version = "0.1.0"

        # Dependencies
        self.registry_factory: Optional[RegistryFactory] = None
        self.business_glossary_provider = None
        self.kpi_provider = None

        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    async def create(cls, config: Dict[str, Any] | A9_NLP_Interface_Agent_Config | None = None) -> "A9_NLP_Interface_Agent":
        agent = cls(config)
        await agent.connect()
        return agent

    async def connect(self) -> bool:
        """Connect to registry providers via RegistryFactory (no local caching)."""
        try:
            self.registry_factory = RegistryFactory()
            try:
                if not getattr(self.registry_factory, "is_initialized", False):
                    await self.registry_factory.initialize()
            except Exception:
                # Some implementations may not require explicit initialize
                pass

            # Business Glossary Provider (for future validation, not used for translation here)
            try:
                self.business_glossary_provider = self.registry_factory.get_provider("business_glossary")
            except Exception as e:
                self.logger.warning(f"Business Glossary Provider unavailable: {e}")
                self.business_glossary_provider = None

            # KPI Provider (used to resolve KPI mentions deterministically)
            try:
                # Prefer convenience accessor that creates a default provider if missing
                self.kpi_provider = self.registry_factory.get_kpi_provider()
                if not self.kpi_provider:
                    # Fallback to direct provider lookup
                    self.kpi_provider = self.registry_factory.get_provider("kpi")
                # Ensure provider data is loaded (RegistryFactory may mark as initialized without loading)
                if self.kpi_provider and hasattr(self.kpi_provider, "load"):
                    try:
                        await self.kpi_provider.load()
                    except TypeError:
                        # In case load is not async in some implementations
                        self.kpi_provider.load()
            except Exception as e:
                self.logger.warning(f"KPI Provider unavailable: {e}")
                self.kpi_provider = None

            self.logger.info("NLP Interface Agent connected to registry providers")
            return True
        except Exception as e:
            self.logger.error(f"Error connecting NLP Interface Agent: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            # Nothing external to disconnect in MVP
            self.logger.info("NLP Interface Agent disconnected")
            return True
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
            return False

    # --- Protocol entrypoints ---

    async def parse_business_query(
        self,
        input_model: NLPBusinessQueryInput,
        context: Optional[Dict[str, Any]] = None,
    ) -> NLPBusinessQueryResult:
        """
        Parse a natural language business query into business-level intent.
        - Returns KPI/groupings/filters/time hints/TopN.
        - Does NOT perform business-to-technical translation.
        - Reads yaml_contract_text from context if present (no caching).
        """
        try:
            # Validate input
            if not (input_model.query or input_model.business_terms):
                return NLPBusinessQueryResult(
                    matched_views=[],
                    unmapped_terms=["query"],
                    human_action_required=True,
                    human_action_type="clarification",
                    human_action_context={
                        "message": "Please provide a natural language query or business terms."
                    },
                )

            query_text = (input_model.query or "").strip()
            principal_ctx = input_model.principal_context or {}
            typical_timeframes = []
            try:
                typical_timeframes = principal_ctx.get("typical_timeframes") or []
            except Exception:
                typical_timeframes = []

            # Extract Top/Bottom N intent
            topn = self._extract_topn(query_text)

            # Extract timeframe hints (neutral, no date math here)
            time_hint = self._extract_time_hint(query_text, typical_timeframes)

            # Extract groupings (simple 'by <something>' pattern)
            groupings = self._extract_groupings(query_text)

            # Resolve KPI name deterministically when possible
            resolved_kpi = self._resolve_kpi_name(query_text)

            matched_views: List[MatchedView] = []
            unmapped_terms: List[str] = []
            human_action_required = False
            human_action_type = None
            human_action_context = None

            if resolved_kpi:
                matched_views.append(
                    MatchedView(
                        kpi_name=resolved_kpi,
                        groupings=groupings,
                        time_filter=time_hint,
                        filters={},  # business-level filters from text only; principal defaults are in principal_context
                    )
                )
            else:
                human_action_required = True
                human_action_type = "clarification"
                human_action_context = {
                    "message": "Could not resolve KPI from your question. Please specify the KPI (e.g., 'Gross Margin' or 'Revenue')."
                }

            return NLPBusinessQueryResult(
                matched_views=matched_views,
                unmapped_terms=unmapped_terms,
                filters={},  # NLP itself does not inject technical filters
                topn=topn,
                principal_context=principal_ctx,
                human_action_required=human_action_required,
                human_action_type=human_action_type,
                human_action_context=human_action_context,
            )
        except Exception as e:
            self.logger.error(f"Error parsing business query: {e}")
            return NLPBusinessQueryResult(
                matched_views=[],
                unmapped_terms=["internal_error"],
                filters={},
                topn=None,
                principal_context=input_model.principal_context or {},
                human_action_required=True,
                human_action_type="error",
                human_action_context={"message": str(e)},
            )

    async def entity_extraction(
        self,
        input_model: EntityExtractionInput,
        context: Optional[Dict[str, Any]] = None,
    ) -> EntityExtractionResult:
        """
        MVP entity extraction:
        - Extracts dates (month/year words), simple 'by <dimension>' segments.
        - Validates types loosely; defers strict mapping to DGA/glossary.
        """
        try:
            text = input_model.text or ""
            entities: List[ExtractedEntity] = []

            # Months & year (simple patterns)
            months = (
                "january|february|march|april|may|june|july|august|september|october|november|december"
            )
            for m in re.finditer(rf"\b({months})\b", text, flags=re.I):
                entities.append(
                    ExtractedEntity(
                        type="month",
                        value=m.group(0),
                        start_char=m.start(),
                        end_char=m.end(),
                        confidence=0.9,
                    )
                )
            for y in re.finditer(r"\b(20\d{2})\b", text):
                entities.append(
                    ExtractedEntity(
                        type="year",
                        value=y.group(1),
                        start_char=y.start(),
                        end_char=y.end(),
                        confidence=0.9,
                    )
                )

            # Group-by segments: 'by <token>' (capture one or two tokens)
            for gb in re.finditer(r"\bby\s+([a-zA-Z_/\- ]{2,40})", text, flags=re.I):
                val = gb.group(1).strip()
                # Limit to first 2 words to avoid over-capturing sentences
                pieces = val.split()
                if pieces:
                    value = " ".join(pieces[:2])
                    entities.append(
                        ExtractedEntity(
                            type="groupby",
                            value=value,
                            start_char=gb.start(1),
                            end_char=gb.start(1) + len(value),
                            confidence=0.7,
                        )
                    )

            return EntityExtractionResult(
                entities=entities,
                unmapped_terms=[],
                human_action_required=False,
            )
        except Exception as e:
            self.logger.error(f"Error in entity_extraction: {e}")
            return EntityExtractionResult(
                entities=[],
                unmapped_terms=["internal_error"],
                human_action_required=True,
                human_action_type="error",
                human_action_context={"message": str(e)},
            )

    # --- Helpers ---

    def _extract_topn(self, query_text: str) -> Optional[TopNSpec]:
        if not query_text:
            return None
        m = re.search(r"\btop\s+(\d+)\b", query_text, flags=re.I)
        if m:
            # Optional 'by <field>'
            field = self._extract_rank_field(query_text)
            return TopNSpec(limit_type="top", limit_n=int(m.group(1)), limit_field=field)
        m = re.search(r"\bbottom\s+(\d+)\b", query_text, flags=re.I)
        if m:
            field = self._extract_rank_field(query_text)
            return TopNSpec(limit_type="bottom", limit_n=int(m.group(1)), limit_field=field)
        return None

    def _extract_rank_field(self, query_text: str) -> Optional[str]:
        # naive: capture 'by <field>' after 'top/bottom N'
        m = re.search(r"\b(?:top|bottom)\s+\d+\s+([a-z]+)\s+by\s+([\w/ \-]+)", query_text, flags=re.I)
        if m:
            return m.group(2).strip()
        m = re.search(r"\bby\s+([\w/ \-]+)", query_text, flags=re.I)
        if m:
            return m.group(1).strip()
        return None

    def _extract_time_hint(self, query_text: str, typical_timeframes: List[str]) -> Optional[TimeFilterSpec]:
        q = (query_text or "").lower()
        # Explicit phrases
        if "last quarter" in q:
            return TimeFilterSpec(expression="last_quarter", granularity="quarter")
        if "current quarter" in q or "this quarter" in q:
            return TimeFilterSpec(expression="current_quarter", granularity="quarter")
        if "ytd" in q or "year to date" in q:
            return TimeFilterSpec(expression="year_to_date", granularity="year")
        if "qtd" in q or "quarter to date" in q:
            return TimeFilterSpec(expression="quarter_to_date", granularity="quarter")
        if "mtd" in q or "month to date" in q:
            return TimeFilterSpec(expression="month_to_date", granularity="month")
        if "last month" in q:
            return TimeFilterSpec(expression="last_month", granularity="month")
        if "this month" in q or "current month" in q:
            return TimeFilterSpec(expression="current_month", granularity="month")
        if "last year" in q:
            return TimeFilterSpec(expression="last_year", granularity="year")
        if "this year" in q or "current year" in q:
            return TimeFilterSpec(expression="current_year", granularity="year")

        # Neutral 'current' phrase resolved with principal typical_timeframes
        if "current" in q or "now" in q:
            gran = self._choose_granularity(typical_timeframes)
            return TimeFilterSpec(expression="current", granularity=gran)
        return None

    def _choose_granularity(self, typical_timeframes: List[str]) -> Optional[str]:
        # Prefer Quarterly > Monthly if both present; else first match
        norm = [str(x).strip().lower() for x in typical_timeframes or []]
        if any("quarter" in x for x in norm):
            return "quarter"
        if any("month" in x for x in norm):
            return "month"
        if any("year" in x for x in norm):
            return "year"
        return None

    def _extract_groupings(self, query_text: str) -> List[str]:
        if not query_text:
            return []
        m = re.search(r"\bby\s+([a-zA-Z_/\- ]{2,40})", query_text, flags=re.I)
        if not m:
            return []
        candidates = m.group(1).strip().split()
        if not candidates:
            return []
        # Take first two tokens as a simple grouping (e.g., 'profit center')
        return [" ".join(candidates[:2])]

    def _resolve_kpi_name(self, query_text: str) -> Optional[str]:
        if not query_text or not self.kpi_provider:
            return None
        q = query_text.lower()
        try:
            kpis = self.kpi_provider.get_all() or []
            # Attempt simple name/synonym containment match
            for k in kpis:
                name = getattr(k, "name", None)
                if isinstance(name, str) and name.lower() in q:
                    return name
                # optional synonyms list
                syns = None
                for cand_attr in ("synonyms", "alias", "aliases"):
                    syns = getattr(k, cand_attr, None)
                    if syns:
                        break
                if isinstance(syns, (list, tuple)):
                    for s in syns:
                        if isinstance(s, str) and s.lower() in q:
                            return name or s
        except Exception as e:
            self.logger.warning(f"Error resolving KPI name: {e}")
        # Deterministic fallback for common KPI phrases (keeps NLP deterministic for MVP)
        if "gross revenue" in q or ("revenue" in q and "growth" not in q):
            return "Gross Revenue"
        if "gross margin" in q or "margin" in q:
            return "Gross Margin"
        if "cost of goods" in q or "cogs" in q:
            return "Cost of Goods Sold"
        return None
