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
    DataLineageResponse
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
