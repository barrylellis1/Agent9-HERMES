"""
# doc-sync-skip
A9 Data Governance Agent

This agent provides data governance capabilities, including business-to-technical term translation,
data quality monitoring, access control, and compliance tracking.

It leverages the Unified Registry Access Layer for business glossary terms,
data product contracts, and governance policies.
"""
# doc-sync-skip

import os
import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import yaml

from pydantic import BaseModel, Field

# Import registry providers
from src.registry.factory import RegistryFactory
from src.registry.bootstrap import RegistryBootstrap
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider, BusinessTerm
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.models.kpi import KPI

# Import shared models
from src.agents.models.data_governance_models import (
    BusinessTermTranslationRequest,
    BusinessTermTranslationResponse,
    DataAccessValidationRequest,
    DataAccessValidationResponse,
    DataLineageRequest,
    DataLineageResponse,
    DataQualityCheckRequest,
    DataQualityCheckResponse,
    KPIDataProductMappingRequest,
    KPIDataProductMappingResponse,
    KPIDataProductMapping,
    DataAssetPathRequest,
    DataAssetPathResponse,
    KPIViewNameRequest,
    KPIViewNameResponse,
    SliceValidityCheckRequest,
    SliceValidityCheckResponse,
    SliceValidityDimensionResult,
    NotSliceableByEntry,
)
from src.agents.models.data_product_onboarding_models import (
    KPIRegistryUpdateRequest,
    KPIRegistryUpdateResponse,
    BusinessProcessMappingRequest,
    BusinessProcessMappingResponse,
)
from src.registry.models.kpi import KPI as RegistryKPI, NotSliceableByEntry as RegistryNotSliceableByEntry
from src.registry.models.business_process import BusinessProcess
from src.analysis.slice_validity import (
    check_completeness as _slice_validity_check_completeness,
    extract_components,
    profile as _slice_validity_profile,
)

# Setup logging
logger = logging.getLogger(__name__)


