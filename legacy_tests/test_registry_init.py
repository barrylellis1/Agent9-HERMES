"""
Test script for registry initialization
This script isolates the registry initialization process to diagnose issues.
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

async def test_registry_initialization():
    """Test registry initialization in isolation."""
    logger = logging.getLogger("test_registry_init")
    logger.info("Starting registry initialization test")
    
    # Create registry factory
    registry_factory = RegistryFactory()
    logger.info("Created registry factory")
    
    # Register providers one by one with detailed logging
    try:
        # KPI Provider
        logger.info("Registering KPI provider")
        kpi_provider = KPIProvider()
        registry_factory.register_provider("kpi", kpi_provider)
        
        # Principal Provider
        logger.info("Registering Principal Profile provider")
        principal_provider = PrincipalProfileProvider()
        registry_factory.register_provider("principal_profile", principal_provider)
        
        # Data Product Provider
        logger.info("Registering Data Product provider")
        data_product_provider = DataProductProvider()
        registry_factory.register_provider("data_product", data_product_provider)
        
        # Business Process Provider
        logger.info("Registering Business Process provider")
        business_process_provider = BusinessProcessProvider(
            source_path="src/registry/business_process/business_process_registry.yaml",
            storage_format="yaml"
        )
        registry_factory.register_provider("business_process", business_process_provider)
        
        # Business Glossary Provider
        logger.info("Registering Business Glossary provider")
        business_glossary_provider = BusinessGlossaryProvider()
        registry_factory.register_provider("business_glossary", business_glossary_provider)
        
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
        
        # Data Product Provider
        logger.info("Loading Data Products")
        data_products = data_product_provider.get_all()
        logger.info(f"Loaded {len(data_products) if data_products else 0} Data Products")
        
        # Business Glossary Provider
        logger.info("Loading Business Terms")
        terms = business_glossary_provider.get_all()
        logger.info(f"Loaded {len(terms) if terms else 0} Business Terms")
        
    except Exception as e:
        logger.error(f"Error during registry initialization: {str(e)}", exc_info=True)
    
    logger.info("Registry initialization test complete")

if __name__ == "__main__":
    asyncio.run(test_registry_initialization())
