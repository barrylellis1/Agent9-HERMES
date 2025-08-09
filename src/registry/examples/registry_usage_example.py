"""
Registry Usage Example

This example demonstrates how to use the registry system in Agent9.
It shows how to initialize the registry, access providers, and use them.
"""

import asyncio
import logging
from typing import List

from src.registry.registry_module import initialize_registry, get_registry
from src.registry.models.business_process import BusinessProcess
from src.registry.models.kpi import KPI, ComparisonType, KPIEvaluationStatus
from src.registry.models.principal import PrincipalProfile


async def main():
    """Example usage of the registry system."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Initialize the registry (this would typically be done at app startup)
    await initialize_registry()
    
    # Get the registry factory
    registry = get_registry()
    
    # Access providers
    business_process_provider = registry.get_provider("business_process")
    kpi_provider = registry.get_provider("kpi")
    principal_provider = registry.get_provider("principal_profile")
    
    # Example 1: Find all business processes for the CFO
    cfo = principal_provider.get("cfo")
    if cfo:
        print(f"\n=== Business Processes for {cfo.name} ===")
        for process_id in cfo.business_processes:
            process = business_process_provider.get(process_id)
            if process:
                print(f"- {process.name}: {process.description or 'No description'}")
    
    # Example 2: Find all KPIs for a specific business process
    process_id = "finance_profitability_analysis"
    process = business_process_provider.get(process_id)
    kpis_for_process = kpi_provider.find_by_business_process(process_id)
    
    if process:
        print(f"\n=== KPIs for {process.name} ===")
        for kpi in kpis_for_process:
            print(f"- {kpi.name}: {kpi.description or 'No description'}")
    
    # Example 3: Find principals interested in a specific KPI
    kpi_id = "gross_margin"
    kpi = kpi_provider.get(kpi_id)
    principals_for_kpi = principal_provider.find_by_kpi(kpi_id)
    
    if kpi:
        print(f"\n=== Principals interested in {kpi.name} ===")
        for principal in principals_for_kpi:
            print(f"- {principal.name} ({principal.title})")
    
    # Example 4: Evaluate a KPI against a threshold
    if kpi:
        value = 12.5  # Example value
        comparison = ComparisonType.YOY
        status = kpi.evaluate(value, comparison)
        
        print(f"\n=== Evaluation of {kpi.name} ===")
        print(f"Value: {value}%")
        print(f"Comparison: {comparison}")
        print(f"Status: {status}")
    
    # Example 5: Legacy compatibility - accessing by enum value
    legacy_process_id = "REVENUE_GROWTH"
    process = business_process_provider.get(legacy_process_id)
    
    if process:
        print(f"\n=== Legacy Compatibility Test ===")
        print(f"Found process by legacy ID: {process.name}")
        print(f"Modern ID: {process.id}")
        print(f"Legacy ID: {process.legacy_id}")


if __name__ == "__main__":
    asyncio.run(main())
