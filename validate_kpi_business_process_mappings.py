#!/usr/bin/env python
"""
Script to validate KPI-to-Business Process mappings in the KPI Registry.
This implements the single source of truth approach where KPI-to-business process
mappings are defined only in the KPI Registry.

The script checks:
1. Every KPI has at least one business process ID referenced
2. All referenced business process IDs actually exist in the business process registry
"""

import yaml
import os
from pathlib import Path
import sys

def load_yaml_file(file_path):
    """Load a YAML file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def validate_kpi_business_process_mappings():
    """
    Validate all KPI-to-Business Process mappings in the KPI Registry.
    """
    # File paths
    base_dir = Path("src", "registry_references")
    kpi_registry_path = base_dir / "kpi_registry" / "kpi_registry.yaml"
    bp_registry_path = base_dir / "business_process_registry" / "yaml" / "business_process_registry.yaml"
    
    print(f"Loading KPI registry from: {kpi_registry_path}")
    kpi_registry = load_yaml_file(kpi_registry_path)
    if not kpi_registry:
        return False

    print(f"Loading business process registry from: {bp_registry_path}")
    bp_registry = load_yaml_file(bp_registry_path)
    if not bp_registry:
        return False
        
    # Build a set of valid business process IDs
    bp_ids = {bp["id"] for bp in bp_registry}
    print(f"Found {len(bp_ids)} business processes in registry")
    
    # Check KPI-to-BP mappings
    kpis = kpi_registry.get('kpis', [])
    print(f"Checking {len(kpis)} KPIs for business process mappings...")
    
    issues_found = 0
    kpis_with_no_bp = []
    invalid_bp_references = {}
    
    for kpi in kpis:
        kpi_id = kpi.get('id')
        bp_refs = kpi.get('business_process_ids', [])
        
        # Check if KPI has any business process references
        if not bp_refs:
            issues_found += 1
            kpis_with_no_bp.append(kpi_id)
            continue
            
        # Check if all referenced business processes exist
        invalid_refs = [bp_id for bp_id in bp_refs if bp_id not in bp_ids]
        if invalid_refs:
            issues_found += 1
            invalid_bp_references[kpi_id] = invalid_refs
    
    # Report results
    print("\n=== KPI-to-Business Process Mapping Validation Results ===")
    
    if issues_found == 0:
        print("✅ All KPIs have valid business process references!")
        print(f"✅ All {len(kpis)} KPIs are properly mapped to business processes")
        return True
        
    print(f"❌ Found {issues_found} KPIs with business process mapping issues:")
    
    if kpis_with_no_bp:
        print(f"\n❌ {len(kpis_with_no_bp)} KPIs have no business process references:")
        for kpi_id in kpis_with_no_bp:
            print(f"  - {kpi_id}")
            
    if invalid_bp_references:
        print(f"\n❌ {len(invalid_bp_references)} KPIs reference non-existent business processes:")
        for kpi_id, invalid_refs in invalid_bp_references.items():
            print(f"  - {kpi_id}: {', '.join(invalid_refs)}")
            
    return False

if __name__ == "__main__":
    success = validate_kpi_business_process_mappings()
    sys.exit(0 if success else 1)
