"""
A9 Data Governance Agent

This agent provides data governance capabilities, including business-to-technical term translation,
data quality monitoring, access control, and compliance tracking.

It leverages the Unified Registry Access Layer for business glossary terms,
data product contracts, and governance policies.
"""

import os
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import yaml

from pydantic import BaseModel, Field

# Import registry providers
from src.registry.factory import RegistryFactory
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
)
from src.agents.models.data_product_onboarding_models import (
    KPIRegistryUpdateRequest,
    KPIRegistryUpdateResponse,
    BusinessProcessMappingRequest,
    BusinessProcessMappingResponse,
)
from src.registry.models.kpi import KPI as RegistryKPI
from src.registry.models.business_process import BusinessProcess

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
    
    async def validate_data_access(
        self, request: DataAccessValidationRequest
    ) -> DataAccessValidationResponse:
        """
        Validate data access permissions for a principal.
        
        Args:
            request: Contains principal_id, data_product_id, and access_type
            
        Returns:
            Response with access validation result
        """
        # For MVP, implement a simple validation
        # In production, this would check against actual policies
        
        # Log the access validation request for audit
        self.logger.info(
            f"Data access validation request: Principal {request.principal_id}, "
            f"Data Product {request.data_product_id}, Access Type {request.access_type}"
        )
        
        # Always allow for now
        return DataAccessValidationResponse(
            allowed=True,
            reason="Access granted for MVP implementation"
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
        
        # Get all KPIs from the registry
        try:
            all_kpis = self.kpi_provider.get_all() or []
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

                self.kpi_provider.upsert(registry_kpi)
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
                    bp_provider.upsert(bp_model)
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
            kpi = kpi_provider.get(kpi_name)
            
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
        # 4) Default to view_{technical_name}
        technical_name = self._get_technical_name_for_kpi(kpi)
        return f"view_{technical_name}"
    
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
