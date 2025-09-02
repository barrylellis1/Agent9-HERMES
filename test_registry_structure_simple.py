#!/usr/bin/env python
"""
Simple test script to examine the registry structure.
This script focuses only on loading and examining the registry structure.
"""

import os
import sys
import yaml
import logging
from pprint import pformat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("registry_test")

def load_registry_from_file():
    """Load the principal registry directly from the YAML file."""
    try:
        # Path to the registry file
        registry_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "src", "registry", "principal", "principal_registry.yaml")
        
        logger.info(f"Attempting to load registry from: {registry_path}")
        
        if not os.path.exists(registry_path):
            logger.error(f"Registry file not found at: {registry_path}")
            return None
        
        with open(registry_path, 'r') as f:
            registry_data = yaml.safe_load(f)
        
        logger.info(f"Successfully loaded registry file")
        return registry_data
    
    except Exception as e:
        logger.error(f"Error loading registry file: {str(e)}", exc_info=True)
        return None

def examine_registry_structure(registry_data):
    """Examine the structure of the registry data."""
    if not registry_data:
        logger.error("No registry data to examine")
        return
    
    logger.info(f"Registry top-level keys: {list(registry_data.keys())}")
    
    # Check for principals
    if "principals" in registry_data:
        principals = registry_data["principals"]
        logger.info(f"Found {len(principals)} principals in registry")
        
        # Print details of the first few principals
        for i, principal in enumerate(principals[:3]):  # Show first 3 principals
            logger.info(f"\nPrincipal {i+1}:")
            logger.info(f"  ID: {principal.get('id')}")
            logger.info(f"  Name: {principal.get('name')}")
            logger.info(f"  Role: {principal.get('role')}")
            
            # Print all keys in the principal
            logger.info(f"  Keys: {list(principal.keys())}")
            
            # Print business processes if available
            if "business_processes" in principal:
                logger.info(f"  Business Processes: {principal['business_processes']}")
            
            # Print persona profile if available
            if "persona_profile" in principal:
                logger.info(f"  Persona Profile Keys: {list(principal['persona_profile'].keys())}")
                logger.info(f"  Decision Style: {principal['persona_profile'].get('decision_style')}")
                logger.info(f"  Communication Style: {principal['persona_profile'].get('communication_style')}")
    else:
        logger.warning("No 'principals' key found in registry data")
    
    # Check for roles
    if "roles" in registry_data:
        roles = registry_data["roles"]
        logger.info(f"\nFound {len(roles)} roles in registry")
        
        # Print details of the first few roles
        for i, role in enumerate(roles[:3]):  # Show first 3 roles
            logger.info(f"\nRole {i+1}:")
            logger.info(f"  ID: {role.get('id')}")
            logger.info(f"  Name: {role.get('name')}")
            logger.info(f"  Keys: {list(role.keys())}")
    else:
        logger.warning("No 'roles' key found in registry data")

def main():
    """Main function."""
    try:
        logger.info("Starting registry structure test")
        
        # Load registry from file
        registry_data = load_registry_from_file()
        if not registry_data:
            logger.error("Failed to load registry data")
            return
        
        # Examine registry structure
        examine_registry_structure(registry_data)
        
        logger.info("Registry structure test completed")
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
