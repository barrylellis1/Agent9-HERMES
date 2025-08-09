#!/usr/bin/env python
"""
Script to fix indentation issues in business_process_registry.yaml
"""

import re
import sys
import yaml
from pathlib import Path

def fix_yaml_indentation(input_file, output_file):
    """Fix YAML indentation in the business process registry file."""
    print(f"Fixing YAML indentation in {input_file}, writing to {output_file}")
    
    # Approach: Load the YAML, fix only top-level section headers and dash placement,
    # and let Python's YAML dumper handle the proper indentation for everything else
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First fix the header comments and list item indentation
    # to ensure proper parsing
    fixed_content = content
    fixed_content = re.sub(r'\s+# ([A-Za-z]+) Domain Processes', r'# \1 Domain Processes', fixed_content)
    fixed_content = re.sub(r'\s{2,}(- id:)', r'- id:', fixed_content)
    
    # Save the intermediate file
    intermediate_path = Path(input_file).with_suffix('.intermediate.yaml')
    with open(intermediate_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    # Now load the YAML, which will parse the structure correctly
    try:
        with open(intermediate_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # And dump it back with proper indentation
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write the original header comments
            for line in content.split('\n')[:8]:  # First 8 lines are header comments
                if line.startswith('#') or line.strip() == '':
                    f.write(f"{line}\n")
            
            # Write the properly indented YAML
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
        
        print(f"YAML indentation fixed! Output written to {output_file}")
        
    except Exception as e:
        print(f"Error processing YAML: {e}")
        # Fall back to regex-based approach
        print("Falling back to regex-based fix")
        regex_fix_indentation(input_file, output_file)

def regex_fix_indentation(input_file, output_file):
    """Fix indentation using regex patterns as a fallback."""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_process_block = False
    in_kpis_section = False
    
    for line in lines:
        # Fix domain headers
        if re.match(r'\s*# [A-Za-z]+ Domain Processes', line):
            fixed_lines.append(re.sub(r'\s*# ([A-Za-z]+) Domain Processes', r'# \1 Domain Processes', line))
            in_process_block = False
            in_kpis_section = False
            continue
        
        # When we hit a process ID line, mark that we're inside a process block
        if re.match(r'\s*- id:', line):
            fixed_lines.append(re.sub(r'\s*- id:', r'- id:', line))
            in_process_block = True
            in_kpis_section = False
            continue
        
        # Check if we're entering a kpis section
        if in_process_block and re.match(r'\s+kpis:', line):
            fixed_lines.append(re.sub(r'\s+kpis:', r'  kpis:', line))
            in_kpis_section = True
            continue
        
        # Inside a process block, fix property indentation
        if in_process_block:
            if in_kpis_section and re.match(r'\s+- ', line):
                # Special handling for kpis list items - indent 4 spaces from kpis: key
                fixed_lines.append(re.sub(r'\s+- ', r'    - ', line))
            # Fix property names (key: value pairs)
            elif re.match(r'\s+[a-z_]+:', line):
                fixed_lines.append(re.sub(r'\s+([a-z_]+:)', r'  \1', line))
                if not 'kpis:' in line:
                    in_kpis_section = False
            # Fix list items under properties that aren't kpis
            elif re.match(r'\s+- ', line) and not in_kpis_section:
                fixed_lines.append(re.sub(r'\s+- ', r'    - ', line))
            else:
                fixed_lines.append(line)
                if line.strip() == '' or line.strip()[0] == '#':
                    in_kpis_section = False
        else:
            fixed_lines.append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"YAML indentation fixed with regex! Output written to {output_file}")

if __name__ == "__main__":
    registry_path = "src/registry_references/business_process_registry/yaml/business_process_registry.yaml"
    output_path = "src/registry_references/business_process_registry/yaml/business_process_registry.fixed.yaml"
    fix_yaml_indentation(registry_path, output_path)
    print("Done! Review the fixed YAML file and rename it if it looks good.")

if __name__ == "__main__":
    registry_path = "src/registry_references/business_process_registry/yaml/business_process_registry.yaml"
    output_path = "src/registry_references/business_process_registry/yaml/business_process_registry.fixed.yaml"
    fix_yaml_indentation(registry_path, output_path)
    print("Done! Review the fixed YAML file and rename it if it looks good.")
