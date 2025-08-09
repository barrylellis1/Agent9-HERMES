#!/usr/bin/env python
"""
Script to manually fix the Business Process Registry YAML by:
1. Fixing indentation issues
2. Removing ONLY the KPIs sections (implementing the single source of truth)
3. PRESERVING owner_role, stakeholder_roles, tags, display_name, etc.

This script uses a line-by-line approach rather than relying on the YAML parser.
"""

import os
import re

def fix_business_process_registry_keep_roles(input_file, output_file):
    """Fix indentation issues and remove ONLY KPIs sections from the business process registry."""
    print(f"Processing {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    skip_mode = False
    kpi_sections_removed = 0
    current_section = None
    
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
            current_section = None
            
        # Handle kpis section - skip it and its items
        elif re.match(r'^\s*kpis:\s*$', line):
            skip_mode = True
            current_section = 'kpis'
            kpi_sections_removed += 1
            i += 1
            # Skip all kpi items (lines starting with - in the indented section)
            while i < len(lines) and (not lines[i].strip().startswith('- id:') and 
                  lines[i].strip().startswith('-')):
                i += 1
            continue
            
        # Handle other property headers (owner_role, stakeholder_roles, etc.)
        elif ':' in line and not line.strip().startswith('-'):
            property_name = line.split(':', 1)[0].strip()
            
            if property_name != 'kpis':
                # Not a KPI section, preserve it with proper indentation
                skip_mode = False
                current_section = property_name
                property_content = line.strip()
                fixed_lines.append(f"  {property_content}\n")
                
        # Handle list items under properties like stakeholder_roles
        elif line.strip().startswith('-') and not skip_mode:
            list_item = line.strip()
            fixed_lines.append(f"    {list_item}\n")
            
        # Add blank lines
        elif not line.strip() and not skip_mode:
            fixed_lines.append("\n")
            
        else:
            # Regular line - only increment if we didn't skip anything
            if not skip_mode:
                i += 1
            else:
                i += 1
                continue
                
        # Normal increment when not in a special case
        if not 'continue' in locals():
            i += 1
    
    # Write fixed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"Removed {kpi_sections_removed} KPI sections")
    print(f"Fixed business process registry saved to: {output_file}")
    print(f"Preserved all owner_role, stakeholder_roles, tags, and other metadata")

if __name__ == "__main__":
    # File paths
    src_dir = os.path.join('src', 'registry_references', 'business_process_registry', 'yaml')
    input_file = os.path.join(src_dir, 'business_process_registry.yaml')
    output_file = os.path.join(src_dir, 'business_process_registry.fixed_with_roles.yaml')
    
    fix_business_process_registry_keep_roles(input_file, output_file)
    print("\nDone!")
    print("Please verify the output file before replacing the original.")
