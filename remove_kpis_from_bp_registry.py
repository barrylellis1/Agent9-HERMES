#!/usr/bin/env python
"""
Script to remove KPIs from Business Process Registry YAML.
This implements the single source of truth approach where KPI-to-business process
mappings are defined only in the KPI Registry.
"""

import yaml
import os

def remove_kpis_from_business_processes(input_file, output_file):
    """
    Remove 'kpis' field from all business processes in the YAML file.
    Also fixes indentation issues with the YAML.
    """
    print(f"Processing Business Process Registry YAML: {input_file}")
    
    # Load YAML with safe loader
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return False
            
    # Process data if it's a list
    if not isinstance(data, list):
        print(f"Error: YAML root should be a list, got {type(data)}")
        return False
        
    # Remove kpis field from each business process
    kpi_counts = 0
    for process in data:
        if 'kpis' in process:
            kpi_counts += 1
            del process['kpis']
    
    # Write modified data back to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Removed 'kpis' field from {kpi_counts} business processes")
    print(f"Written cleaned business process registry to {output_file}")
    return True

def main():
    # File paths
    src_dir = os.path.join('src', 'registry_references', 'business_process_registry', 'yaml')
    input_file = os.path.join(src_dir, 'business_process_registry.yaml')
    output_file = os.path.join(src_dir, 'business_process_registry.no_kpis.yaml')
    
    success = remove_kpis_from_business_processes(input_file, output_file)
    if success:
        print("Business Process Registry successfully updated to remove KPI references.")
        print("KPI-to-business process mappings should now be maintained only in the KPI Registry.")
    else:
        print("Failed to update Business Process Registry.")

if __name__ == "__main__":
    main()
