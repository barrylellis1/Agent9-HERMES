#!/usr/bin/env python
"""
Script to completely fix all indentation issues in business_process_registry.yaml
This is a line-by-line approach to ensure proper indentation for all elements
"""

def fix_yaml_indentation(input_file, output_file):
    """Fix all indentation issues in the business process registry file."""
    print(f"Fixing complete YAML indentation in {input_file}, writing to {output_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_process_block = False
    in_kpis_section = False
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith('#'):
            fixed_lines.append(line)
            continue
            
        # Process entry starts
        if stripped_line.startswith('- id:'):
            fixed_lines.append(f"- {stripped_line[2:]}\n")
            in_process_block = True
            in_kpis_section = False
            continue
            
        # Properties within a process entry
        if in_process_block:
            # Handle kpis property
            if stripped_line == 'kpis:':
                fixed_lines.append(f"  kpis:\n")
                in_kpis_section = True
                continue
                
            # Handle KPI list items
            if in_kpis_section and stripped_line.startswith('-'):
                fixed_lines.append(f"    {stripped_line}\n")
                continue
                
            # Handle other properties (name, domain, etc.)
            if ':' in stripped_line and not stripped_line.startswith('-'):
                fixed_lines.append(f"  {stripped_line}\n")
                if not 'kpis:' in stripped_line:
                    in_kpis_section = False
                continue
        
        # Other lines (preserve as is)
        fixed_lines.append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"YAML indentation fully fixed! Output written to {output_file}")

if __name__ == "__main__":
    registry_path = "src/registry_references/business_process_registry/yaml/business_process_registry.yaml"
    output_path = "src/registry_references/business_process_registry/yaml/business_process_registry.complete.yaml"
    fix_yaml_indentation(registry_path, output_path)
    print("Done! Review the final YAML file and replace the original if it looks good.")
