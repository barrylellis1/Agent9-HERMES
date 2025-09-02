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
    DataAssetPathResponse
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
        
    async def map_kpis_to_data_products(
        self, request: KPIDataProductMappingRequest
    ) -> KPIDataProductMappingResponse:
        """
        Map KPIs to their corresponding data products.
        
        This method serves as the authoritative source for KPI to data product mappings,
        ensuring consistent data access across the system.
        
        Args:
            request: Contains KPI names to map and optional context
            
        Returns:
            Response with KPI to data product mappings
        """
        if not self.business_glossary_provider:
            self.logger.error("Business Glossary Provider not initialized")
            return KPIDataProductMappingResponse(
                mappings=[],
                unmapped_kpis=request.kpi_names,
                human_action_required=True,
                human_action_context={
                    "message": "Business Glossary Provider not available. Please contact your administrator."
                }
            )
        
        # Initialize response objects
        mappings = []
        unmapped_kpis = []
        
        # Process each KPI name
        for kpi_name in request.kpi_names:
            # First check if the KPI exists in the business glossary
            kpi_term = self.business_glossary_provider.get_term(kpi_name)
            
            if kpi_term and hasattr(kpi_term, 'metadata') and kpi_term.metadata:
                # If the KPI has a data_product_id in its metadata, use that
                data_product_id = kpi_term.metadata.get('data_product_id')
                if data_product_id:
                    mappings.append(KPIDataProductMapping(
                        kpi_name=kpi_name,
                        data_product_id=data_product_id,
                        technical_name=kpi_term.metadata.get('technical_name'),
                        metadata=kpi_term.metadata
                    ))
                    continue
            
            # If we reach here, we couldn't find the mapping in the business glossary
            # Try to infer from KPI name or context
            inferred_data_product = self._infer_data_product_from_kpi(kpi_name, request.context)
            
            if inferred_data_product:
                mappings.append(KPIDataProductMapping(
                    kpi_name=kpi_name,
                    data_product_id=inferred_data_product,
                    technical_name=None,
                    metadata={"source": "inferred"}
                ))
            else:
                # If all else fails, use the default data product
                default_data_product = "FI_Star_Schema"  # Default finance data product
                mappings.append(KPIDataProductMapping(
                    kpi_name=kpi_name,
                    data_product_id=default_data_product,
                    technical_name=None,
                    metadata={"source": "default"}
                ))
                # Add to unmapped list for reporting
                unmapped_kpis.append(kpi_name)
        
        # Determine if human action is required
        human_action_required = len(unmapped_kpis) > 0
        human_action_context = None
        
        if human_action_required:
            human_action_context = {
                "unmapped_kpis": unmapped_kpis,
                "message": "These KPIs could not be mapped to specific data products and are using defaults."
            }
        
        # Log the mapping operation for audit
        self.logger.info(
            f"KPI to data product mapping: {len(mappings)} mapped, "
            f"{len(unmapped_kpis)} using default mapping"
        )
        
        return KPIDataProductMappingResponse(
            mappings=mappings,
            unmapped_kpis=unmapped_kpis,
            human_action_required=human_action_required,
            human_action_context=human_action_context
        )
    
    def _infer_data_product_from_kpi(self, kpi_name: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Infer the data product from KPI name or context.
        
        Args:
            kpi_name: Name of the KPI
            context: Additional context for inference
            
        Returns:
            Inferred data product ID or None
        """
        kpi_name_lower = kpi_name.lower()
        
        # Finance KPIs
        if any(term in kpi_name_lower for term in ['revenue', 'profit', 'margin', 'cost', 'expense', 'budget']):
            return "FI_Star_Schema"
        
        # HR KPIs
        if any(term in kpi_name_lower for term in ['employee', 'headcount', 'turnover', 'retention']):
            return "HR_Data_Product"
        
        # Supply Chain KPIs
        if any(term in kpi_name_lower for term in ['inventory', 'supply', 'logistics', 'warehouse']):
            return "SC_Data_Product"
        
        # Use context if available
        if context and 'business_domain' in context:
            domain = context['business_domain'].lower()
            if 'finance' in domain:
                return "FI_Star_Schema"
            elif 'hr' in domain or 'human resources' in domain:
                return "HR_Data_Product"
            elif 'supply' in domain or 'logistics' in domain:
                return "SC_Data_Product"
        
        # No inference possible
        return None
        
    async def get_data_asset_path(
        self, request: DataAssetPathRequest
    ) -> DataAssetPathResponse:
        """
        Resolve the path to a data asset.
        
        This method serves as the authoritative source for data asset locations,
        ensuring consistent data access across the system.
        
        Args:
            request: Contains asset name and optional context
            
        Returns:
            Response with data asset path and metadata
        """
        # For MVP, implement a simple path resolution
        # In production, this would query a metadata catalog or registry
        
        # Extract asset name and normalize
        asset_name = request.asset_name.lower()
        
        # Default response values
        data_product_id = "unknown"
        asset_path = ""
        access_type = "read"
        metadata = {}
        
        # Map common assets to their locations
        if "finance" in asset_name or "fi_" in asset_name:
            data_product_id = "FI_Star_Schema"
            asset_path = "data/agent9-hermes.duckdb"
            metadata = {"schema": "finance", "type": "duckdb"}
        elif "hr" in asset_name:
            data_product_id = "HR_Data_Product"
            asset_path = "data/agent9-athena.duckdb"
            metadata = {"schema": "hr", "type": "duckdb"}
        elif "apollo" in asset_name:
            data_product_id = "Apollo_Data_Product"
            asset_path = "data/agent9-apollo.duckdb"
            metadata = {"schema": "apollo", "type": "duckdb"}
        else:
            # Default to the main data product
            data_product_id = "FI_Star_Schema"
            asset_path = "data/agent9-hermes.duckdb"
            metadata = {"schema": "default", "type": "duckdb"}
        
        self.logger.info(f"Resolved asset path for {asset_name}: {asset_path}")
        
        return DataAssetPathResponse(
            asset_name=request.asset_name,
            data_product_id=data_product_id,
            asset_path=asset_path,
            access_type=access_type,
            metadata=metadata
        )
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
