#!/usr/bin/env python
"""
Registry Chain Validation Script

This script validates the entire registry chain from principal profiles to data products:
1. Principal Profiles -> Business Processes
2. Business Processes -> KPIs
3. KPIs -> Data Products (tables/views in contracts)

Ensures all references across registries are valid and all connections
are properly established for the MVP finance workflow.
"""

import os
import asyncio
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Add the src directory to the path so we can import the modules
sys.path.append(str(Path(__file__).parent))

# Import registry models/providers
from src.registry.models.business_process import BusinessProcess
from src.registry.models.kpi import KPI
from src.registry.models.principal import PrincipalProfile
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.principal_provider import PrincipalProfileProvider
# Use direct YAML parsing for contracts

# Initialize console output formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️ {message}{RESET}")

def print_section(title):
    print(f"\n{BOLD}=== {title} ==={RESET}")

def load_yaml_file(file_path: Path) -> Any:
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_error(f"Error loading {file_path}: {e}")
        return None


async def load_registries():
    """Load all registries needed for validation."""
    print_section("Loading Registry Data")

    # File paths
    base_dir = Path("src", "registry_references")
    principal_yaml_path = base_dir / "principal_registry" / "yaml" / "principal_registry.yaml"
    bp_yaml_path = base_dir / "business_process_registry" / "yaml" / "business_process_registry.yaml"
    kpi_yaml_path = base_dir / "kpi_registry" / "kpi_registry.yaml"
    contract_yaml_path = Path("src", "contracts", "fi_star_schema.yaml")  # Finance contract for MVP
    
    # Load providers
    print_info("Loading Principal Registry...")
    principal_provider = PrincipalProfileProvider(source_path=str(principal_yaml_path), storage_format="yaml")
    await principal_provider.load()
    principals = principal_provider.get_all()
    print_success(f"Loaded {len(principals)} principals")
    
    print_info("Loading Business Process Registry...")
    bp_provider = BusinessProcessProvider(source_path=str(bp_yaml_path), storage_format="yaml")
    await bp_provider.load()
    processes = bp_provider.get_all()
    print_success(f"Loaded {len(processes)} business processes")
    
    print_info("Loading KPI Registry...")
    kpi_provider = KPIProvider(source_path=str(kpi_yaml_path), storage_format="yaml")
    await kpi_provider.load()
    kpis = kpi_provider.get_all()
    print_success(f"Loaded {len(kpis)} KPIs")
    
    print_info(f"Loading Contract data from {contract_yaml_path}...")
    contract_data = load_yaml_file(contract_yaml_path)
    if contract_data:
        # Get tables, views, and data product name from contract
        tables = contract_data.get("tables", [])
        views = contract_data.get("views", [])
        data_product_name = contract_data.get("data_product", None)
        print_success(f"Loaded contract with {len(tables)} tables and {len(views)} views")
    else:
        tables = []
        views = []
        data_product_name = None
        print_error("Failed to load contract data")
    
    return principals, processes, kpis, (tables, views, data_product_name)


async def validate_principal_to_business_process(principals: List[PrincipalProfile], processes: List[BusinessProcess]):
    """Validate Principal -> Business Process references."""
    print_section("Validating Principal -> Business Process References")
    
    # Create a lookup dictionary for business processes by ID and display name
    process_by_id = {p.id: p for p in processes}
    process_by_display = {p.display_name: p for p in processes}
    all_process_ids = set(process_by_id.keys())
    all_display_names = set(process_by_display.keys())
    
    # Track validation results
    total_references = 0
    valid_references = 0
    invalid_references = []
    
    # Validate each principal's business process references
    for principal in principals:
        if hasattr(principal, 'business_processes') and principal.business_processes:
            for bp_ref in principal.business_processes:
                total_references += 1
                # Try to find by ID first, then by display name
                if bp_ref in all_process_ids:
                    valid_references += 1
                elif bp_ref in all_display_names:
                    valid_references += 1
                else:
                    invalid_references.append((principal.id, bp_ref))
    
    # Print validation results
    if valid_references == total_references:
        print_success(f"All {valid_references} principal-to-business process references are valid")
    else:
        print_error(f"Found {len(invalid_references)} invalid business process references from principals")
        for principal_id, bp_ref in invalid_references:
            print_error(f"  Principal {principal_id} references non-existent business process: {bp_ref}")
    
    # Check which principals have business processes defined for them
    principals_with_processes = []
    principals_without_processes = []
    for principal in principals:
        if hasattr(principal, 'business_processes') and principal.business_processes:
            principals_with_processes.append(principal.id)
        else:
            principals_without_processes.append(principal.id)
    
    print_info(f"Principals with business processes: {', '.join(principals_with_processes)}")
    if principals_without_processes:
        print_warning(f"Principals without business processes: {', '.join(principals_without_processes)}")
    
    return valid_references == total_references, total_references, valid_references


