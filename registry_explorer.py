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

# We'll use direct YAML file reading instead of importing models
# This makes the UI more robust and independent of code changes

# Set page config
st.set_page_config(
    page_title="Agent9 Registry Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import registry factory
from src.registry.factory import RegistryFactory

# Initialize registry factory
registry_factory = RegistryFactory()

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
    
    # Search for YAML files in src/registry directory
    registry_dir = Path("src/registry")
    if registry_dir.exists():
        for file_path in registry_dir.glob("**/*.yaml"):
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
        if not kpi_data or "kpis" not in kpi_data:
            st.error("Invalid KPI registry file or no KPIs found.")
            return
        
        # Display KPIs
        kpis = kpi_data["kpis"]
        kpi_names = [kpi["name"] for kpi in kpis]
        
        # KPI selection
        selected_kpi_name = st.selectbox("Select KPI", kpi_names)
        selected_kpi = next((kpi for kpi in kpis if kpi["name"] == selected_kpi_name), None)
        
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
        # Similar implementation for Principal Profiles
        st.info("Principal Profile registry explorer to be implemented")
        
    elif registry_type == "Data Product":
        st.header("Data Product Registry")
        # Similar implementation for Data Products
        st.info("Data Product registry explorer to be implemented")
        
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
        if not bp_data or "business_processes" not in bp_data:
            st.error("Invalid Business Process registry file or no Business Processes found.")
            return
        
        # Group business processes by domain
        business_processes = bp_data["business_processes"]
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
        
        # Display business processes for selected domain
        if selected_domain in domains:
            st.subheader(f"{selected_domain} Business Processes")
            
            # Check if any process in this domain is a domain-level process
            has_domain_level = any([
                ("domain" in bp and bp["domain"] == selected_domain and "display_name" in bp and ":" not in bp["display_name"]) or
                ("display_name" in bp and ":" not in bp["display_name"] and bp.get("domain", "") == selected_domain)
                for bp in domains[selected_domain]
            ])
            
            if has_domain_level:
                st.info(f"This domain has domain-level business processes.")
            
            # Display business processes
            for bp in domains[selected_domain]:
                # Determine if this is a domain-level process
                is_domain_level = False
                if "domain" in bp and bp["domain"] == selected_domain:
                    is_domain_level = True
                elif "display_name" in bp and ":" not in bp["display_name"]:
                    # If display_name doesn't have a colon, it might be a domain-level process
                    is_domain_level = True
                
                # Create expander for each business process
                display_name = bp.get("display_name", bp.get("name", "Unnamed Process"))
                with st.expander(f"{display_name} {'(Domain-Level)' if is_domain_level else ''}"):
                    # Basic info
                    st.write(f"**ID:** {bp.get('id', 'N/A')}")
                    st.write(f"**Domain:** {bp.get('domain', selected_domain)}")
                    st.write(f"**Description:** {bp.get('description', 'No description available')}")
                    
                    # Associated KPIs
                    if "kpis" in bp and bp["kpis"]:
                        st.subheader("Associated KPIs")
                        for kpi in bp["kpis"]:
                            st.write(f"- {kpi}")
                    
                    # Stakeholders
                    if "stakeholders" in bp and bp["stakeholders"]:
                        st.subheader("Stakeholders")
                        for stakeholder in bp["stakeholders"]:
                            st.write(f"- {stakeholder}")
                    
                    # Parent-child relationships
                    if "parent_id" in bp:
                        st.subheader("Parent Process")
                        st.write(f"- {bp['parent_id']}")
                    
                    if "child_ids" in bp and bp["child_ids"]:
                        st.subheader("Child Processes")
                        for child in bp["child_ids"]:
                            st.write(f"- {child}")
                    
                    # Raw YAML view
                    with st.expander("View Raw YAML"):
                        st.code(yaml.dump(bp, sort_keys=False), language="yaml")
        
        # Business Process Statistics
        st.sidebar.subheader("Business Process Statistics")
        st.sidebar.write(f"Total Business Processes: {len(business_processes)}")
        
        # Count by domain
        domain_counts = {domain: len(processes) for domain, processes in domains.items()}
        
        st.sidebar.write("Business Processes by Domain:")
        for domain, count in domain_counts.items():
            st.sidebar.write(f"- {domain}: {count}")
        
        # Check for hierarchical structure
        has_hierarchy = any(["parent_id" in bp or "child_ids" in bp for bp in business_processes])
        if has_hierarchy:
            st.sidebar.info("Hierarchical structure detected in business processes.")
        else:
            st.sidebar.info("No hierarchical structure detected in business processes.")
        
    elif registry_type == "Business Term":
        st.header("Business Term Registry")
        # Similar implementation for Business Terms
        st.info("Business Term registry explorer to be implemented")

if __name__ == "__main__":
    main()
