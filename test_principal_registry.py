"""
Simple script to test loading and accessing the principal registry.
"""
import sys
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.append('.')

from src.registry.registry_factory import RegistryFactory

def main():
    """Load and display principal profiles from registry."""
    logger.info("=== Testing Principal Registry Access ===")
    
    # Initialize registry factory
    registry_factory = RegistryFactory()
    
    # Get principal registry provider
    principal_registry = registry_factory.get_principal_registry_provider()
    
    # Load principal profiles
    principal_profiles = principal_registry.get_principal_profiles()
    
    # Display available profiles
    logger.info(f"Found {len(principal_profiles)} principal profiles:")
    for role, profile in principal_profiles.items():
        logger.info(f"Role: {role}")
        logger.info(f"  Name: {profile.get('name', 'N/A')}")
        logger.info(f"  Business Processes: {profile.get('business_processes', [])}")
        logger.info(f"  Default Filters: {profile.get('default_filters', {})}")
        logger.info("---")
    
    # Check if specific roles exist
    test_roles = ["cfo", "ceo", "finance_manager", "hr_manager"]
    for role in test_roles:
        profile = principal_registry.get_principal_profile(role)
        if profile:
            logger.info(f"Found profile for {role}: {profile.get('name', 'N/A')}")
        else:
            logger.info(f"No profile found for {role}")
    
    # Display registry file path
    registry_path = principal_registry.get_registry_path()
    logger.info(f"Principal registry path: {registry_path}")
    
    # Check if file exists
    if Path(registry_path).exists():
        logger.info("Registry file exists")
    else:
        logger.error("Registry file does not exist")

if __name__ == "__main__":
    main()
