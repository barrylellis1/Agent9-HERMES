"""
KPI Registry Validation Script

Validates that the KPI registry YAML file can be loaded and accessed by the KPI provider.
This script tests both direct provider usage and access via the Registry Factory.
"""

import asyncio
import logging
import os
import yaml
from typing import List, Dict, Any

from src.registry.models.kpi import KPI, ComparisonType
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.factory import RegistryFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def validate_direct_provider():
    """Validate loading KPIs directly from the KPI provider."""
    logger.info("=== Testing Direct KPI Provider Access ===")
    
    # First load and register the KPIs manually
    yaml_path = "src/registry_references/kpi_registry/kpi_registry.yaml"
    provider = await load_kpis_from_yaml(yaml_path)
    
    # Validate KPI count
    kpis = provider.get_all()
    logger.info(f"Loaded {len(kpis)} KPIs from YAML")
    
    # Validate specific KPIs exist
    validate_sample_kpis(kpis, provider)
    
    return len(kpis)

async def load_kpis_from_yaml(yaml_path: str) -> KPIProvider:
    """Load KPIs from YAML file and register them with a provider."""
    logger.info(f"Loading KPIs from {yaml_path}")
    
    # Initialize the KPI provider
    provider = KPIProvider()
    
    try:
        # Read the YAML file
        with open(yaml_path, "r") as file:
            data = yaml.safe_load(file)
            
        # Extract the KPI list from the 'kpis' key
        if isinstance(data, dict) and 'kpis' in data:
            kpi_list = data['kpis']
            logger.info(f"Found {len(kpi_list)} KPIs in YAML under 'kpis' key")
            
            # Register each KPI with the provider
            for kpi_data in kpi_list:
                try:
                    kpi = KPI(**kpi_data)
                    provider.register(kpi)
                    logger.debug(f"Registered KPI: {kpi.id} - {kpi.name}")
                except Exception as e:
                    logger.error(f"Failed to create KPI from {kpi_data.get('id', 'unknown')}: {e}")
        else:
            logger.error(f"YAML file does not contain a 'kpis' list: {data.keys() if isinstance(data, dict) else type(data)}")
    except Exception as e:
        logger.error(f"Error processing {yaml_path}: {e}")
    
    return provider

async def validate_registry_factory():
    """Validate loading KPIs via the Registry Factory."""
    logger.info("\n=== Testing Registry Factory Access ===")
    
    try:
        # Initialize the Registry Factory
        factory = RegistryFactory()
        
        # Create and register a KPI provider
        yaml_path = "src/registry_references/kpi_registry/kpi_registry.yaml"
        kpi_provider = await load_kpis_from_yaml(yaml_path)
        
        # Register the provider with the factory
        factory.register_provider('kpi', kpi_provider)
        
        # Initialize the factory
        await factory.initialize()
        
        # Get the KPI provider from the factory
        provider = factory.get_kpi_provider()
        if provider is None:
            logger.error("Registry Factory returned None for KPI provider")
            return 0
            
        # Validate KPI count
        kpis = provider.get_all()
        logger.info(f"Loaded {len(kpis)} KPIs via Registry Factory")
        
        # Validate specific KPIs exist
        validate_sample_kpis(kpis, provider)
        
        return len(kpis)
    except Exception as e:
        logger.error(f"Error in Registry Factory validation: {e}")
        return 0

def validate_sample_kpis(kpis: List[KPI], provider: KPIProvider):
    """Validate that specific sample KPIs exist and have expected properties."""
    # Check for some specific KPIs
    test_kpis = ["gross_margin", "revenue", "payroll"]
    
    for kpi_id in test_kpis:
        kpi = provider.get(kpi_id)
        if kpi:
            logger.info(f"Found KPI: {kpi.id} - {kpi.name} (Domain: {kpi.domain})")
            logger.info(f"  Description: {kpi.description}")
            logger.info(f"  Data Product: {kpi.data_product_id}")
            logger.info(f"  Business Processes: {', '.join(kpi.business_process_ids)}")
            logger.info(f"  Owner Role: {kpi.owner_role}")
            
            # Test the evaluation function
            if kpi.thresholds:
                threshold = kpi.thresholds[0]
                test_value = 5.0
                status = kpi.evaluate(test_value, threshold.comparison_type)
                logger.info(f"  Evaluation test: {test_value} → {status}")
        else:
            logger.error(f"KPI {kpi_id} not found!")

async def main():
    """Main validation function."""
    logger.info("Starting KPI Registry validation")
    
    direct_count = await validate_direct_provider()
    factory_count = await validate_registry_factory()
    
    # Validate that expected KPIs are present in both approaches
    # (note: factory may load additional default KPIs, so exact count may differ)
    logger.info(f"\nDirect KPI count: {direct_count}")
    logger.info(f"Registry Factory KPI count: {factory_count}")
    
    # Check key KPIs exist in both approaches as a basic validation
    if direct_count > 0 and factory_count > 0:
        logger.info("\n✓ SUCCESS: KPIs loaded successfully via both direct provider and Registry Factory")
    else:
        logger.error("\n✗ ERROR: KPI loading failed in one or both approaches!")
        
    logger.info("\nKPI Registry validation completed")

if __name__ == "__main__":
    asyncio.run(main())
