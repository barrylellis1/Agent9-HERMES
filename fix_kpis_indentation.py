#!/usr/bin/env python
"""
Script to fix kpis indentation in business_process_registry.yaml
"""

import re
from pathlib import Path

def fix_kpis_indentation(input_file, output_file):
    """Fix kpis indentation in the business process registry file."""
    print(f"Fixing KPIs indentation in {input_file}, writing to {output_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First, ensure all kpis: keys are properly indented with 2 spaces
    content = re.sub(r'(\n\s*)kpis:', r'\1  kpis:', content)
    
    # Then, ensure all kpis list items are indented with 4 spaces (2 more than kpis:)
    content = re.sub(r'(\n\s*kpis:\s*\n)\s*-\s', r'\1    - ', content)
    content = re.sub(r'(\n\s*-\s+"[^"]+"\s*\n)\s*-\s', r'\1    - ', content)
    
    # Write the fixed content to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"KPIs indentation fixed! Output written to {output_file}")

if __name__ == "__main__":
    input_path = "src/registry_references/business_process_registry/yaml/business_process_registry.fixed.yaml"
    output_path = "src/registry_references/business_process_registry/yaml/business_process_registry.final.yaml"
    fix_kpis_indentation(input_path, output_path)
    print("Done! Review the final YAML file and replace the original if it looks good.")