class A9_Data_Governance_Agent:
    """
    Agent9 Data Governance Agent
    
    Provides data governance capabilities, including business-to-technical term translation,
    data quality monitoring, access control, and compliance tracking.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Data Governance Agent with the provided configuration.
        
        Args:
            config: Configuration dictionary with required settings.
        """
        # Store the configuration
        self.config = config or {}
        
        # Set up agent properties
        self.name = "A9_Data_Governance_Agent"
        self.version = "0.1.0"
        
        # Initialize registry providers
        self.registry_factory = None
        self.business_glossary_provider = None
        self.kpi_provider = None
        self.data_product_provider = None
        self.data_product_agent = None  # Wired post-bootstrap by runtime._wire_governance_dependencies() — needed for check_slice_validity's multi-backend SQL execution.

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        self.glossary_path = config.get("glossary_path")
    
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Data_Governance_Agent":
        """
        Create a new instance of the Data Governance Agent.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            A9_Data_Governance_Agent instance
        """
        agent = cls(config)
        await agent.connect()
        return agent
    
    async def connect(self) -> bool:
        """Initialize connections to dependent services and registries."""
        try:
            # Initialize the registry factory
            self.registry_factory = RegistryFactory()
            
            # Get the Business Glossary Provider
            try:
                self.business_glossary_provider = self.registry_factory.get_provider("business_glossary")
                if not self.business_glossary_provider:
                    # If not available, create it
                    self.business_glossary_provider = BusinessGlossaryProvider(
                        glossary_path=self.glossary_path
                    )
            except Exception as e:
                self.logger.warning(f"Could not get Business Glossary Provider from registry factory: {e}")
                # Create a default provider
                self.business_glossary_provider = BusinessGlossaryProvider(
                    glossary_path=self.glossary_path
                )
                
            # Get the KPI Provider
            try:
                self.kpi_provider = self.registry_factory.get_kpi_provider()
                if not self.kpi_provider:
                    # Try alternate method
                    self.kpi_provider = self.registry_factory.get_provider("kpi")
            except Exception as e:
                self.logger.warning(f"Could not get KPI Provider from registry factory: {e}")

            # Get the Data Product Provider
            try:
                self.data_product_provider = self.registry_factory.get_data_product_provider()
                if not self.data_product_provider:
                    # Try alternate method
                    self.data_product_provider = self.registry_factory.get_provider("data_product")
            except Exception as e:
                self.logger.warning(f"Could not get Data Product Provider from registry factory: {e}")

            self.logger.info("Connected to dependent services and registries")
            return True
        except Exception as e:
            self.logger.error(f"Error connecting to services: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from dependent services."""
        try:
            # Nothing to disconnect for now
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from services: {e}")
            return False
    
    def _get_kpi_provider(self) -> Optional[KPIProvider]:
        """
        Get the KPI provider from the registry factory.
        
        Returns:
            KPIProvider instance or None if not available
        """
        try:
            registry_factory = RegistryFactory()
            return registry_factory.get_provider('kpi')
        except Exception as e:
            self.logger.error(f"Error getting KPI provider: {e}")
            return None
            
    
    
    async def translate_business_terms(
        self, request: BusinessTermTranslationRequest
    ) -> BusinessTermTranslationResponse:
        """
        Translate business terms to technical attribute names.
        
        Args:
            request: Contains business terms to translate and context
            
        Returns:
            Response with mapped terms, unmapped terms, and HITL flags
        """
        if not self.business_glossary_provider:
            self.logger.error("Business Glossary Provider not initialized")
            return BusinessTermTranslationResponse(
                resolved_terms={},
                unmapped_terms=request.business_terms,
                human_action_required=True,
                human_action_type="error",
                human_action_context={
                    "message": "Business Glossary Provider not available. Please contact your administrator."
                }
            )
        
        system = request.system or "duckdb"
        translation_results = self.business_glossary_provider.translate_business_terms(
            request.business_terms, system
        )
        
        # Process results
        resolved_terms = {}
        unmapped_terms = []
        
        for term, result in translation_results.items():
            if result["resolved"]:
                resolved_terms[term] = result["technical_name"]
            else:
                unmapped_terms.append(term)
        
        # Determine if human action is required
        human_action_required = len(unmapped_terms) > 0
        human_action_type = "clarification" if human_action_required else None
        human_action_context = None
        
        if human_action_required:
            human_action_context = {
                "unmapped_terms": unmapped_terms,
                "message": "Please clarify or map these terms before proceeding."
            }
        
        # Log the translation operation for audit
        self.logger.info(
            f"Business term translation: {len(resolved_terms)} resolved, "
            f"{len(unmapped_terms)} unmapped"
        )
        
        return BusinessTermTranslationResponse(
            resolved_terms=resolved_terms,
            unmapped_terms=unmapped_terms,
            human_action_required=human_action_required,
            human_action_type=human_action_type,
            human_action_context=human_action_context
        )

    async def resolve_dimension_label(self, field_name: str, client_id: Optional[str] = None) -> Optional[str]:
        """Reverse translation: a raw technical dimension/column name (e.g.
        'customer_region', from a data product contract's dimension_semantics
        list) to its governed glossary display term (e.g. 'Customer Region').

        Added 2026-08-24 so DA's dimensional breakdown (the Variance Breakdown
        exhibit) can show a governed business label instead of either the raw
        field name or an ungoverned client-side mechanical transform. An
        enrichment, not a gate: returns None (never raises) when the glossary
        doesn't yet carry an entry for this field — the caller falls back to
        a plain mechanical Title Case transform in that case, same discipline
        as translate_business_terms' unmapped_terms path, just non-blocking
        since this is display-only, not a governance decision.
        """
        if not self.business_glossary_provider or not field_name:
            return None
        try:
            term = self.business_glossary_provider.get_by_technical_name(field_name, client_id=client_id)
            return term.name if term else None
        except Exception as e:
            self.logger.debug(f"resolve_dimension_label failed for '{field_name}' (non-fatal): {e}")
            return None

    async def validate_data_access(
        self, request: DataAccessValidationRequest
    ) -> DataAccessValidationResponse:
        """
        Validate data access permissions for a principal.

        Tenant isolation: when client_id is provided, the principal may only access
        data products belonging to the same client. If client_id is None (legacy/test),
        access is allowed with a warning.

        Args:
            request: Contains principal_id, data_product_id, access_type, and client_id

        Returns:
            Response with access validation result
        """
        principal_client = getattr(request, 'client_id', None)

        # Resolve the data product's client_id from the registry
        dp_client = None

        # Tier 1: Look up from data product provider directly
        if self.data_product_provider:
            dp = self.data_product_provider.get(request.data_product_id)
            if dp:
                dp_client = getattr(dp, 'client_id', None)

        # Tier 2 fallback: Look up from KPI provider (in case data product isn't in registry yet)
        if not dp_client and self.kpi_provider:
            for kpi in self.kpi_provider.get_all():
                dp_id = self._get_data_product_id_for_kpi(kpi)
                if dp_id == request.data_product_id:
                    dp_client = getattr(kpi, 'client_id', None)
                    break

        # Tenant isolation check: strict match when principal has a client_id
        if principal_client:
            if dp_client and principal_client != dp_client:
                # Cross-client access forbidden (only when data product client is known)
                self.logger.warning(
                    f"Access DENIED: principal={request.principal_id} (client={principal_client}) "
                    f"attempted to access dp={request.data_product_id} (client={dp_client})"
                )
                return DataAccessValidationResponse(
                    allowed=False,
                    reason=f"Client mismatch: principal belongs to '{principal_client}', "
                           f"data product belongs to '{dp_client}'"
                )
            elif not dp_client:
                # Principal is scoped but data product has no client_id in the registry.
                # This means the data product was not seeded with a client_id — deny to
                # prevent silent cross-client leaks. Fix by re-seeding the data product
                # with the correct client_id.
                self.logger.warning(
                    f"Access DENIED: scoped principal={request.principal_id} (client={principal_client}) "
                    f"attempted to access dp={request.data_product_id} which has no client_id in registry"
                )
                return DataAccessValidationResponse(
                    allowed=False,
                    reason=f"Data product '{request.data_product_id}' is missing client_id in registry — "
                           f"re-seed with client_id='{principal_client}' to grant access"
                )
        else:
            # No principal_client — admin/system context, allow regardless of data product client_id
            self.logger.info(
                f"Access ALLOWED (admin/unscoped): principal={request.principal_id} "
                f"dp={request.data_product_id} dp_client={dp_client}"
            )
            return DataAccessValidationResponse(
                allowed=True,
                reason=f"Access granted (unscoped principal, system context)"
            )

        self.logger.info(
            f"Access ALLOWED: principal={request.principal_id} dp={request.data_product_id} "
            f"client={principal_client}"
        )
        return DataAccessValidationResponse(
            allowed=True,
            reason=f"Access granted for client '{principal_client}'"
        )
    
    async def get_data_lineage(
        self, request: DataLineageRequest
    ) -> DataLineageResponse:
        """
        Get data lineage for a data product.
        
        Args:
            request: Contains data_product_id
            
        Returns:
            Response with data lineage information
        """
        # For MVP, return minimal lineage info
        # In production, this would query actual lineage registry
        
        return DataLineageResponse(
            data_product_id=request.data_product_id,
            lineage_nodes=[],
            lineage_edges=[]
        )
    
    async def check_data_quality(
        self, request: DataQualityCheckRequest
    ) -> DataQualityCheckResponse:
        """
        Check data quality for a data product.
        
        Args:
            request: Contains data_product_id and quality dimensions
            
        Returns:
            Response with data quality metrics
        """
        # For MVP, return dummy quality metrics
        # In production, this would run actual quality checks
        
        return DataQualityCheckResponse(
            data_product_id=request.data_product_id,
            quality_metrics={
                "completeness": 0.98,
                "accuracy": 0.95,
                "timeliness": 1.0
            },
            issues=[]
        )
        
    async def map_kpis_to_data_products(
        self, request: KPIDataProductMappingRequest
    ) -> KPIDataProductMappingResponse:
        """
        Map KPIs to data products.
        
        Args:
            request: Contains KPI names to map and context
            
        Returns:
            Response with KPI to data product mappings
        """
        if not self.kpi_provider:
            self.logger.error("KPI Provider not initialized")
            return KPIDataProductMappingResponse(
                mappings=[],
                unmapped_kpis=request.kpi_names,
                human_action_required=True,
                human_action_context={
                    "message": "KPI Provider not available. Please contact your administrator."
                }
            )
        
        mappings = []
        unmapped_kpis = []
        
        # Get KPIs from the registry, scoped by client_id when provided
        try:
            client_id = getattr(request, 'client_id', None)
            if client_id and hasattr(self.kpi_provider, 'get_by_client'):
                all_kpis = self.kpi_provider.get_by_client(client_id) or []
            else:
                all_kpis = self.kpi_provider.get_all() or []
                if client_id:
                    all_kpis = [k for k in all_kpis if not getattr(k, 'client_id', None) or getattr(k, 'client_id', None) == client_id]
            kpi_dict = {kpi.name: kpi for kpi in all_kpis if hasattr(kpi, 'name')}
            
            for kpi_name in request.kpi_names:
                if kpi_name in kpi_dict:
                    kpi = kpi_dict[kpi_name]
                    data_product_id = self._get_data_product_id_for_kpi(kpi)
                    technical_name = self._get_technical_name_for_kpi(kpi)
                    
                    mappings.append(KPIDataProductMapping(
                        kpi_name=kpi_name,
                        data_product_id=data_product_id,
                        technical_name=technical_name,
                        metadata=self._get_kpi_metadata(kpi)
                    ))
                else:
                    unmapped_kpis.append(kpi_name)
        except Exception as e:
            self.logger.error(f"Error mapping KPIs to data products: {e}")
            return KPIDataProductMappingResponse(
                mappings=[],
                unmapped_kpis=request.kpi_names,
                human_action_required=True,
                human_action_context={
                    "message": f"Error mapping KPIs: {str(e)}"
                }
            )
        
        # Determine if human action is required
        human_action_required = len(unmapped_kpis) > 0
        human_action_context = None
        
        if human_action_required:
            human_action_context = {
                "unmapped_kpis": unmapped_kpis,
                "message": "Please map these KPIs to data products before proceeding."
            }
        
        # Log the mapping operation for audit
        self.logger.info(
            f"KPI to data product mapping: {len(mappings)} mapped, "
            f"{len(unmapped_kpis)} unmapped"
        )
        
        return KPIDataProductMappingResponse(
            mappings=mappings,
            unmapped_kpis=unmapped_kpis,
            human_action_required=human_action_required,
            human_action_context=human_action_context
        )

    async def register_kpi_metadata(
        self, request: KPIRegistryUpdateRequest
    ) -> KPIRegistryUpdateResponse:
        """Register or update KPI definitions in the governance registry."""

        request_id = request.request_id

        if not self.kpi_provider:
            self.logger.error("KPI Provider not initialized")
            return KPIRegistryUpdateResponse.error(
                request_id=request_id,
                error_message="KPI provider unavailable",
                updated_count=0,
                duplicated_ids=[entry.kpi_id for entry in request.kpis],
                registry_path=None,
            )

        updated_count = 0
        duplicated_ids: List[str] = []

        for entry in request.kpis:
            try:
                payload = entry.model_dump()
                payload.setdefault("data_product_id", request.data_product_id)
                if entry.thresholds:
                    thresholds = []
                    for th in entry.thresholds:
                        thresholds.append(
                            {
                                "comparison_type": th.type,
                                "green_threshold": th.value,
                                "yellow_threshold": None,
                                "red_threshold": None,
                                "inverse_logic": th.comparator in {"<=", "<"},
                            }
                        )
                    payload["thresholds"] = thresholds

                registry_kpi = RegistryKPI(**payload)

                existing = self.kpi_provider.get(registry_kpi.id)
                if existing and not request.overwrite_existing:
                    duplicated_ids.append(registry_kpi.id)
                    continue

                await self.kpi_provider.upsert(registry_kpi)
                updated_count += 1
            except Exception as err:
                self.logger.error(f"Failed to register KPI {entry.kpi_id}: {err}")
                duplicated_ids.append(entry.kpi_id)

        registry_path = getattr(self.kpi_provider, "source_path", None)

        return KPIRegistryUpdateResponse.success(
            request_id=request_id,
            updated_count=updated_count,
            duplicated_ids=duplicated_ids,
            registry_path=registry_path,
        )

    async def map_business_process(
        self, request: BusinessProcessMappingRequest
    ) -> BusinessProcessMappingResponse:
        """Associate KPIs with governed business processes."""

        request_id = request.request_id

        try:
            if not self.registry_factory:
                self.registry_factory = RegistryFactory()

            bp_provider = self.registry_factory.get_business_process_provider()
            if not bp_provider:
                # Same shape as the principal-provider startup race fixed Aug 2026
                # (a9_principal_context_agent.py): don't manufacture a flat,
                # non-tenant-aware provider on an empty factory slot — that's how
                # this codebase already had a cross-tenant leak once. Self-heal via
                # RegistryBootstrap first (idempotent, re-verifies what's missing);
                # only degrade to the flat fallback — and log it as a real failure,
                # not a silent substitution — if it's still empty afterward.
                try:
                    await RegistryBootstrap.initialize()
                except Exception as e:
                    self.logger.warning(f"RegistryBootstrap.initialize() failed: {e}")
                bp_provider = self.registry_factory.get_business_process_provider()
                if not bp_provider:
                    self.logger.error(
                        "No business_process provider after RegistryBootstrap.initialize() — "
                        "using a local, unregistered, non-tenant-aware fallback for this call only."
                    )
                    bp_provider = BusinessProcessProvider()

            applied: List[Any] = []
            skipped: List[str] = []

            # Ensure provider is loaded lazily
            try:
                if hasattr(bp_provider, "load"):
                    await bp_provider.load()
            except Exception:
                pass

            for mapping in request.mappings:
                try:
                    existing = bp_provider.get(mapping.process_id)
                    if existing and not request.overwrite_existing:
                        skipped.append(mapping.process_id)
                        continue

                    payload = {
                        "id": mapping.process_id,
                        "name": mapping.process_id.replace("_", " ").title(),
                        "domain": "Finance",
                        "description": mapping.notes or "Auto-generated process mapping",
                        "kpi_ids": mapping.kpi_ids,
                        "compliance_policies": mapping.compliance_policies,
                    }

                    bp_model = BusinessProcess(**payload)
                    await bp_provider.upsert(bp_model)
                    applied.append(mapping)
                except Exception as err:
                    self.logger.error(
                        f"Failed to map business process {mapping.process_id}: {err}"
                    )
                    skipped.append(mapping.process_id)

            registry_path = getattr(bp_provider, "source_path", None)

            return BusinessProcessMappingResponse.success(
                request_id=request_id,
                applied_mappings=applied,
                skipped_process_ids=skipped,
                registry_path=registry_path,
            )
        except Exception as err:
            self.logger.error(f"Business process mapping error: {err}")
            return BusinessProcessMappingResponse.error(
                request_id=request_id,
                error_message=str(err),
                applied_mappings=[],
                skipped_process_ids=[m.process_id for m in request.mappings],
                registry_path=None,
            )
    
    async def get_view_name_for_kpi(
        self, request: KPIViewNameRequest
    ) -> KPIViewNameResponse:
        """
        Get the view name for a KPI.
        
        Args:
            request: KPIViewNameRequest containing the KPI name and context
            
        Returns:
            KPIViewNameResponse with the view name
        """
        try:
            kpi_name = request.kpi_name
            # Get the KPI provider
            kpi_provider = self._get_kpi_provider()
            if not kpi_provider:
                self.logger.error("KPI provider not available")
                return KPIViewNameResponse(
                    kpi_name=kpi_name,
                    view_name="unknown",
                    data_product_id=None
                )
            
            # Get the KPI definition
            kpi = None

            # 1) Try direct provider lookup (often keyed by KPI id)
            try:
                kpi = kpi_provider.get(kpi_name)
            except Exception:
                kpi = None

            # 2) Try normalized id derived from display name (e.g., "Gross Revenue" -> "gross_revenue")
            if not kpi:
                try:
                    raw = str(kpi_name or "").strip().lower()
                    raw = raw.replace("-", " ")
                    parts = [p for p in raw.split() if p]
                    normalized_id = "_".join(parts)
                    if normalized_id:
                        kpi = kpi_provider.get(normalized_id)
                except Exception:
                    kpi = None

            # 3) Fallback: scan all KPIs and match by display name (case-insensitive)
            if not kpi:
                try:
                    _req_client = getattr(request, 'client_id', None) or (request.context or {}).get('client_id') if request else None
                    all_kpis = kpi_provider.get_all() if hasattr(kpi_provider, "get_all") else []
                    target = str(kpi_name or "").strip().lower()
                    for candidate in (all_kpis or []):
                        try:
                            cand_name = getattr(candidate, "name", None)
                            if not (isinstance(cand_name, str) and cand_name.strip().lower() == target):
                                continue
                            _cand_client = getattr(candidate, 'client_id', None)
                            if _req_client and _cand_client and _cand_client != _req_client:
                                continue
                            kpi = candidate
                            break
                        except Exception:
                            continue
                except Exception:
                    kpi = None
            
            if kpi:
                data_product_id = self._get_data_product_id_for_kpi(kpi)
                view_name = self._get_view_name_for_kpi(kpi)
                
                return KPIViewNameResponse(
                    kpi_name=kpi_name,
                    view_name=view_name,
                    data_product_id=data_product_id
                )
            else:
                self.logger.warning(f"KPI {kpi_name} not found in registry")
                return KPIViewNameResponse(
                    kpi_name=kpi_name,
                    view_name="unknown",
                    data_product_id=None
                )
        except Exception as e:
            # Use request.kpi_name to avoid UnboundLocalError if exception occurs before kpi_name is assigned
            error_kpi_name = getattr(request, 'kpi_name', 'unknown')
            self.logger.error(f"Error getting view name for KPI {error_kpi_name}: {e}")
            return KPIViewNameResponse(
                kpi_name=error_kpi_name,
                view_name="unknown",
                data_product_id=None
            )
        

    def _get_data_product_id_for_kpi(self, kpi: KPI) -> str:
        """
        Get the data product ID for a KPI.
        
{{ ... }}
        Args:
            kpi: KPI object
            
        Returns:
            Data product ID
        """
        # Try to get data_product_id attribute
        if hasattr(kpi, 'data_product_id') and kpi.data_product_id:
            return kpi.data_product_id
        
        # Try to get data_product attribute
        if hasattr(kpi, 'data_product') and kpi.data_product:
            return kpi.data_product
        
        # Default to FI_Star_Schema for Finance KPIs
        return "FI_Star_Schema"
    
    def _get_technical_name_for_kpi(self, kpi: KPI) -> str:
        """
        Get the technical name for a KPI.
        
        Args:
            kpi: KPI object
            
        Returns:
            Technical name
        """
        # Try to get technical_name attribute
        if hasattr(kpi, 'technical_name') and kpi.technical_name:
            return kpi.technical_name
        
        # Default to KPI name with spaces replaced by underscores
        if hasattr(kpi, 'name'):
            return kpi.name.lower().replace(' ', '_')
        
        return "unknown"
    
    def _get_view_name_for_kpi(self, kpi: KPI) -> str:
        """
        Get the view name for a KPI.
        
        Args:
            kpi: KPI object
            
        Returns:
            View name
        """
        # 1) Explicit attribute wins
        if hasattr(kpi, 'view_name') and kpi.view_name:
            return kpi.view_name
        # 2) Metadata-defined view_name
        if hasattr(kpi, 'metadata') and isinstance(getattr(kpi, 'metadata'), dict):
            vn = kpi.metadata.get('view_name')
            if vn:
                return vn
        # 3) If KPI maps to FI_Star_Schema, use canonical FI_Star_View
        try:
            dp_id = self._get_data_product_id_for_kpi(kpi)
            if isinstance(dp_id, str) and dp_id.strip().lower() == 'fi_star_schema':
                return 'FI_Star_View'
        except Exception:
            pass
        # 4) No synthetic view fallback (PRD-aligned: do not invent view names)
        return "unknown"
    
    def _get_kpi_metadata(self, kpi: KPI) -> Dict[str, Any]:
        """
        Get metadata for a KPI.
        
        Args:
            kpi: KPI object
            
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        # Add common metadata fields
        if hasattr(kpi, 'description'):
            metadata['description'] = kpi.description
        
        if hasattr(kpi, 'unit'):
            metadata['unit'] = kpi.unit
        
        if hasattr(kpi, 'business_processes'):
            metadata['business_processes'] = kpi.business_processes
        
        if hasattr(kpi, 'dimensions'):
            metadata['dimensions'] = kpi.dimensions
        
        if hasattr(kpi, 'thresholds'):
            metadata['thresholds'] = kpi.thresholds
        
        if hasattr(kpi, 'positive_trend_is_good'):
            metadata['positive_trend_is_good'] = kpi.positive_trend_is_good
        
        return metadata

    # --- Slice validity (docs/architecture/kpi_semantic_contract.md §4) ---
    async def check_slice_validity(
        self, request: SliceValidityCheckRequest
    ) -> SliceValidityCheckResponse:
        """Run the slice-validity check for one ratio KPI, persist the result.

        Triggered by a human — the onboarding Day 6 panel or Settings ->
        Maintenance -> Slice Validity — never automatically. Advisory only:
        nothing downstream reads the persisted not_sliceable_by to gate
        anything (see that field's docstring on src.registry.models.kpi.KPI);
        this method's only effect is writing three fields a human can read.

        Non-fatal by design, matching this agent's established convention —
        get_view_name_for_kpi returns "unknown" rather than raising,
        register_kpi_metadata returns .error() rather than raising. A
        resolution failure here is a diagnostic result to display, not a
        workflow step anything else depends on.

        Routes the profiling query through A9_Data_Product_Agent.execute_sql()
        (multi-backend) rather than a BigQuery-only client, and passes
        data_product_id explicitly so execute_sql's Tier-1 registry-based
        routing engages regardless of whether the query text itself is
        backend-detectable — Snowflake and DuckDB queries are unquoted by
        convention (src/analysis/slice_validity.py's _quote_view), so
        execute_sql's Tier-2 regex fallback (backtick -> BigQuery,
        bracket -> SQL Server) would not recognise them.
        """
        kpi_id = request.kpi_id
        client_id = request.client_id

        def _error(msg: str, cross_component_results=None, completeness_results=None,
                   not_sliceable_by=None, components_used=None) -> SliceValidityCheckResponse:
            self.logger.error(f"[check_slice_validity] {kpi_id}/{client_id}: {msg}")
            return SliceValidityCheckResponse(
                kpi_id=kpi_id,
                client_id=client_id,
                status="error",
                error_message=msg,
                cross_component_results=cross_component_results or [],
                completeness_results=completeness_results or [],
                not_sliceable_by=not_sliceable_by or [],
                components_used=components_used or [],
            )

        if not self.data_product_agent:
            return _error(
                "A9_Data_Product_Agent not wired — check runtime._wire_governance_dependencies()"
            )

        provider = self.kpi_provider or self._get_kpi_provider()
        if not provider:
            return _error("KPI provider unavailable")

        # Found live (2026-08-15): a bare provider.get(kpi_id) is genuinely
        # unsafe, not just theoretically so — two real clients (lubricants,
        # brookshire_brothers) both use the id "gross_margin_pct", and a bare
        # lookup returned brookshire_brothers' record for a lubricants
        # request. DatabaseRegistryProvider.get()'s own docstring says
        # exactly this: "a bare-id linear scan... matches the first cached
        # item with the given id regardless of tenant... callers that need a
        # specific tenant's record MUST pass client_id." Pass it. The
        # TypeError fallback covers the plain in-memory KPIProvider (used in
        # some dev/test contexts), whose .get() signature doesn't accept the
        # kwarg — the STRICT MATCH re-check below still applies either way,
        # so an unscoped result can never leak through.
        try:
            try:
                kpi = provider.get(kpi_id, client_id=client_id)
            except TypeError:
                kpi = provider.get(kpi_id)
        except Exception as exc:
            return _error(f"KPI lookup failed: {exc}")
        if kpi is None or getattr(kpi, "client_id", None) != client_id:
            return _error(f"KPI '{kpi_id}' not found for client '{client_id}'")

        dimensions = request.dimensions or [d.field for d in (kpi.dimensions or [])]
        if not dimensions:
            return _error(
                f"No dimensions to check for '{kpi_id}' — pass request.dimensions "
                "or set KPI.dimensions in the registry"
            )

        # Auto-derive from the KPI's own sql_query when not given explicitly —
        # required to run this against every KPI (42 across the three seeded
        # clients, 26 of them a plain single-component sum) rather than only
        # the compound ones a caller happened to specify components for by
        # hand. The query already encodes the answer correctly by
        # construction; extracting it is more reliable than asking twice.
        # extract_components() also resolves WHICH column — a real subset of
        # KPIs (product_sales_revenue, service_revenue, base_oil_cost,
        # distribution_cost — found live 2026-08-15) filter on
        # account_category, not account_type, and have no account_type
        # filter anywhere in their sql_query.
        if request.components:
            components = request.components
            measure_column = request.measure_column or "account_type"
        else:
            measure_column, components = extract_components(kpi.sql_query)
            if request.measure_column:
                measure_column = request.measure_column
        if not components:
            return _error(
                f"Could not determine which components '{kpi_id}' is built from — "
                "its sql_query doesn't filter by account_type or account_category, "
                "and none were given explicitly"
            )

        data_product_id = self._get_data_product_id_for_kpi(kpi)
        source_system = "bigquery"
        if self.data_product_provider and data_product_id:
            try:
                try:
                    dp = self.data_product_provider.get(data_product_id, client_id=client_id)
                except TypeError:
                    dp = self.data_product_provider.get(data_product_id)
                if dp is not None and getattr(dp, "client_id", None) == client_id:
                    source_system = getattr(dp, "source_system", None) or "bigquery"
            except Exception:
                pass  # keep the bigquery default rather than fail the whole check

        # Found live (2026-08-15): _get_view_name_for_kpi() returns the bare
        # KPI.view_name ("LubricantsStarSchemaView"), not the fully-qualified
        # `project.dataset.view` reference. execute_sql()'s BigQuery routing
        # is Tier-2 REGEX detection of that exact fully-qualified, backtick-
        # quoted shape in the SQL text — unlike Snowflake, which genuinely
        # gets Tier-1 data_product_id-based routing inside execute_sql, BOTH
        # BigQuery and SQL Server routing there fall back to pattern-matching
        # the query text itself (CLAUDE.md's Tier-1/Tier-2 description is the
        # intended design; the live execute_sql code only implements it for
        # Snowflake). A backtick-wrapped BARE name has no dots, never matches
        # the pattern, and the query silently fell through to the DuckDB
        # manager, which doesn't understand backtick quoting at all —
        # confirmed live via a DuckDB "Parser Error: syntax error at or near
        # backtick" on every dimension, each one silently skipped by
        # profile()'s per-dimension error handling rather than surfacing.
        #
        # Fix: for bigquery specifically, pull the ALREADY-CORRECT
        # fully-qualified reference straight out of the KPI's own sql_query —
        # the exact same regex execute_sql/generate_sql_for_kpi use to detect
        # it, reusing rather than re-deriving. Guaranteed correct by
        # construction: it's copied from a query already proven to run.
        view = self._get_view_name_for_kpi(kpi)
        if source_system == "bigquery":
            _bq_ref = re.search(r'`[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+`', kpi.sql_query or "")
            if _bq_ref:
                view = _bq_ref.group(0).strip("`")
        if not view or view == "unknown":
            return _error(f"Could not resolve a view for KPI '{kpi_id}' — no view_name set")

        async def _run_query(sql: str) -> List[Dict[str, Any]]:
            result = await self.data_product_agent.execute_sql(sql, data_product_id=data_product_id)
            if not isinstance(result, dict) or not result.get("success"):
                raise RuntimeError((result or {}).get("message") or "execute_sql failed")
            return result.get("rows") or []

        # Completeness applies to every KPI, one component or many — always run
        # it. Cross-component coverage only means something with 2+ components
        # to compare; a single-component KPI (26 of 42 across the seeded
        # clients) has nothing on the other side of that comparison, so
        # skipping it isn't a shortcut, it's the check correctly not claiming
        # to measure something it structurally can't.
        try:
            completeness_verdicts = await _slice_validity_check_completeness(
                _run_query, view, measure_column, components, dimensions,
                request.value_column, request.version_filter, source_system,
            )
            cross_component_verdicts = []
            if len(components) >= 2:
                cross_component_verdicts = await _slice_validity_profile(
                    _run_query, view, measure_column, components,
                    dimensions, request.version_filter, source_system,
                )
        except Exception as exc:
            return _error(f"Slice-validity profiling failed: {exc}", components_used=components)

        completeness_results = [
            SliceValidityDimensionResult(dimension=v.dimension, counts=v.counts, coverage=v.coverage, verdict=v.verdict)
            for v in completeness_verdicts
        ]
        cross_component_results = [
            SliceValidityDimensionResult(dimension=v.dimension, counts=v.counts, coverage=v.coverage, verdict=v.verdict)
            for v in cross_component_verdicts
        ]
        # UNION of dimensions failing EITHER check — "not sliceable by X"
        # should mean don't trust it for any reason, not just the reason the
        # first check happened to look for. One structured entry per denied
        # dimension (§4), not a bare name: reason_class defaults to
        # 'pipeline_gap' (profiling alone cannot tell a permanent structural
        # fact about the CLIENT's business from a fixable completeness gap
        # in the CLIENT's own source data/ETL — this is never an Agent9
        # code defect, Agent9 doesn't own the client's warehouse pipeline.
        # §4.3's "prefer loud" means treating an unclassified gap as worth
        # flagging to whoever owns that pipeline until a human overrides it
        # via source='declared', not assuming it's permanent by default).
        # When a dimension fails both checks, the completeness note wins —
        # arbitrary but deterministic, and completeness is the check with a
        # value column to quote a concrete ratio from.
        _invalid_by_dim: Dict[str, Any] = {}
        for v in cross_component_verdicts:
            if v.verdict == "INVALID":
                _invalid_by_dim[v.dimension] = (
                    f"Cross-component coverage {v.coverage:.0%} — components reach different "
                    f"sets of {v.dimension} values ({v.counts})"
                )
        for v in completeness_verdicts:
            if v.verdict == "INVALID":
                _c = v.counts or {}
                _invalid_by_dim[v.dimension] = (
                    f"Completeness {v.coverage:.0%} — {_c.get('complete_rows', '?')}/"
                    f"{_c.get('total_rows', '?')} rows carry a {v.dimension} value"
                )
        not_sliceable_by = [
            NotSliceableByEntry(dimension=dim, reason_class="pipeline_gap", source="derived", note=note)
            for dim, note in sorted(_invalid_by_dim.items())
        ]
        # Persisted per dimension, both sub-checks side by side so a human
        # reading the record later can see WHICH question failed, not just
        # that one did.
        details: Dict[str, Any] = {}
        for v in completeness_verdicts:
            details.setdefault(v.dimension, {})["completeness"] = {
                "counts": v.counts, "coverage": v.coverage, "verdict": v.verdict,
            }
        for v in cross_component_verdicts:
            details.setdefault(v.dimension, {})["cross_component"] = {
                "counts": v.counts, "coverage": v.coverage, "verdict": v.verdict,
            }
        checked_at = datetime.now(timezone.utc)

        try:
            # Re-typed through the REGISTRY-layer NotSliceableByEntry explicitly —
            # model_copy(update=...) does not validate/coerce, so leaving the
            # agent-layer instances in place would leave `updated_kpi` holding a
            # field typed List[registry.NotSliceableByEntry] but populated with
            # agent.NotSliceableByEntry instances. Same shape, still worth being
            # exact about which class actually owns the field.
            _registry_not_sliceable_by = [
                RegistryNotSliceableByEntry(**e.model_dump()) for e in not_sliceable_by
            ]
            updated_kpi = kpi.model_copy(update={
                "not_sliceable_by": _registry_not_sliceable_by,
                "slice_validity_details": details,
                "slice_validity_checked_at": checked_at,
            })
            # DatabaseRegistryProvider.upsert()/register() logs a DB failure
            # and returns False rather than raising — found live 2026-08-15,
            # where a serialization bug (now fixed in database_provider.py)
            # failed the write and this method still returned status="success"
            # because no exception ever surfaced. `is False` specifically:
            # some provider stand-ins (tests, alternate implementations) may
            # legitimately return None for "no boolean signal available",
            # which must not be treated as a failure.
            persisted = await provider.upsert(updated_kpi)
            if persisted is False:
                raise RuntimeError("registry write reported failure (see provider logs)")
        except Exception as exc:
            # The check DID run — return what it found, but status=error and no
            # checked_at, because nothing durable was recorded. Returning
            # status=success here would show a fresh timestamp that reverts to
            # stale on the next page load, which is the exact false-confidence
            # failure mode this feature exists to avoid, just moved one step
            # earlier.
            return _error(
                f"Check ran but failed to persist: {exc}",
                cross_component_results=cross_component_results,
                completeness_results=completeness_results,
                not_sliceable_by=not_sliceable_by,
                components_used=components,
            )

        return SliceValidityCheckResponse(
            kpi_id=kpi_id,
            client_id=client_id,
            status="success",
            cross_component_results=cross_component_results,
            completeness_results=completeness_results,
            components_used=components,
            not_sliceable_by=not_sliceable_by,
            checked_at=checked_at,
        )

    # --- Registry Integrity Validation (per PRD) ---
    def _contract_path(self) -> str:
        """
        Resolve contract path from the canonical registry_references location.
        This ensures single source of truth for data product contracts.
        """
        try:
            # Canonical path in registry_references (single source of truth)
            canonical = "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"
            if os.path.exists(canonical):
                return canonical
            
            # Try from project root
            here = os.path.dirname(__file__)
            proj_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
            abs_canonical = os.path.join(proj_root, canonical)
            if os.path.exists(abs_canonical):
                return abs_canonical
            
            return canonical
        except Exception:
            return "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"

    def _load_exposed_columns(self, view_name: str = "FI_Star_View") -> Set[str]:
        """Load contract-exposed columns for a given view (labels)."""
        try:
            cpath = self._contract_path()
            if not os.path.exists(cpath):
                return set()
            with open(cpath, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            views = (doc or {}).get("views", [])
            target = None
            vn_key = (view_name or "").strip().lower()
            for v in views:
                if isinstance(v, dict) and str(v.get("name", "")).strip().lower() == vn_key:
                    target = v; break
            if target is None:
                for v in views:
                    if isinstance(v, dict) and v.get("name") == "FI_Star_View":
                        target = v; break
            if not isinstance(target, dict):
                return set()
            llm_profile = target.get("llm_profile", {}) or {}
            cols = llm_profile.get("exposed_columns") or []
            out: Set[str] = set()
            for c in cols:
                try:
                    s = str(c).strip()
                    if s.startswith('"') and s.endswith('"') and len(s) > 1:
                        s = s[1:-1]
                    if s:
                        out.add(s)
                except Exception:
                    continue
            return out
        except Exception:
            return set()

    async def validate_registry_integrity(self, view_name: str = "FI_Star_View") -> Dict[str, Any]:
        """
        Validate cross-registry alignment per PRD:
        - Glossary→Contract: duckdb mappings must be contract labels
        - KPI→Contract: KPI dimensions must be labels or glossary-resolvable
        - Principal defaults→Contract: default filters must be labels or glossary-resolvable (if provider present)
        Returns a dict report with issues and summary counts. Lightweight; safe for dev/test.
        """
        issues: List[Dict[str, Any]] = []
        summary: Dict[str, int] = {"glossary_mismatch": 0, "kpi_mismatch": 0, "principal_mismatch": 0}

        # 1) Load authoritative labels from contract
        labels = self._load_exposed_columns(view_name) or set()

        # 2) Glossary→Contract check
        try:
            if self.business_glossary_provider:
                terms = getattr(self.business_glossary_provider, 'terms', {}) or {}
                # terms is dict name->BusinessTerm; iterate values
                for term_obj in (terms.values() if isinstance(terms, dict) else []):
                    try:
                        tm = getattr(term_obj, 'technical_mappings', {}) or {}
                        mapped = tm.get('duckdb')
                        if isinstance(mapped, str) and mapped.strip():
                            m = mapped.strip().strip('"')
                            if m not in labels:
                                issues.append({"type": "glossary_mismatch", "term": getattr(term_obj, 'name', None), "mapped": mapped, "message": "Glossary mapping not in contract exposed_columns"})
                                summary["glossary_mismatch"] += 1
                    except Exception:
                        continue
        except Exception:
            issues.append({"type": "glossary_error", "message": "Failed to load glossary for validation"})

        # 3) KPI→Contract check
        try:
            provider = self.kpi_provider or self._get_kpi_provider()
            all_kpis = provider.get_all() if provider else []
            for kpi in (all_kpis or []):
                try:
                    dims = []
                    if hasattr(kpi, 'dimensions') and isinstance(kpi.dimensions, list):
                        for d in kpi.dimensions:
                            if isinstance(d, dict) and 'name' in d:
                                dims.append(str(d['name']))
                            elif isinstance(d, str):
                                dims.append(d)
                    for dim in dims:
                        dn = str(dim).strip().strip('"')
                        if not dn:
                            continue
                        if dn in labels:
                            continue
                        # Try glossary resolution
                        mapped = None
                        try:
                            mapped = self.business_glossary_provider.get_technical_mapping(dn, system='duckdb') if self.business_glossary_provider else None
                        except Exception:
                            mapped = None
                        if not isinstance(mapped, str) or mapped.strip().strip('"') not in labels:
                            issues.append({"type": "kpi_mismatch", "kpi": getattr(kpi, 'name', None), "dimension": dim, "message": "KPI dimension not a contract label or resolvable via glossary"})
                            summary["kpi_mismatch"] += 1
                except Exception:
                    continue
        except Exception:
            issues.append({"type": "kpi_error", "message": "Failed to load KPI registry for validation"})

        # 4) Principal defaults→Contract (optional)
        # Use registry factory to attempt principal provider lookup
        pp = None
        try:
            rf = self.registry_factory or RegistryFactory()
            pp = rf.get_principal_profile_provider()
        except Exception:
            pp = None
        if pp:
            try:
                profiles = pp.get_all() or []
            except Exception:
                profiles = []
            for prof in profiles:
                defaults = getattr(prof, 'default_filters', {}) or {}
                for key in list(defaults.keys()):
                    k = str(key).strip().strip('"')
                    if not k:
                        continue
                    if k in labels:
                        continue
                    mapped = None
                    try:
                        mapped = self.business_glossary_provider.get_technical_mapping(k, system='duckdb') if self.business_glossary_provider else None
                    except Exception:
                        mapped = None
                    if not isinstance(mapped, str) or mapped.strip().strip('"') not in labels:
                        issues.append({"type": "principal_mismatch", "principal": getattr(prof, 'id', None), "filter_key": key, "message": "Principal default filter not a contract label or resolvable via glossary"})
                        summary["principal_mismatch"] += 1

        ok = (summary["glossary_mismatch"] == 0 and summary["kpi_mismatch"] == 0 and summary["principal_mismatch"] == 0)
        return {"success": ok, "issues": issues, "summary": summary, "view_name": view_name, "label_count": len(labels)}


    async def compute_and_persist_top_dimensions(
        self,
        data_product_agent,
        timeframe: Optional[str] = None,
        max_dimensions_per_kpi: int = 5,
        enrichment_output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute top "valuable" dimensions per KPI by executing grouped aggregates via the Data Product Agent
        and persist results to a non-destructive enrichment YAML next to the KPI registry.

        The enrichment file (kpi_enrichment.yaml) stores:
          top_dimensions:
            <KPI Name>: "Dim A, Dim B, Dim C"
          dimension_scores:
            <KPI Name>: "{\"Dim A\": 0.62, \"Dim B\": 0.55}"

        Notes:
        - Uses a simple top-3 share metric (sum of top 3 group totals / sum of all groups) per dimension.
        - Does not modify the primary KPI registry; KPIProvider will merge this file on load.
        - Keeps patterns simple and leverages existing agents.
        """
        try:
            if not data_product_agent:
                return {"success": False, "message": "Data Product Agent is required", "written": False}

            # Locate KPI registry directory to place enrichment file alongside it
            kp = self.kpi_provider or self._get_kpi_provider()
            if kp and getattr(kp, "source_path", None):
                base_dir = os.path.dirname(kp.source_path)
            else:
                # Fallback to default registry path convention
                here = os.path.dirname(__file__)
                base_dir = os.path.abspath(os.path.join(here, "..", "..", "registry", "kpi"))
            out_path = enrichment_output_path or os.path.join(base_dir, "kpi_enrichment.yaml")

            # Helper: load candidate dimensions from the contract (label-based)
            def _contract_dims(limit: int = 50) -> List[str]:
                dims: List[str] = []
                try:
                    cpath = self._contract_path()
                    if not os.path.exists(cpath):
                        return []
                    with open(cpath, "r", encoding="utf-8") as f:
                        doc = yaml.safe_load(f)
                    views = (doc or {}).get("views", [])
                    target = None
                    for v in views:
                        if isinstance(v, dict) and v.get("name") == "FI_Star_View":
                            target = v
                            break
                    if not isinstance(target, dict):
                        return []
                    llm_profile = target.get("llm_profile", {}) or {}
                    all_dims = llm_profile.get("dimension_semantics", []) or []
                    ban = ["flag", "hierarchy", "id", "transaction date", "version", "fiscal ytd", "fiscal qtd", "fiscal mtd"]
                    kept: List[str] = []
                    for d in all_dims:
                        s = str(d or "").strip()
                        if not s:
                            continue
                        sl = s.lower()
                        if any(b in sl for b in ban):
                            continue
                        kept.append(s)
                    if isinstance(limit, int) and limit > 0:
                        kept = kept[:limit]
                    dims = kept
                except Exception:
                    pass
                return dims

            # Load KPIs (ensure provider is loaded if empty)
            try:
                if kp and hasattr(kp, "get_all"):
                    if not kp.get_all() and hasattr(kp, "load"):
                        await kp.load()
            except Exception:
                pass
            all_kpis = kp.get_all() if kp else []
            if not all_kpis:
                return {"success": False, "message": "No KPIs available to analyze", "written": False}

            # Load existing enrichment (merge, do not overwrite other keys)
            existing: Dict[str, Any] = {}
            try:
                if os.path.exists(out_path):
                    with open(out_path, "r", encoding="utf-8") as f:
                        existing = yaml.safe_load(f) or {}
            except Exception:
                existing = {}

            top_dimensions_map: Dict[str, str] = dict(existing.get("top_dimensions") or {})
            dimension_scores_map: Dict[str, str] = dict(existing.get("dimension_scores") or {})

            # Candidate dimensions from contract; KPI metadata dims are additive when present
            contract_dim_candidates = _contract_dims()

            def _score_dim(rows: List[List[Any]], columns: List[str]) -> float:
                # Score by concentration: top-3 share of total
                try:
                    if not rows:
                        return 0.0
                    # determine measure column index
                    mi = -1
                    if columns:
                        for idx, c in enumerate(columns):
                            if str(c).strip().lower() == "total_value":
                                mi = idx
                                break
                    if mi < 0:
                        mi = 1 if (columns and len(columns) > 1) else 0
                    vals: List[float] = []
                    for r in rows:
                        try:
                            v = r[mi]
                            vals.append(float(v) if v is not None else 0.0)
                        except Exception:
                            continue
                    if not vals:
                        return 0.0
                    total = sum(vals) or 1.0
                    vals.sort(reverse=True)
                    top3 = sum(vals[:3])
                    return float(top3) / float(total) if total else 0.0
                except Exception:
                    return 0.0

            analyzed = 0
            failures: List[str] = []

            for kpi in all_kpis:
                try:
                    kpi_name = getattr(kpi, "name", None) or getattr(kpi, "id", None) or "unknown"
                    # Compose candidate dims: contract dims + KPI metadata dims
                    candidate_dims: List[str] = list(contract_dim_candidates)
                    try:
                        if hasattr(kpi, "dimensions") and isinstance(kpi.dimensions, list):
                            for d in kpi.dimensions:
                                if isinstance(d, dict) and d.get("name"):
                                    candidate_dims.append(str(d.get("name")))
                                elif isinstance(d, str):
                                    candidate_dims.append(d)
                    except Exception:
                        pass
                    # Deduplicate while preserving order
                    seen: Set[str] = set()
                    dims_unique: List[str] = []
                    for d in candidate_dims:
                        s = str(d).strip()
                        if s and s not in seen:
                            seen.add(s)
                            dims_unique.append(s)

                    if not dims_unique:
                        continue

                    # Score each dimension by executing grouped KPI SQL via Data Product Agent
                    dim_scores: Dict[str, float] = {}
                    for dim in dims_unique:
                        try:
                            gen = await data_product_agent.generate_sql_for_kpi(
                                kpi_definition=kpi,
                                timeframe=timeframe,
                                filters=None,
                                breakdown=True,
                                override_group_by=[dim]
                            )
                            if not gen.get("success"):
                                continue
                            exec_resp = await data_product_agent.execute_sql(gen.get("sql"))
                            rows = exec_resp.get("rows") or []
                            cols = exec_resp.get("columns") or []
                            score = _score_dim(rows, cols)
                            dim_scores[dim] = score
                        except Exception:
                            # Non-fatal per-dimension
                            continue

                    # Select top-N dimensions by score
                    if dim_scores:
                        top_sorted = sorted(dim_scores.items(), key=lambda kv: kv[1], reverse=True)
                        top_list = [d for d, _ in top_sorted[: max(1, int(max_dimensions_per_kpi or 5))]]
                        # Persist as comma-separated string for readability
                        top_dimensions_map[kpi_name] = ", ".join(top_list)
                        # Store scores as compact JSON string to preserve floats precisely
                        try:
                            dimension_scores_map[kpi_name] = json.dumps({k: round(v, 6) for k, v in dim_scores.items()})
                        except Exception:
                            # Fallback to YAML-native mapping
                            dimension_scores_map[kpi_name] = {k: float(v) for k, v in dim_scores.items()}
                        analyzed += 1
                    else:
                        failures.append(kpi_name)
                except Exception:
                    failures.append(getattr(kpi, "name", "unknown"))

            # Write enrichment YAML (non-destructive merge)
            out_doc = dict(existing)
            out_doc["top_dimensions"] = top_dimensions_map
            out_doc["dimension_scores"] = dimension_scores_map

            try:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(out_doc, f, sort_keys=True, allow_unicode=True)
                return {
                    "success": True,
                    "written": True,
                    "path": out_path,
                    "kpis_analyzed": analyzed,
                    "kpis_total": len(all_kpis),
                    "failures": failures,
                }
            except Exception as we:
                return {"success": False, "written": False, "message": str(we), "path": out_path}
        except Exception as e:
            self.logger.error(f"compute_and_persist_top_dimensions error: {e}")
            return {"success": False, "written": False, "message": str(e)}


def create_data_governance_agent(config: Dict[str, Any] = None) -> A9_Data_Governance_Agent:
    """
    Factory function to create a Data Governance Agent.
    
    Args:
        config: Configuration dictionary with these options:
            - glossary_path: Path to the business glossary YAML file (optional)
        
    Returns:
        A9_Data_Governance_Agent instance
    """
    if not config:
        config = {}
        
    return A9_Data_Governance_Agent(config)
