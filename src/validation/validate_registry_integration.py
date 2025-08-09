"""
Registry Integration Validation Script

This script validates the integration between all registry components
(KPI, Principal, Business Process, Data Product) and ensures they
work together correctly in registry-driven workflows.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Set

# Add the project root to Python path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.registry.factory import RegistryFactory
from src.registry.models.kpi import KPI
from src.registry.models.principal import PrincipalProfile
from src.registry.models.business_process import BusinessProcess
from src.registry.models.data_product import DataProduct
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.data_product_provider import DataProductProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Paths to registry YAML files
PRINCIPAL_REGISTRY_PATH = "src/registry_references/principal_registry/yaml/principal_registry.yaml"
KPI_REGISTRY_PATH = "src/registry_references/kpi_registry/yaml/kpi_registry.yaml"
BUSINESS_PROCESS_REGISTRY_PATH = "src/registry_references/business_process_registry/yaml/business_process_registry.yaml"
DATA_PRODUCT_CONTRACTS_PATH = "src/contracts"  # Directory containing YAML contracts

class RegistryIntegrationValidator:
    """Validates integration between registry components."""
    
    def __init__(self):
        """Initialize the registry integration validator."""
        self.factory = RegistryFactory()
        self.principal_provider = None
        self.kpi_provider = None
        self.business_process_provider = None
        self.data_product_provider = None
        
        # Track validation results
        self.issues = []
        self.successful_validations = []
    
    async def initialize_factory(self) -> None:
        """Initialize the Registry Factory with all providers."""
        logger.info("Initializing Registry Factory with all providers")
        
        # Create and register providers
        await self._register_principal_provider()
        await self._register_kpi_provider()
        await self._register_business_process_provider()
        await self._register_data_product_provider()
        
        # Initialize the factory
        await self.factory.initialize()
        
        # Get initialized providers from factory
        self.principal_provider = self.factory.get_principal_profile_provider()
        self.kpi_provider = self.factory.get_kpi_provider()
        self.business_process_provider = self.factory.get_business_process_provider()
        self.data_product_provider = self.factory.get_data_product_provider()
        
        if None in [self.principal_provider, self.kpi_provider, 
                    self.business_process_provider, self.data_product_provider]:
            logger.error("One or more providers not initialized correctly")
            self.issues.append("Factory initialization failed")
        else:
            logger.info("All registry providers initialized successfully")
            self.successful_validations.append("Factory initialization")
    
    async def _register_principal_provider(self) -> None:
        """Register a Principal provider with the factory."""
        try:
            provider = PrincipalProfileProvider(PRINCIPAL_REGISTRY_PATH, storage_format="yaml")
            await provider.load()
            self.factory.register_provider('principal_profile', provider)
            logger.info(f"Registered principal provider with {len(provider.get_all())} principals")
        except Exception as e:
            logger.error(f"Error registering principal provider: {e}")
            self.issues.append(f"Principal provider registration failed: {e}")
    
    async def _register_kpi_provider(self) -> None:
        """Register a KPI provider with the factory."""
        try:
            provider = KPIProvider(KPI_REGISTRY_PATH, storage_format="yaml")
            await provider.load()
            self.factory.register_provider('kpi', provider)
            logger.info(f"Registered KPI provider with {len(provider.get_all())} KPIs")
        except Exception as e:
            logger.error(f"Error registering KPI provider: {e}")
            self.issues.append(f"KPI provider registration failed: {e}")
    
    async def _register_business_process_provider(self) -> None:
        """Register a Business Process provider with the factory."""
        try:
            provider = BusinessProcessProvider(BUSINESS_PROCESS_REGISTRY_PATH, storage_format="yaml")
            await provider.load()
            self.factory.register_provider('business_process', provider)
            logger.info(f"Registered business process provider with {len(provider.get_all())} business processes")
        except Exception as e:
            logger.error(f"Error registering business process provider: {e}")
            self.issues.append(f"Business process provider registration failed: {e}")
    
    async def _register_data_product_provider(self) -> None:
        """Register a Data Product provider with the factory."""
        try:
            provider = DataProductProvider(DATA_PRODUCT_CONTRACTS_PATH)
            await provider.load()
            self.factory.register_provider('data_product', provider)
            logger.info(f"Registered data product provider with {len(provider.get_all())} data products")
        except Exception as e:
            logger.error(f"Error registering data product provider: {e}")
            self.issues.append(f"Data product provider registration failed: {e}")
    
    async def validate_principal_kpi_references(self) -> None:
        """Validate that KPIs referenced by principals actually exist."""
        logger.info("Validating principal-KPI references")
        
        if not self.principal_provider or not self.kpi_provider:
            logger.error("Cannot validate principal-KPI references: providers not initialized")
            self.issues.append("Principal-KPI reference validation skipped")
            return
        
        principals = self.principal_provider.get_all()
        kpis = self.kpi_provider.get_all()
        kpi_ids = set(kpi.id for kpi in kpis)
        
        missing_kpis = set()
        
        for principal in principals:
            if not hasattr(principal, 'kpis') or not principal.kpis:
                continue
                
            for kpi_id in principal.kpis:
                if kpi_id not in kpi_ids:
                    missing_kpis.add(kpi_id)
                    logger.warning(f"Principal {principal.id} references non-existent KPI: {kpi_id}")
        
        if missing_kpis:
            logger.error(f"Found {len(missing_kpis)} KPI references in principals that don't exist")
            self.issues.append(f"Principal-KPI reference validation failed: missing KPIs {missing_kpis}")
        else:
            logger.info("All KPIs referenced by principals exist in the KPI registry")
            self.successful_validations.append("Principal-KPI references")
    
    async def validate_principal_business_process_references(self) -> None:
        """Validate that business processes referenced by principals actually exist."""
        logger.info("Validating principal-business process references")
        
        if not self.principal_provider or not self.business_process_provider:
            logger.error("Cannot validate principal-business process references: providers not initialized")
            self.issues.append("Principal-business process reference validation skipped")
            return
        
        principals = self.principal_provider.get_all()
        processes = self.business_process_provider.get_all() if self.business_process_provider else []
        
        # Create sets of identifiers to check against
        process_ids = set(process.id for process in processes)
        process_display_names = set(process.display_name for process in processes if hasattr(process, 'display_name') and process.display_name)
        process_names = set(f"{process.domain}: {process.name}" for process in processes)
        
        missing_processes = set()
        
        for principal in principals:
            if not hasattr(principal, 'business_processes') or not principal.business_processes:
                continue
                
            for process_id in principal.business_processes:
                # First check direct matches against display_name and domain+name format
                if process_id in process_display_names or process_id in process_names:
                    continue
                    
                # Fall back to normalization for ID-based matching
                normalized_id = process_id.lower().replace(" ", "_").replace(":", "_")
                found = False
                
                for existing_id in process_ids:
                    if normalized_id in existing_id.lower() or existing_id.lower() in normalized_id:
                        found = True
                        break
                        
                if not found:
                    missing_processes.add(process_id)
                    logger.warning(f"Principal {principal.id} references non-existent business process: {process_id}")
        
        if missing_processes:
            logger.error(f"Found {len(missing_processes)} business process references in principals that don't exist")
            self.issues.append(f"Principal-business process reference validation failed: missing processes {missing_processes}")
        else:
            logger.info("All business processes referenced by principals exist in the business process registry")
            self.successful_validations.append("Principal-business process references")
    
    async def validate_kpi_business_process_references(self) -> None:
        """Validate that business processes referenced by KPIs actually exist."""
        logger.info("Validating KPI-business process references")
        
        if not self.kpi_provider or not self.business_process_provider:
            logger.error("Cannot validate KPI-business process references: providers not initialized")
            self.issues.append("KPI-business process reference validation skipped")
            return
        
        kpis = self.kpi_provider.get_all()
        processes = self.business_process_provider.get_all()
        process_ids = set(process.id for process in processes)
        
        missing_processes = set()
        
        for kpi in kpis:
            if not hasattr(kpi, 'business_processes') or not kpi.business_processes:
                continue
                
            for process_id in kpi.business_processes:
                if process_id not in process_ids:
                    missing_processes.add(process_id)
                    logger.warning(f"KPI {kpi.id} references non-existent business process: {process_id}")
        
        if missing_processes:
            logger.error(f"Found {len(missing_processes)} business process references in KPIs that don't exist")
            self.issues.append(f"KPI-business process reference validation failed: missing processes {missing_processes}")
        else:
            logger.info("All business processes referenced by KPIs exist in the business process registry")
            self.successful_validations.append("KPI-business process references")
    
    async def validate_data_product_kpi_references(self) -> None:
        """Validate that KPIs referenced by data products actually exist."""
        logger.info("Validating data product-KPI references")
        
        if not self.data_product_provider or not self.kpi_provider:
            logger.error("Cannot validate data product-KPI references: providers not initialized")
            self.issues.append("Data product-KPI reference validation skipped")
            return
        
        data_products = self.data_product_provider.get_all()
        kpis = self.kpi_provider.get_all()
        kpi_ids = set(kpi.id for kpi in kpis)
        
        missing_kpis = set()
        
        for data_product in data_products:
            if not hasattr(data_product, 'kpis') or not data_product.kpis:
                continue
                
            for kpi_id in data_product.kpis:
                if kpi_id not in kpi_ids:
                    missing_kpis.add(kpi_id)
                    logger.warning(f"Data product {data_product.id} references non-existent KPI: {kpi_id}")
        
        if missing_kpis:
            logger.error(f"Found {len(missing_kpis)} KPI references in data products that don't exist")
            self.issues.append(f"Data product-KPI reference validation failed: missing KPIs {missing_kpis}")
        else:
            logger.info("All KPIs referenced by data products exist in the KPI registry")
            self.successful_validations.append("Data product-KPI references")
    
    async def validate_registry_driven_workflow(self) -> None:
        """Validate an end-to-end registry-driven workflow."""
        logger.info("\nValidating end-to-end registry-driven workflow")
        
        # Skip if any provider is missing
        if None in [self.principal_provider, self.kpi_provider, 
                    self.business_process_provider, self.data_product_provider]:
            logger.error("Cannot validate registry-driven workflow: one or more providers not initialized")
            self.issues.append("Registry-driven workflow validation skipped")
            return
        
        try:
            # Simulate a workflow for CFO persona
            cfo = self.principal_provider.get("cfo_001")
            if not cfo:
                logger.error("CFO principal not found")
                self.issues.append("Registry-driven workflow validation failed: CFO principal not found")
                return
            
            logger.info(f"Starting workflow for principal: {cfo.name} ({cfo.title})")
            
            # Get business processes relevant to CFO
            if hasattr(cfo, 'business_processes') and cfo.business_processes:
                bp_count = len(cfo.business_processes)
                logger.info(f"Found {bp_count} business processes for CFO")
                
                # Get KPIs relevant to CFO's business processes
                if self.kpi_provider:
                    relevant_kpis = []
                    for bp in cfo.business_processes:
                        # Normalize business process ID for comparison
                        bp_normalized = bp.lower().replace(" ", "_").replace(":", "_")
                        
                        # Find KPIs for this business process
                        for kpi in self.kpi_provider.get_all():
                            if hasattr(kpi, 'business_processes') and kpi.business_processes:
                                for kpi_bp in kpi.business_processes:
                                    if bp_normalized in kpi_bp.lower() or kpi_bp.lower() in bp_normalized:
                                        relevant_kpis.append(kpi)
                                        break
                    
                    logger.info(f"Found {len(relevant_kpis)} KPIs relevant to CFO's business processes")
                    
                    if relevant_kpis:
                        logger.info("Sample of relevant KPIs:")
                        for i, kpi in enumerate(relevant_kpis[:3]):
                            logger.info(f"  - {kpi.id}: {kpi.name}")
                        
                        # Success
                        self.successful_validations.append("Registry-driven workflow for CFO")
                    else:
                        logger.warning("No relevant KPIs found for CFO's business processes")
                        self.issues.append("Registry-driven workflow validation: no KPIs found for CFO's business processes")
            else:
                logger.warning("CFO has no business processes defined")
                self.issues.append("Registry-driven workflow validation: CFO has no business processes")
        
        except Exception as e:
            logger.error(f"Error in registry-driven workflow validation: {e}")
            self.issues.append(f"Registry-driven workflow validation failed: {e}")
    
    async def run_all_validations(self) -> None:
        """Run all validation tests."""
        await self.initialize_factory()
        
        # Run validation tests
        await self.validate_principal_kpi_references()
        await self.validate_principal_business_process_references()
        await self.validate_kpi_business_process_references()
        await self.validate_data_product_kpi_references()
        await self.validate_registry_driven_workflow()
        
        # Display summary
        self._display_summary()
    
    def _display_summary(self) -> None:
        """Display a summary of validation results."""
        logger.info("\n=== Registry Integration Validation Summary ===")
        
        if self.successful_validations:
            logger.info(f"\n✓ Successful validations ({len(self.successful_validations)}):")
            for validation in self.successful_validations:
                logger.info(f"  - {validation}")
        
        if self.issues:
            logger.error(f"\n✗ Issues found ({len(self.issues)}):")
            for issue in self.issues:
                logger.error(f"  - {issue}")
            logger.error("\nRegistry integration validation completed with issues")
        else:
            logger.info("\n✓ All validations passed successfully!")
            logger.info("\nRegistry integration validation completed successfully")

async def main():
    """Main function."""
    logger.info("Starting Registry Integration Validation")
    
    validator = RegistryIntegrationValidator()
    await validator.run_all_validations()

if __name__ == "__main__":
    asyncio.run(main())