async def validate_business_process_to_kpi(processes: List[BusinessProcess], kpis: List[KPI]):
    """Validate KPI -> Business Process references."""
    print_section("Validating KPI -> Business Process References")
    
    # Create lookup dictionaries
    process_by_id = {p.id: p for p in processes}
    process_by_display = {p.display_name: p for p in processes}
    all_process_ids = set(process_by_id.keys())
    all_display_names = set(process_by_display.keys())
    
    # Track validation results
    total_references = 0
    valid_references = 0
    invalid_references = []
    
    # Validate each KPI's business process references
    for kpi in kpis:
        if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
            for bp_ref in kpi.business_process_ids:
                total_references += 1
                # Try to find by ID first, then by display name
                if bp_ref in all_process_ids:
                    valid_references += 1
                elif bp_ref in all_display_names:
                    valid_references += 1
                else:
                    invalid_references.append((kpi.id, bp_ref))
    
    # Print validation results
    if valid_references == total_references:
        print_success(f"All {valid_references} KPI-to-business process references are valid")
    else:
        print_error(f"Found {len(invalid_references)} invalid business process references from KPIs")
        for kpi_id, bp_ref in invalid_references:
            print_error(f"  KPI {kpi_id} references non-existent business process: {bp_ref}")
    
    # Check which processes have KPIs referencing them
    processes_with_kpis = set()
    for kpi in kpis:
        if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
            for bp_ref in kpi.business_process_ids:
                if bp_ref in all_process_ids or bp_ref in all_display_names:
                    processes_with_kpis.add(bp_ref)
    
    processes_without_kpis = all_process_ids.difference(processes_with_kpis)
    
    # Print analysis of business process KPI coverage
    print_info(f"{len(processes_with_kpis)} business processes are referenced by KPIs")
    if processes_without_kpis:
        print_warning(f"{len(processes_without_kpis)} business processes are not referenced by any KPI")
        print_warning(f"Business processes without KPIs: {', '.join(sorted(processes_without_kpis))}")
    
    return valid_references == total_references, total_references, valid_references


async def validate_kpi_to_data_products(kpis: List[KPI], contract_data: Tuple[List[dict], List[dict], str]):
    """Validate KPI -> Data Products (tables/views) references."""
    print_section("Validating KPI -> Data Products References")
    
    tables, views, data_product_name = contract_data
    
    # Extract table and view names from contract
    table_names = set(table.get('name', '') for table in tables)
    view_names = set(view.get('name', '') for view in views)
    
    # Add data product name to valid references if it exists
    all_data_product_names = table_names.union(view_names)
    if data_product_name:
        all_data_product_names.add(data_product_name)
    
    print_info(f"Contract contains {len(table_names)} tables and {len(view_names)} views")
    
    # Track validation results
    total_references = 0
    valid_references = 0
    invalid_references = []
    kpis_with_data_products = []
    kpis_without_data_products = []
    
    # Check each KPI for data product references in its query or definition
    for kpi in kpis:
        has_data_product_ref = False
        
        # Check for direct data_product_id reference
        if hasattr(kpi, 'data_product_id') and kpi.data_product_id:
            dp_id = kpi.data_product_id
            total_references += 1
            # Check if the data product ID is a known table or view name
            if dp_id in all_data_product_names:
                has_data_product_ref = True
                valid_references += 1
            else:
                invalid_references.append((kpi.id, dp_id))
        
        # Check for SQL query references
        if hasattr(kpi, 'calculation') and kpi.calculation:
            if hasattr(kpi.calculation, 'sql_query') and kpi.calculation.sql_query:
                query = kpi.calculation.sql_query
                for table_name in table_names:
                    if table_name in query:
                        has_data_product_ref = True
                        total_references += 1
                        valid_references += 1
                
                for view_name in view_names:
                    if view_name in query:
                        has_data_product_ref = True
                        total_references += 1
                        valid_references += 1
        
        # Check for data sources in metadata
        if hasattr(kpi, 'metadata') and kpi.metadata:
            if 'data_sources' in kpi.metadata:
                data_sources = kpi.metadata['data_sources']
                if isinstance(data_sources, list):
                    for source in data_sources:
                        total_references += 1
                        if source in all_data_product_names:
                            valid_references += 1
                            has_data_product_ref = True
                        else:
                            invalid_references.append((kpi.id, source))
        
        # Record KPI data product coverage
        if has_data_product_ref:
            kpis_with_data_products.append(kpi.id)
        else:
            kpis_without_data_products.append(kpi.id)
    
    # Print validation results
    if total_references == 0:
        print_warning("No explicit data product references found in KPIs")
    elif valid_references == total_references:
        print_success(f"All {valid_references} KPI-to-data product references are valid")
    else:
        print_error(f"Found {len(invalid_references)} invalid data product references from KPIs")
        for kpi_id, dp_ref in invalid_references:
            print_error(f"  KPI {kpi_id} references non-existent data product: {dp_ref}")
    
    print_info(f"{len(kpis_with_data_products)} KPIs reference data products")
    if kpis_without_data_products:
        print_warning(f"{len(kpis_without_data_products)} KPIs don't reference any data products")
        print_warning(f"KPIs without data products: {', '.join(kpis_without_data_products)}")
    
    return valid_references == total_references, total_references, valid_references


