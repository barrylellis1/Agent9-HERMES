#!/usr/bin/env python
"""
Script to manually fix the Business Process Registry YAML by:
1. Fixing indentation issues
2. Removing KPIs sections (implementing the single source of truth)

This script uses a line-by-line approach rather than relying on the YAML parser.
"""

import os
import re

def manual_fix_business_process_registry(input_file, output_file):
    """Fix indentation issues and remove KPIs sections from the business process registry."""
    print(f"Processing {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    skip_mode = False
    kpi_sections_removed = 0
    
    # First pass - get header
    for i, line in enumerate(lines):
        if i < 8:  # Keep header comments intact
            fixed_lines.append(line)
            continue
        else:
            break
            
    # Second pass - process business processes
    i = 8
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Process entry starts
        if line.strip().startswith('- id:'):
            # Start of a new business process
            fixed_lines.append(f"{line}\n")
            skip_mode = False
            
        # Handle kpis section - skip it and its items
        elif re.match(r'^\s*kpis:\s*$', line):
            skip_mode = True
            kpi_sections_removed += 1
            i += 1
            # Skip all kpi items (lines starting with - in the indented section)
            while i < len(lines) and (not lines[i].strip().startswith('- id:') and 
                  (lines[i].strip().startswith('-') or not lines[i].strip())):
                i += 1
            continue
            
        # Don't skip other properties
        elif line.strip() and ':' in line and not line.strip().startswith('-'):
            if not skip_mode:
                # Ensure proper indentation - 2 spaces
                property_content = line.strip()
                fixed_lines.append(f"  {property_content}\n")
                
        # List items under properties (like stakeholder_roles items)
        elif line.strip().startswith('-') and not skip_mode:
            list_item = line.strip()
            fixed_lines.append(f"    {list_item}\n")
            
        # Add blank lines
        elif not line.strip() and not skip_mode:
            fixed_lines.append("\n")
            
        i += 1
    
    # Write fixed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"Removed {kpi_sections_removed} KPI sections")
    print(f"Fixed business process registry saved to: {output_file}")

if __name__ == "__main__":
    # File paths
    src_dir = os.path.join('src', 'registry_references', 'business_process_registry', 'yaml')
    input_file = os.path.join(src_dir, 'business_process_registry.yaml')
    output_file = os.path.join(src_dir, 'business_process_registry.fixed_no_kpis.yaml')
    
    manual_fix_business_process_registry(input_file, output_file)
    print("\nDone!")
    print("Please verify the output file before replacing the original.")
