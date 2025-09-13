"""
Registry Explorer UI

A Streamlit application for exploring and managing registry data in Agent9.
This includes KPIs, Principal Profiles, Data Products, Business Terms, etc.
"""

import streamlit as st
import yaml
import os
import json
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any, Optional

# Set page config
st.set_page_config(
    page_title="Agent9 Registry Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper functions
def load_yaml_file(file_path: str) -> Dict:
    """Load YAML file into a dictionary."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Error loading {file_path}: {str(e)}")
        return {}

def find_registry_files() -> Dict[str, List[str]]:
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

def display_kpi_details(kpi_data: Dict) -> None:
    """Display detailed information about a KPI."""
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(kpi_data["name"])
        st.write(f"**ID:** {kpi_data['id']}")
        st.write(f"**Domain:** {kpi_data['domain']}")
        st.write(f"**Unit:** {kpi_data.get('unit', 'N/A')}")
        st.write(f"**Description:** {kpi_data.get('description', 'No description available')}")
    
    with col2:
        st.write(f"**Data Product:** {kpi_data.get('data_product_id', 'N/A')}")
        st.write(f"**Owner:** {kpi_data.get('owner_role', 'N/A')}")
        st.write(f"**Tags:** {', '.join(kpi_data.get('tags', []))}")
        st.write(f"**Business Processes:** {', '.join(kpi_data.get('business_process_ids', []))}")
    
    # SQL Query
    st.subheader("SQL Query")
    st.code(kpi_data.get('sql_query', 'No SQL query available'), language="sql")
    
    # Thresholds
    if "thresholds" in kpi_data and kpi_data["thresholds"]:
        st.subheader("Thresholds")
        threshold_data = []
        for t in kpi_data["thresholds"]:
            threshold_data.append({
                "Comparison": t["comparison_type"],
                "Green": t.get("green_threshold", "N/A"),
                "Yellow": t.get("yellow_threshold", "N/A"),
                "Red": t.get("red_threshold", "N/A"),
                "Inverse Logic": "Yes" if t.get("inverse_logic", False) else "No"
            })
        st.table(pd.DataFrame(threshold_data))
    
    # Dimensions
    if "dimensions" in kpi_data and kpi_data["dimensions"]:
        st.subheader("Dimensions")
        dimension_data = []
        for d in kpi_data["dimensions"]:
            dimension_data.append({
                "Name": d["name"],
                "Field": d["field"],
                "Description": d.get("description", "N/A"),
                "Values": ", ".join(d.get("values", []))
            })
        st.table(pd.DataFrame(dimension_data))
    
    # Stakeholders
    if "stakeholder_roles" in kpi_data and kpi_data["stakeholder_roles"]:
        st.subheader("Stakeholders")
        st.write(", ".join(kpi_data["stakeholder_roles"]))

def display_principal_details(principal_data: Dict) -> None:
    """Display detailed information about a Principal Profile."""
    st.subheader(principal_data.get("name", "Unnamed Principal"))
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**ID:** {principal_data.get('id', 'N/A')}")
        st.write(f"**Role:** {principal_data.get('role', 'N/A')}")
        st.write(f"**Title:** {principal_data.get('title', 'N/A')}")
        st.write(f"**Department:** {principal_data.get('department', 'N/A')}")
    
    with col2:
        if "principal_groups" in principal_data and principal_data["principal_groups"]:
            st.write(f"**Groups:** {', '.join(principal_data['principal_groups'])}")
        if "typical_timeframes" in principal_data and principal_data["typical_timeframes"]:
            st.write(f"**Typical Timeframes:** {', '.join(principal_data['typical_timeframes'])}")
    
    # Default Filters
    if "default_filters" in principal_data and principal_data["default_filters"]:
        st.subheader("Default Filters")
        filters_data = []
        for filter_name, filter_values in principal_data["default_filters"].items():
            if isinstance(filter_values, list):
                filters_data.append({
                    "Filter": filter_name,
                    "Values": ", ".join(filter_values)
                })
            else:
                filters_data.append({
                    "Filter": filter_name,
                    "Values": str(filter_values)
                })
        st.table(pd.DataFrame(filters_data))
    
    # Responsibilities
    if "responsibilities" in principal_data and principal_data["responsibilities"]:
        st.subheader("Responsibilities")
        for resp in principal_data["responsibilities"]:
            st.write(f"- {resp}")
    
    # Business Processes
    if "business_processes" in principal_data and principal_data["business_processes"]:
        st.subheader("Business Processes")
        for process in principal_data["business_processes"]:
            st.write(f"- {process}")
    
    # KPIs
    if "kpis" in principal_data and principal_data["kpis"]:
        st.subheader("KPIs")
        for kpi in principal_data["kpis"]:
            st.write(f"- {kpi}")
    
    # Time Frame Settings
    if "time_frame" in principal_data and principal_data["time_frame"]:
        st.subheader("Time Frame Settings")
        time_frame = principal_data["time_frame"]
        st.write(f"**Default Period:** {time_frame.get('default_period', 'N/A')}")
        st.write(f"**Historical Periods:** {time_frame.get('historical_periods', 'N/A')}")
        st.write(f"**Forward Looking Periods:** {time_frame.get('forward_looking_periods', 'N/A')}")
    
    # Communication Preferences
    if "communication" in principal_data and principal_data["communication"]:
        st.subheader("Communication Preferences")
        comm = principal_data["communication"]
        st.write(f"**Detail Level:** {comm.get('detail_level', 'N/A')}")
        if "format_preference" in comm:
            st.write(f"**Format Preference:** {', '.join(comm['format_preference'])}")
        if "emphasis" in comm:
            st.write(f"**Emphasis:** {', '.join(comm['emphasis'])}")
    
    # Persona Profile
    if "persona_profile" in principal_data and principal_data["persona_profile"]:
        st.subheader("Persona Profile")
        persona = principal_data["persona_profile"]
        st.write(f"**Decision Style:** {persona.get('decision_style', 'N/A')}")
        st.write(f"**Risk Tolerance:** {persona.get('risk_tolerance', 'N/A')}")
        st.write(f"**Communication Style:** {persona.get('communication_style', 'N/A')}")
        if "values" in persona:
            st.write(f"**Values:** {', '.join(persona['values'])}")
    
    # Raw YAML view
    with st.expander("View Raw YAML"):
        st.code(yaml.dump(principal_data, sort_keys=False), language="yaml")

def display_data_product_details(dp_data: Dict) -> None:
    """Display detailed information about a Data Product."""
    st.subheader(dp_data.get("name", "Unnamed Data Product"))
    
    # Basic info
    st.write(f"**ID:** {dp_data.get('id', 'N/A')}")
    st.write(f"**Source:** {dp_data.get('source', 'N/A')}")
    st.write(f"**Description:** {dp_data.get('description', 'No description available')}")
    
    # Tables/Views
    if "tables" in dp_data and dp_data["tables"]:
        st.subheader("Tables/Views")
        for table in dp_data["tables"]:
            st.write(f"- **{table.get('name', 'Unnamed')}**: {table.get('description', 'No description')}")
    
    # Raw YAML view
    with st.expander("View Raw YAML"):
        st.code(yaml.dump(dp_data, sort_keys=False), language="yaml")

def display_business_process_details(bp_data: Dict) -> None:
    """Display detailed information about a Business Process."""
    # Get display name or ID for the header
    header_name = bp_data.get("display_name", bp_data.get("id", "Unnamed Business Process"))
    st.subheader(header_name)
    
    # Determine if this is a domain-level process
    is_domain_level = False
    if "domain" in bp_data and bp_data["domain"] == header_name:
        is_domain_level = True
    elif "display_name" in bp_data and ":" not in bp_data["display_name"]:
        # If display_name doesn't have a colon, it might be a domain-level process
        is_domain_level = True
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**ID:** {bp_data.get('id', 'N/A')}")
        st.write(f"**Display Name:** {bp_data.get('display_name', 'N/A')}")
        
        # Extract domain
        domain = None
        if "domain" in bp_data:
            domain = bp_data["domain"]
        elif "display_name" in bp_data and ":" in bp_data["display_name"]:
            domain = bp_data["display_name"].split(":", 1)[0].strip()
        
        if domain:
            st.write(f"**Domain:** {domain}")
            
        # Process type
        if is_domain_level:
            st.write("**Process Type:** Domain-level")
        else:
            st.write("**Process Type:** Specific process")
    
    with col2:
        st.write(f"**Description:** {bp_data.get('description', 'No description available')}")
        if "parent_id" in bp_data:
            st.write(f"**Parent Process:** {bp_data.get('parent_id', 'N/A')}")
    
    # Child processes
    if "child_processes" in bp_data and bp_data["child_processes"]:
        st.subheader("Child Processes")
        for child in bp_data["child_processes"]:
            if isinstance(child, dict):
                st.write(f"- **{child.get('display_name', child.get('id', 'Unnamed'))}**")
            else:
                st.write(f"- {child}")
    
    # KPIs
    if "kpis" in bp_data and bp_data["kpis"]:
        st.subheader("Associated KPIs")
        for kpi in bp_data["kpis"]:
            if isinstance(kpi, dict):
                st.write(f"- **{kpi.get('name', kpi.get('id', 'Unnamed'))}**")
            else:
                st.write(f"- {kpi}")
    
    # Stakeholders
    if "stakeholders" in bp_data and bp_data["stakeholders"]:
        st.subheader("Stakeholders")
        for stakeholder in bp_data["stakeholders"]:
            if isinstance(stakeholder, dict):
                st.write(f"- **{stakeholder.get('role', 'Unnamed')}**: {stakeholder.get('responsibility', 'N/A')}")
            else:
                st.write(f"- {stakeholder}")
    
    # Metadata
    if "metadata" in bp_data and bp_data["metadata"]:
        st.subheader("Metadata")
        metadata = bp_data["metadata"]
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                st.write(f"**{key}:**")
                st.write(value)
            else:
                st.write(f"**{key}:** {value}")
    
    # Domain-level process information
    if is_domain_level:
        st.subheader("Domain-Level Process")
        st.info("This is a domain-level business process used for high-level categorization in the MVP. " 
               "It represents a broad business area rather than a specific process.")
    
    # Raw YAML view
    with st.expander("View Raw YAML"):
        st.code(yaml.dump(bp_data, sort_keys=False), language="yaml")

# Main application
def main():
    st.title("Agent9 Registry Explorer")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    registry_type = st.sidebar.selectbox(
        "Registry Type",
        ["KPI", "Principal Profile", "Data Product", "Business Process", "Business Term"]
    )
    
    # Find registry files
    registry_files = find_registry_files()
    
    if registry_type == "KPI":
        st.header("KPI Registry")
        
        # Get KPI files
        kpi_files = registry_files["KPI"]
        if not kpi_files:
            st.warning("No KPI registry files found.")
            return
        
        # Select KPI file
        selected_file = st.selectbox("Select KPI Registry File", kpi_files)
        
        # Load KPI data
        kpi_data = load_yaml_file(selected_file)
        
        # Try different structures (kpis list or direct dict)
        kpis = []
        if "kpis" in kpi_data:
            kpis = kpi_data["kpis"]
        elif isinstance(kpi_data, list):
            kpis = kpi_data
        elif isinstance(kpi_data, dict) and "id" in kpi_data and "name" in kpi_data:
            kpis = [kpi_data]
        
        if not kpis:
            st.error("No KPIs found in the selected file.")
            st.write("File structure:")
            st.code(yaml.dump(kpi_data, sort_keys=False), language="yaml")
            return
        
        # Display KPIs
        kpi_names = [kpi.get("name", f"Unnamed KPI ({kpi.get('id', 'unknown')})") for kpi in kpis]
        
        # KPI selection
        selected_kpi_name = st.selectbox("Select KPI", kpi_names)
        selected_kpi = next((kpi for kpi in kpis if kpi.get("name") == selected_kpi_name), None)
        
        if selected_kpi:
            # Display KPI details
            display_kpi_details(selected_kpi)
            
            # Raw YAML view
            with st.expander("View Raw YAML"):
                st.code(yaml.dump(selected_kpi, sort_keys=False), language="yaml")
        
        # KPI Statistics
        st.sidebar.subheader("KPI Statistics")
        st.sidebar.write(f"Total KPIs: {len(kpis)}")
        
        # Count by domain
        domains = {}
        for kpi in kpis:
            domain = kpi.get("domain", "Unknown")
            domains[domain] = domains.get(domain, 0) + 1
        
        st.sidebar.write("KPIs by Domain:")
        for domain, count in domains.items():
            st.sidebar.write(f"- {domain}: {count}")
    
    elif registry_type == "Principal Profile":
        st.header("Principal Profile Registry")
        
        # Get Principal Profile files
        principal_files = registry_files["Principal"]
        if not principal_files:
            st.warning("No Principal Profile registry files found.")
            return
        
        # Select Principal Profile file
        selected_file = st.selectbox("Select Principal Profile Registry File", principal_files)
        
        # Load Principal Profile data
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
            st.error("No Principal Profiles found in the selected file.")
            st.write("File structure:")
            st.code(yaml.dump(principal_data, sort_keys=False), language="yaml")
            return
        
        # Display Principal Profiles
        principal_names = [p.get("name", p.get("role", f"Unnamed Principal ({p.get('id', 'unknown')})")) for p in principals]
        
        # Principal selection
        selected_principal_name = st.selectbox("Select Principal Profile", principal_names)
        selected_principal = next((p for p in principals if p.get("name") == selected_principal_name or p.get("role") == selected_principal_name), None)
        
        if selected_principal:
            # Display Principal details
            display_principal_details(selected_principal)
        
    elif registry_type == "Data Product":
        st.header("Data Product Registry")
        
        # Get Data Product files
        dp_files = registry_files["Data Product"]
        if not dp_files:
            st.warning("No Data Product registry files found.")
            return
        
        # Select Data Product file
        selected_file = st.selectbox("Select Data Product Registry File", dp_files)
        
        # Load Data Product data
        dp_data = load_yaml_file(selected_file)
        
        # Try different structures
        data_products = []
        if "data_products" in dp_data:
            data_products = dp_data["data_products"]
        elif isinstance(dp_data, list):
            data_products = dp_data
        elif isinstance(dp_data, dict) and "id" in dp_data:
            data_products = [dp_data]
        
        if not data_products:
            st.error("No Data Products found in the selected file.")
            st.write("File structure:")
            st.code(yaml.dump(dp_data, sort_keys=False), language="yaml")
            return
        
        # Display Data Products
        dp_names = [dp.get("name", f"Unnamed Data Product ({dp.get('id', 'unknown')})") for dp in data_products]
        
        # Data Product selection
        selected_dp_name = st.selectbox("Select Data Product", dp_names)
        selected_dp = next((dp for dp in data_products if dp.get("name") == selected_dp_name), None)
        
        if selected_dp:
            # Display Data Product details
            display_data_product_details(selected_dp)
        
    elif registry_type == "Business Process":
        st.header("Business Process Registry")
        
        # Get Business Process files
        bp_files = registry_files["Business Process"]
        if not bp_files:
            st.warning("No Business Process registry files found.")
            return
        
        # Select Business Process file
        selected_file = st.selectbox("Select Business Process Registry File", bp_files)
        
        # Load Business Process data
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
            st.error("No Business Processes found in the selected file.")
            st.write("File structure:")
            st.code(yaml.dump(bp_data, sort_keys=False), language="yaml")
            return
        
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
        
        # Domain selection
        domain_list = list(domains.keys())
        selected_domain = st.selectbox("Select Domain", domain_list)
        
        # Business Process selection within domain
        domain_bps = domains[selected_domain]
        bp_names = [bp.get("display_name", bp.get("id", "Unnamed Business Process")) for bp in domain_bps]
        
        selected_bp_name = st.selectbox("Select Business Process", bp_names)
        selected_bp = next((bp for bp in domain_bps if bp.get("display_name") == selected_bp_name or bp.get("id") == selected_bp_name), None)
        
        if selected_bp:
            # Display Business Process details
            display_business_process_details(selected_bp)
            
        # Business Process Statistics
        st.sidebar.subheader("Business Process Statistics")
        st.sidebar.write(f"Total Business Processes: {len(business_processes)}")
        st.sidebar.write(f"Total Domains: {len(domains)}")
        
        st.sidebar.write("Business Processes by Domain:")
        for domain, bps in domains.items():
            st.sidebar.write(f"- {domain}: {len(bps)}")
            
        # Check for hierarchical structure
        has_hierarchy = any("parent_id" in bp for bp in business_processes)
        if has_hierarchy:
            st.sidebar.write("✓ Hierarchical structure detected")
        else:
            st.sidebar.write("✗ No hierarchical structure detected")
        
    elif registry_type == "Business Term":
        st.header("Business Term Registry")
        # Similar implementation for Business Terms
        st.info("Business Term registry explorer to be implemented")

if __name__ == "__main__":
    main()
