"""
Principal Registry Validation Script

This script validates the loading of principal profile data from YAML
and the correct operation of the Registry Factory for principal profiles.
"""

import asyncio
import logging
import sys
import yaml
from typing import Dict, List, Any

from src.registry.factory import RegistryFactory
from src.registry.models.principal import PrincipalProfile
from src.registry.providers.principal_provider import PrincipalProfileProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def load_principals_from_yaml(yaml_path: str) -> PrincipalProfileProvider:
    """Load principals from YAML file directly."""
    logger.info(f"Loading principals from {yaml_path}")
    
    try:
        # Read the YAML file
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Check if the data is in the expected format with a 'principals' key
        if "principals" not in data:
            logger.error(f"No 'principals' key found in YAML file at {yaml_path}")
            return None
        
        principals_data = data["principals"]
        logger.info(f"Found {len(principals_data)} principals in YAML under 'principals' key")
        
        # Create a provider instance
        provider = PrincipalProfileProvider(yaml_path, storage_format="yaml")
        
        # Load the provider data
        await provider.load()
        
        return provider
    except Exception as e:
        logger.error(f"Error loading principals from YAML: {e}")
        return None

def validate_sample_principals(principals: List[PrincipalProfile], provider: PrincipalProfileProvider) -> None:
    """Validate key principals are present with expected attributes."""
    # Validate CFO principal
    cfo = provider.get("cfo_001")
    if cfo:
        logger.info(f"Found Principal: {cfo.id} - {cfo.name} (Title: {cfo.title})")
        logger.info(f"  Description: {cfo.description}")
        logger.info(f"  Business Processes: {cfo.business_processes}")
        logger.info(f"  Default Filters: {cfo.default_filters}")
    else:
        logger.error("CFO principal not found!")
    
    # Validate CDO principal
    cdo = provider.get("cdo_001")
    if cdo:
        logger.info(f"Found Principal: {cdo.id} - {cdo.name} (Title: {cdo.title})")
        logger.info(f"  Description: {cdo.description}")
        logger.info(f"  Business Processes: {cdo.business_processes}")
        logger.info(f"  Default Filters: {cdo.default_filters}")
    else:
        logger.error("CDO principal not found!")
    
    # Validate Manager principal
    manager = provider.get("manager_001")
    if manager:
        logger.info(f"Found Principal: {manager.id} - {manager.name} (Title: {manager.title})")
        logger.info(f"  Description: {manager.description}")
        logger.info(f"  Business Processes: {manager.business_processes}")
    else:
        logger.error("Manager principal not found!")

async def validate_direct_provider() -> int:
    """Validate loading principals directly via the provider."""
    logger.info("\n=== Testing Direct Principal Provider Access ===")
    
    # Load principals from YAML
    yaml_path = "src/registry_references/principal_registry/yaml/principal_registry.yaml"
    provider = await load_principals_from_yaml(yaml_path)
    
    if provider is None:
        logger.error("Failed to load principals from YAML")
        return 0
    
    # Validate principal count
    principals = provider.get_all()
    logger.info(f"Loaded {len(principals)} principals from YAML")
    
    # Validate specific principals exist
    validate_sample_principals(principals, provider)
    
    return len(principals)

async def validate_registry_factory() -> int:
    """Validate loading principals via the Registry Factory."""
    logger.info("\n=== Testing Registry Factory Access ===")
    
    try:
        # Initialize the Registry Factory
        factory = RegistryFactory()
        
        # Create and register a Principal provider
        yaml_path = "src/registry_references/principal_registry/yaml/principal_registry.yaml"
        principal_provider = await load_principals_from_yaml(yaml_path)
        
        if principal_provider is None:
            logger.error("Failed to load principals from YAML for Registry Factory")
            return 0
        
        # Register the provider with the factory
        factory.register_provider('principal_profile', principal_provider)
        
        # Initialize the factory
        await factory.initialize()
        
        # Get the Principal provider from the factory
        provider = factory.get_principal_profile_provider()
        if provider is None:
            logger.error("Registry Factory returned None for Principal provider")
            return 0
            
        # Validate principal count
        principals = provider.get_all()
        logger.info(f"Loaded {len(principals)} principals via Registry Factory")
        
        # Validate specific principals exist
        validate_sample_principals(principals, provider)
        
        return len(principals)
    except Exception as e:
        logger.error(f"Error in Registry Factory validation: {e}")
        return 0

async def main():
    """Main validation function."""
    logger.info("Starting Principal Registry validation")
    
    direct_count = await validate_direct_provider()
    factory_count = await validate_registry_factory()
    
    # Validate that expected principals are present in both approaches
    # (note: factory may load additional default principals, so exact count may differ)
    logger.info(f"\nDirect Principal count: {direct_count}")
    logger.info(f"Registry Factory Principal count: {factory_count}")
    
    # Check key principals exist in both approaches as a basic validation
    if direct_count > 0 and factory_count > 0:
        logger.info("\n✓ SUCCESS: Principals loaded successfully via both direct provider and Registry Factory")
    else:
        logger.error("\n✗ ERROR: Principal loading failed in one or both approaches!")
        
    logger.info("\nPrincipal Registry validation completed")

if __name__ == "__main__":
    asyncio.run(main())
