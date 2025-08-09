#!/usr/bin/env python3
"""
Registry Validation Script

This script validates the KPI registry and ensures proper alignment with business processes,
principal profiles, and other required metadata for MVP compliance.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.append(project_root)

from src.registry_references.kpi_registry.kpi_registry import KPI_REGISTRY
from src.agents.models.situation_awareness_models import BusinessProcess, PrincipalRole
from src.registry_references.principal_registry.principal_roles import PrincipalRole as RegistryPrincipalRole


def validate_kpi_registry():
    """
    Validate the KPI registry for completeness and alignment with business processes,
    principal profiles, and other required metadata for MVP compliance.
    """
    print("Starting KPI Registry validation...")
    print(f"Found {len(KPI_REGISTRY)} KPIs in the registry.")
    
    # Define MVP scope
    mvp_business_processes = [bp.value for bp in BusinessProcess]
    
    # Validation metrics
    errors = 0
    warnings = 0
    
    # Validate each KPI
    for i, kpi in enumerate(KPI_REGISTRY, 1):
        print(f"\n\033[1m[{i}/{len(KPI_REGISTRY)}] Validating KPI: {kpi.name}\033[0m")
        
        # Check for required metadata
        if not kpi.business_processes:
            print(f"  \033[91mERROR: Missing business_processes for KPI '{kpi.name}'\033[0m")
            errors += 1
        
        if not kpi.data_product_id:
            print(f"  \033[91mERROR: Missing data_product_id for KPI '{kpi.name}'\033[0m")
            errors += 1
        
        if not kpi.thresholds or (kpi.thresholds.warning is None and kpi.thresholds.critical is None):
            print(f"  \033[93mWARNING: Missing thresholds for KPI '{kpi.name}'\033[0m")
            warnings += 1
        
        if not hasattr(kpi, 'comparison_methods') or not kpi.comparison_methods:
            print(f"  \033[93mWARNING: Missing comparison_methods for KPI '{kpi.name}'\033[0m")
            warnings += 1
        
        # Check if business processes are within MVP scope
        for bp in kpi.business_processes:
            if bp not in mvp_business_processes:
                print(f"  \033[93mWARNING: Business process '{bp}' for KPI '{kpi.name}' is outside MVP scope\033[0m")
                warnings += 1
    
    # Validate alignment between models and registries
    print("\n\033[1mValidating alignment between models and registries:\033[0m")
    
    # Check PrincipalRole alignment
    model_roles = {r.name: r.value for r in PrincipalRole}
    registry_roles = {r.name: r.value for r in RegistryPrincipalRole}
    
    print("\nPrincipalRole alignment:")
    for model_role_name, model_role_value in model_roles.items():
        found = False
        for reg_role_name, reg_role_value in registry_roles.items():
            if model_role_name.lower() == reg_role_name.lower() or reg_role_name.lower() in model_role_name.lower():
                found = True
                print(f"  \033[92mOK: {model_role_name} in model aligns with {reg_role_name} in registry\033[0m")
                break
        
        if not found:
            print(f"  \033[93mWARNING: {model_role_name} in model has no clear mapping in registry\033[0m")
            warnings += 1
    
    # Summary
    print("\n\033[1mValidation Summary:\033[0m")
    print(f"Total KPIs validated: {len(KPI_REGISTRY)}")
    print(f"Errors found: {errors}")
    print(f"Warnings found: {warnings}")
    
    if errors == 0 and warnings == 0:
        print("\n\033[92mAll validations passed successfully!\033[0m")
        return True
    elif errors == 0:
        print("\n\033[93mValidation completed with warnings but no errors.\033[0m")
        return True
    else:
        print("\n\033[91mValidation failed with errors. Please fix the issues before proceeding.\033[0m")
        return False


if __name__ == "__main__":
    success = validate_kpi_registry()
    sys.exit(0 if success else 1)
