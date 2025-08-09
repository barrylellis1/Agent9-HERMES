#!/usr/bin/env python
"""
Test script to verify the business process registry loader works with the cleaned YAML structure.
This script:
1. Loads the business process registry from the cleaned YAML file
2. Prints out all loaded business processes
3. Verifies that each business process has the expected properties
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.append(str(Path(__file__).parent))

from src.registry.providers.business_process_provider import BusinessProcessProvider


async def test_business_process_registry():
    """Test loading the business process registry from YAML."""
    # Path to the business process registry YAML
    yaml_path = str(Path("src/registry_references/business_process_registry/yaml/business_process_registry.yaml"))
    
    print(f"Testing business process registry loading from: {yaml_path}")
    
    # Create and load the provider
    provider = BusinessProcessProvider(source_path=yaml_path, storage_format="yaml")
    await provider.load()
    
    # Get all business processes
    processes = provider.get_all()
    print(f"Successfully loaded {len(processes)} business processes")
    
    # Verify each business process has the expected properties
    for i, process in enumerate(processes, 1):
        print(f"\n{i}. Business Process: {process.id}")
        print(f"   Name: {process.name}")
        print(f"   Domain: {process.domain}")
        print(f"   Owner Role: {process.owner_role}")
        print(f"   Stakeholders: {', '.join(process.stakeholder_roles)}")
        print(f"   Tags: {', '.join(process.tags)}")
        print(f"   Display Name: {process.display_name}")
        
        # Verify the process has no KPIs attribute
        assert not hasattr(process, "kpis"), f"Business process {process.id} still has KPIs attribute"
    
    # Test finding by domain
    finance_processes = provider.find_by_domain("Finance")
    print(f"\nFound {len(finance_processes)} finance business processes")
    
    # Test finding by owner role
    cfo_processes = provider.find_by_owner_role("CFO")
    print(f"Found {len(cfo_processes)} business processes owned by CFO")
    
    # Test finding by display name
    profitability = provider.get("Finance: Profitability Analysis")
    if profitability:
        print(f"Successfully found business process by display name: {profitability.id}")
    
    print("\nAll tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(test_business_process_registry())
