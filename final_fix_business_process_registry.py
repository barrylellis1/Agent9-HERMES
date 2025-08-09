#!/usr/bin/env python
"""
FINAL script to fix the Business Process Registry YAML:
1. Fixing indentation and structure issues
2. Removing ONLY the KPIs sections (implementing the single source of truth)
3. PRESERVING owner_role, stakeholder_roles, tags, display_name, etc.
4. Ensuring consistent structure with proper '- id:' entries for all processes

This script handles the file differently to produce a fully correct YAML structure.
"""

import os
import yaml
import re

def read_original_yaml(input_file):
    """Read the YAML file as text to preserve comments"""
    with open(input_file, 'r', encoding='utf-8') as f:
        return f.read()

def extract_business_processes(yaml_text):
    """Extract business processes as a list of dictionaries with correct structure"""
    # Split the text by business process entries
    process_texts = re.split(r'(?=^- id: "|^  id: ")', yaml_text, flags=re.MULTILINE)
    
    # Get the header (first element)
    header = process_texts[0]
    process_texts = process_texts[1:]
    
    # Process each business process text
    business_processes = []
    
    for process_text in process_texts:
        # Normalize indentation
        lines = process_text.strip().split('\n')
        process_dict = {}
        
        # Extract ID
        id_match = re.search(r'id: "([^"]+)"', lines[0])
        if id_match:
            process_dict['id'] = id_match.group(1)
        
        # Extract other properties
        current_key = None
        list_mode = False
        
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            
            # Skip kpis sections and their items
            if line == 'kpis:':
                list_mode = True
                current_key = 'kpis'
                continue
            
            # End of kpis section
            if list_mode and current_key == 'kpis' and line and not line.startswith('-'):
                list_mode = False
                
            # Skip list items in kpis section
            if list_mode and current_key == 'kpis' and line.startswith('-'):
                continue
                
            # Regular properties
            if ':' in line and not line.startswith('-'):
                key, value = [part.strip() for part in line.split(':', 1)]
                current_key = key
                list_mode = False
                
                if value:  # Single line property
                    process_dict[key] = value
                else:  # Multi-line property (list)
                    list_mode = True
                    process_dict[key] = []
                    
            # List items
            elif line.startswith('-') and list_mode and current_key != 'kpis':
                value = line[1:].strip()
                if current_key in process_dict and isinstance(process_dict[current_key], list):
                    process_dict[current_key].append(value)
        
        # Only add if we have an ID
        if 'id' in process_dict:
            business_processes.append(process_dict)
    
    return header, business_processes

def write_fixed_yaml(output_file, header, business_processes):
    """Write the fixed YAML file with proper structure"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write(header.rstrip() + '\n\n')
        
        # Write business processes
        for i, process in enumerate(business_processes):
            # Write process ID and add a newline before each process except the first
            if i > 0:
                f.write('\n')
            f.write(f"- id: \"{process['id']}\"\n")
            
            # Write other properties with proper indentation
            for key, value in process.items():
                if key == 'id':  # Already written
                    continue
                    
                if isinstance(value, list):
                    # List property
                    f.write(f"  {key}:\n")
                    for item in value:
                        f.write(f"    - {item}\n")
                else:
                    # Single-value property
                    f.write(f"  {key}: {value}\n")
    
    print(f"Fixed YAML written to {output_file}")

def main():
    # File paths
    src_dir = os.path.join('src', 'registry_references', 'business_process_registry', 'yaml')
    input_file = os.path.join(src_dir, 'business_process_registry.yaml')
    output_file = os.path.join(src_dir, 'business_process_registry.final.yaml')
    
    print(f"Processing {input_file}...")
    
    # Read original YAML
    yaml_text = read_original_yaml(input_file)
    
    # Extract and process business processes
    header, business_processes = extract_business_processes(yaml_text)
    
    # Write fixed YAML
    write_fixed_yaml(output_file, header, business_processes)
    
    print(f"Processed {len(business_processes)} business processes")
    print(f"Successfully removed all KPI sections while preserving other metadata")
    print("\nDone!")
    print("Please verify the output file before replacing the original.")

if __name__ == "__main__":
    main()
