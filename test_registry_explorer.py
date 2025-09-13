"""
Test script for registry explorer functionality
"""

import yaml
from pathlib import Path

def load_yaml_file(file_path):
    """Load YAML file into a dictionary."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return {}

def find_registry_files():
    """Find all registry YAML files in the project."""
    registry_files = {
        "KPI": [],
        "Principal": [],
        "Data Product": [],
        "Business Process": [],
        "Business Term": [],
        "Other": []
    }
    
    # Search for YAML files in src/registry directory and root directory
    search_dirs = [Path("src/registry"), Path(".")]
    
    for base_dir in search_dirs:
        if base_dir.exists():
            for file_path in base_dir.glob("**/*.yaml"):
                file_str = str(file_path)
                if "kpi" in file_str.lower():
                    registry_files["KPI"].append(file_str)
                elif "principal" in file_str.lower() or "profile" in file_str.lower():
                    registry_files["Principal"].append(file_str)
                elif "data_product" in file_str.lower() or "dataproduct" in file_str.lower():
                    registry_files["Data Product"].append(file_str)
                elif "business_process" in file_str.lower() or "businessprocess" in file_str.lower():
                    registry_files["Business Process"].append(file_str)
                elif "business_term" in file_str.lower() or "businessterm" in file_str.lower():
                    registry_files["Business Term"].append(file_str)
                else:
                    registry_files["Other"].append(file_str)
    
    return registry_files

def test_business_process_registry():
    """Test loading and processing business process registry files."""
    registry_files = find_registry_files()
    
    # Get Business Process files
    bp_files = registry_files["Business Process"]
    if not bp_files:
        print("No Business Process registry files found.")
        return
    
    print(f"Found {len(bp_files)} Business Process registry files:")
    for file in bp_files:
        print(f"  - {file}")
    
    # Load the first Business Process file
    selected_file = bp_files[0]
    print(f"\nLoading {selected_file}...")
    bp_data = load_yaml_file(selected_file)
    
    # Try different structures
    business_processes = []
    if "business_processes" in bp_data:
        business_processes = bp_data["business_processes"]
    elif "processes" in bp_data:
        business_processes = bp_data["processes"]
    elif isinstance(bp_data, list):
        business_processes = bp_data
    elif isinstance(bp_data, dict) and "id" in bp_data:
        business_processes = [bp_data]
    
    if not business_processes:
        print("No Business Processes found in the selected file.")
        print("File structure:")
        print(yaml.dump(bp_data, sort_keys=False))
        return
    
    print(f"\nFound {len(business_processes)} Business Processes")
    
    # Group by domain for easier navigation
    domains = {}
    for bp in business_processes:
        # Extract domain from display_name or use explicit domain field
        domain = None
        if "domain" in bp:
            domain = bp["domain"]
        elif "display_name" in bp and ":" in bp["display_name"]:
            domain = bp["display_name"].split(":", 1)[0].strip()
        else:
            domain = "Other"
        
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(bp)
    
    print(f"\nBusiness Processes by Domain:")
    for domain, bps in domains.items():
        print(f"  - {domain}: {len(bps)}")
        # Print first business process in each domain
        if bps:
            first_bp = bps[0]
            print(f"    Example: {first_bp.get('display_name', first_bp.get('id', 'Unnamed'))}")
    
    # Check for hierarchical structure
    has_hierarchy = any("parent_id" in bp for bp in business_processes)
    if has_hierarchy:
        print("\n[+] Hierarchical structure detected")
    else:
        print("\n[-] No hierarchical structure detected")

def test_principal_registry():
    """Test loading and processing principal registry files."""
    registry_files = find_registry_files()
    
    # Get Principal files
    principal_files = registry_files["Principal"]
    if not principal_files:
        print("No Principal registry files found.")
        return
    
    print(f"Found {len(principal_files)} Principal registry files:")
    for file in principal_files:
        print(f"  - {file}")
    
    # Load the first Principal file
    selected_file = principal_files[0]
    print(f"\nLoading {selected_file}...")
    principal_data = load_yaml_file(selected_file)
    
    # Try different structures
    principals = []
    if "principals" in principal_data:
        principals = principal_data["principals"]
    elif "profiles" in principal_data:
        principals = principal_data["profiles"]
    elif isinstance(principal_data, list):
        principals = principal_data
    elif isinstance(principal_data, dict) and "role" in principal_data:
        principals = [principal_data]
    
    if not principals:
        print("No Principal Profiles found in the selected file.")
        print("File structure:")
        print(yaml.dump(principal_data, sort_keys=False))
        return
    
    print(f"\nFound {len(principals)} Principal Profiles")
    
    # Check business processes in principal profiles
    for principal in principals:
        name = principal.get("name", principal.get("role", "Unnamed"))
        print(f"\nPrincipal: {name}")
        
        if "business_processes" in principal:
            business_processes = principal["business_processes"]
            print(f"  Business Processes: {business_processes}")
        else:
            print("  No business processes defined")

if __name__ == "__main__":
    print("Testing Registry Explorer Functionality\n")
    print("=" * 50)
    print("Testing Business Process Registry:")
    print("=" * 50)
    test_business_process_registry()
    
    print("\n" + "=" * 50)
    print("Testing Principal Registry:")
    print("=" * 50)
    test_principal_registry()
