"""
A9 Data Governance Agent

This agent provides data governance capabilities, including business-to-technical term translation,
data quality monitoring, access control, and compliance tracking.

It leverages the Unified Registry Access Layer for business glossary terms,
data product contracts, and governance policies.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union

from pydantic import BaseModel, Field

# Import registry providers
from src.registry.factory import RegistryFactory
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider, BusinessTerm
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.models.kpi import KPI

# Import shared models
from src.agents.models.data_governance_models import (
    BusinessTermTranslationRequest,
    BusinessTermTranslationResponse,
    DataAccessValidationRequest,
    DataAccessValidationResponse,
    DataQualityCheckRequest,
    DataQualityCheckResponse,
    DataLineageRequest,
    DataLineageResponse,
    KPIDataProductMappingRequest,
    KPIDataProductMappingResponse,
    KPIDataProductMapping,
    DataAssetPathRequest,
    DataAssetPathResponse,
    KPIViewNameRequest,
    KPIViewNameResponse
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
            
    def _get_view_name_for_kpi(self, kpi: KPI) -> str:
        """
        Get the view name for a KPI.
        
        Args:
            kpi: KPI object
            
        Returns:
            View name for the KPI
        """
        try:
            # Check if the KPI has a view_name attribute
            if hasattr(kpi, 'view_name') and kpi.view_name:
                return kpi.view_name
                
            # Check if the KPI has metadata with view_name
            if hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict) and 'view_name' in kpi.metadata:
                return kpi.metadata['view_name']
                
            # Generate a view name based on KPI name
            if hasattr(kpi, 'name'):
                return f"view_{kpi.name.lower().replace(' ', '_')}"
                
            return "unknown_view"
        except Exception as e:
            self.logger.error(f"Error getting view name for KPI: {e}")
            return "unknown_view"
            
    def _get_data_product_id_for_kpi(self, kpi: KPI) -> Optional[str]:
        """
        Get the data product ID for a KPI.
        
        Args:
            kpi: KPI object
            
        Returns:
            Data product ID for the KPI
        """
        try:
            # Check if the KPI has a data_product_id attribute
            if hasattr(kpi, 'data_product_id') and kpi.data_product_id:
                return kpi.data_product_id
                
            # Check if the KPI has metadata with data_product_id
            if hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict) and 'data_product_id' in kpi.metadata:
                return kpi.metadata['data_product_id']
                
            # Default to FI_Star_Schema
            return "FI_Star_Schema"
        except Exception as e:
            self.logger.error(f"Error getting data product ID for KPI: {e}")
            return "FI_Star_Schema"
    
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
