"""
Test script with minimal configuration
This script uses a minimal configuration to test the core functionality.
"""

import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src directory to path if needed
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.registry.factory import RegistryFactory
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.registry.providers.data_product_provider import DataProductProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider

async def test_minimal_config():
    """Test with minimal configuration."""
    logger = logging.getLogger("test_minimal_config")
    logger.info("Starting minimal configuration test")
    
    # Create registry factory
    registry_factory = RegistryFactory()
    logger.info("Created registry factory")
    
    # Register providers with explicit file paths
    try:
        # KPI Provider with explicit file path
        logger.info("Registering KPI provider with explicit file path")
        kpi_provider = KPIProvider(
            source_path="src/registry/kpi/kpi_registry.yaml",
            storage_format="yaml"
        )
        registry_factory.register_provider("kpi", kpi_provider)
        
        # Principal Provider with explicit file path
        logger.info("Registering Principal Profile provider with explicit file path")
        principal_provider = PrincipalProfileProvider(
            source_path="src/registry/principal/principal_registry.yaml",
            storage_format="yaml"
        )
        registry_factory.register_provider("principal_profile", principal_provider)
        
        # Business Process Provider with explicit file path
        logger.info("Registering Business Process provider with explicit file path")
        business_process_provider = BusinessProcessProvider(
            source_path="src/registry/business_process/business_process_registry.yaml",
            storage_format="yaml"
        )
        registry_factory.register_provider("business_process", business_process_provider)
        
        # Initialize all providers
        logger.info("Initializing all providers")
        await registry_factory.initialize()
        
        # Check initialization status
        logger.info("Provider initialization status:")
        for provider_name, status in registry_factory.provider_status().items():
            logger.info(f"  - {provider_name}: {'Initialized' if status else 'Not initialized'}")
        
        # Test loading data from each provider
        logger.info("\nTesting data loading from each provider:")
        
        # KPI Provider
        logger.info("Loading KPIs")
        kpis = kpi_provider.get_all()
        logger.info(f"Loaded {len(kpis) if kpis else 0} KPIs")
        
        # Principal Provider
        logger.info("Loading Principal Profiles")
        profiles = principal_provider.get_all()
        logger.info(f"Loaded {len(profiles) if profiles else 0} Principal Profiles")
        
        # Business Process Provider
        logger.info("Loading Business Processes")
        processes = business_process_provider.get_all()
        logger.info(f"Loaded {len(processes) if processes else 0} Business Processes")
        
    except Exception as e:
        logger.error(f"Error during minimal configuration test: {str(e)}", exc_info=True)
    
    logger.info("Minimal configuration test complete")

if __name__ == "__main__":
    asyncio.run(test_minimal_config())