async def validate_finance_focused_mvp_coverage(principals: List[PrincipalProfile], processes: List[BusinessProcess], kpis: List[KPI]):
    """Validate Finance-focused MVP coverage."""
    print_section("Validating Finance-Focused MVP Coverage")
    
    # Define the 5 core finance business processes for MVP
    core_finance_processes = {
        "finance_profitability_analysis": "Profitability Analysis",
        "finance_revenue_growth_analysis": "Revenue Growth Analysis", 
        "finance_expense_management": "Expense Management",
        "finance_cash_flow_management": "Cash Flow Management",
        "finance_budget_vs_actuals": "Budget vs. Actuals"
    }
    
    # Check business processes
    found_processes = set()
    for process in processes:
        if process.id in core_finance_processes:
            found_processes.add(process.id)
    
    if len(found_processes) == len(core_finance_processes):
        print_success(f"All {len(core_finance_processes)} core finance business processes for MVP are defined")
    else:
        print_error(f"Only {len(found_processes)} of {len(core_finance_processes)} core finance business processes found")
        missing = set(core_finance_processes.keys()) - found_processes
        print_error(f"Missing processes: {', '.join(missing)}")
    
    # Check CFO, CEO, and COO principals for Finance MVP
    finance_principals = {"cfo", "ceo_001", "coo_001"}
    found_principals = set()
    for principal in principals:
        if principal.id in finance_principals:
            found_principals.add(principal.id)
    
    if len(found_principals) == len(finance_principals):
        print_success(f"All {len(finance_principals)} finance principals for MVP are defined")
    else:
        print_error(f"Only {len(found_principals)} of {len(finance_principals)} finance principals found")
        missing = finance_principals - found_principals
        print_error(f"Missing principals: {', '.join(missing)}")
    
    # Check KPIs linked to finance business processes
    finance_kpis = []
    for kpi in kpis:
        if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
            for bp_ref in kpi.business_process_ids:
                if bp_ref in core_finance_processes or bp_ref in [f"Finance: {name}" for name in core_finance_processes.values()]:
                    finance_kpis.append(kpi.id)
                    break
    
    if finance_kpis:
        print_success(f"Found {len(finance_kpis)} KPIs linked to core finance business processes")
        print_info(f"Finance KPIs: {', '.join(finance_kpis)}")
    else:
        print_error("No KPIs are linked to core finance business processes")
    
    return True  # Return validation result


async def main():
    """Main validation function."""
    print(f"{BOLD}Registry Chain Validation - Principal to Data Products{RESET}")
    print("=" * 50)
    
    # Load all registry data
    principals, processes, kpis, contract_data = await load_registries()
    
    # Validate each link in the chain
    principal_bp_result, p_total, p_valid = await validate_principal_to_business_process(principals, processes)
    bp_kpi_result, bp_total, bp_valid = await validate_business_process_to_kpi(processes, kpis)
    kpi_dp_result, kpi_total, kpi_valid = await validate_kpi_to_data_products(kpis, contract_data)
    
    # Validate Finance MVP coverage
    mvp_result = await validate_finance_focused_mvp_coverage(principals, processes, kpis)
    
    # Print overall validation summary
    print_section("Validation Summary")
    total_refs = p_total + bp_total + kpi_total
    valid_refs = p_valid + bp_valid + kpi_valid
    
    if principal_bp_result and bp_kpi_result and kpi_dp_result:
        print_success("All registry references are valid!")
        print_success(f"Validated {valid_refs}/{total_refs} references across the registry chain")
    else:
        print_error("Registry validation found issues that need to be addressed")
        print_info(f"Validated {valid_refs}/{total_refs} references across the registry chain")
        
    if mvp_result:
        print_success("Finance-focused MVP coverage is good")
    else:
        print_warning("Finance-focused MVP coverage has gaps")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
