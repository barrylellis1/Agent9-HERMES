"""
Test script for the Situation Awareness Agent.

This script validates that the agent correctly loads principal profiles
and KPI definitions from external registries, and identifies potential
misalignments or gaps between profiles, registries, models, and SAP data.
"""

import sys
import os
import asyncio
import logging
import json
import yaml
import unittest.mock as mock
from pprint import pprint
from typing import Dict, List, Any, Set

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import registry factory
from src.registry.factory import RegistryFactory
from src.registry.providers.registry_provider import PrincipalProfileProvider, KPIProvider
from src.registry_references.principal_registry.principal_roles import PrincipalRole as RegistryPrincipalRole

# Import situation awareness models
from src.agents.models.situation_awareness_models import (
    PrincipalRole, 
    BusinessProcess, 
    TimeFrame, 
    ComparisonType,
    SituationDetectionRequest,
    KPIDefinition
)

# Import the agent
from src.agents.new.a9_situation_awareness_agent import create_situation_awareness_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Mock Data Product MCP Service Agent for testing
class MockDataProductMCPServiceAgent:
    async def connect(self):
        logger.info("Mock Data Product MCP Service Agent connected")
        return True

    async def disconnect(self):
        logger.info("Mock Data Product MCP Service Agent disconnected")
        return True

    async def execute_query(self, query, parameters=None):
        # Return mock data based on the query
        logger.info(f"Mock executing query: {query[:100]}...")
        if "revenue" in query.lower():
            return {"data": [{"quarter": "2023-Q1", "revenue": 1000000}, {"quarter": "2023-Q2", "revenue": 1200000}]}
        elif "expense" in query.lower():
            return {"data": [{"month": "2023-01", "expenses": 500000}, {"month": "2023-02", "expenses": 550000}]}
        # Default mock response
        return {"data": [{"value": 100}]}

async def test_agent_initialization():
    """Test that the agent initializes correctly using external registries."""
    logger.info("Testing agent initialization...")
    
    # Initialize the registry factory
    registry_factory = RegistryFactory()
    
    # Patch the Data Product MCP Service Agent
    with mock.patch('src.agents.a9_data_product_mcp_service_agent.A9DataProductMCPServiceAgent', 
                   return_value=MockDataProductMCPServiceAgent()):
        
        # Create the agent
        agent = create_situation_awareness_agent({
            "contract_path": "src/contracts/fi_star_schema.yaml"
        })
        
        # Connect to dependencies
        await agent.connect()
        
        # Validate principal profiles are loaded from registry
        logger.info(f"Loaded {len(agent.principal_profiles)} principal profiles")
        assert len(agent.principal_profiles) > 0, "No principal profiles loaded"
        
        # Validate KPIs are loaded from registry
        logger.info(f"Loaded {len(agent.kpi_registry)} KPIs")
        assert len(agent.kpi_registry) > 0, "No KPIs loaded"
        
        # Disconnect
        await agent.disconnect()
        logger.info("Agent initialization test completed successfully")

async def test_metadata_alignment():
    """Test for metadata alignment gaps between registries, models, and data."""
    logger.info("Testing metadata alignment...")
    
    # Initialize the registry factory
    registry_factory = RegistryFactory()
    
    # Load the data contract
    contract_path = "src/contracts/fi_star_schema.yaml"
    with open(contract_path, "r") as f:
        contract = yaml.safe_load(f)
    
    # Patch the Data Product MCP Service Agent
    with mock.patch('src.agents.a9_data_product_mcp_service_agent.A9DataProductMCPServiceAgent', 
                   return_value=MockDataProductMCPServiceAgent()):
        
        # Create the agent
        agent = create_situation_awareness_agent({
            "contract_path": contract_path
        })
        
        # Connect to dependencies
        await agent.connect()
        
        # 1. Check that all business processes in principal profiles match enum values
        check_business_process_alignment(agent)
        
        # 2. Check KPI definitions for completeness
        check_kpi_completeness(agent.kpi_registry)
        
        # 3. Verify SAP data model matches KPI requirements
        check_data_model_alignment(contract, agent.kpi_registry)
        
        # 4. Check for target domain consistency
        check_domain_consistency(agent)
        
        # Disconnect
        await agent.disconnect()
        logger.info("Metadata alignment test completed successfully")

def check_business_process_alignment(agent):
    """Check alignment between principal profile business processes and enum values."""
    logger.info("\n== Checking Business Process Alignment ==\n")
    
    # Get business processes from the model
    model_bps = [bp.value for bp in BusinessProcess]
    logger.info(f"Found {len(model_bps)} business processes in the model: {model_bps}")
    
    # Get business processes from the principal profiles using the registry factory
    registry_factory = RegistryFactory()
    principal_provider = registry_factory.get_principal_profile_provider()
    
    # If provider is not registered yet, get profiles directly from agent
    if principal_provider is None:
        profiles = agent.principal_profiles
    else:
        profiles = principal_provider.get_all_profiles()
    
    profile_bps = set()
    for profile in profiles.values():
        for bp in profile.business_processes:
            profile_bps.add(bp)
    
    logger.info(f"Found {len(profile_bps)} unique business processes in principal profiles")
    
    # Track business processes referenced in profiles but not in enum
    missing_enums = set()
    
    # Check each principal profile
    for role, profile in profiles.items():
        role_name = role.name if hasattr(role, "name") else str(role)
        logger.info(f"Checking profile: {role_name}")
        
        for bp_str in profile.business_processes:
            if bp_str.startswith("Finance: "):
                # Extract just the process name (without the domain prefix)
                process_name = bp_str.replace("Finance: ", "").upper().replace(" ", "_")
                
                if process_name not in model_bps:
                    missing_enums.add(process_name)
                    logger.warning(f"  - Process '{process_name}' in profile does not exist in BusinessProcess enum")
                else:
                    logger.info(f"  - Process '{process_name}' exists in BusinessProcess enum")
    
    if missing_enums:
        logger.warning(f"\nFound {len(missing_enums)} business processes missing from enum: {missing_enums}\n")
    else:
        logger.info("\nAll business processes in profiles match enum values\n")

def check_kpi_completeness(kpi_registry: Dict[str, KPIDefinition]):
    """Check KPI definitions for completeness and metadata gaps."""
    logger.info("\n== Checking KPI Completeness ==\n")
    
    # Get KPIs from the registry factory if not provided
    if not kpi_registry:
        registry_factory = RegistryFactory()
        kpi_provider = registry_factory.get_kpi_provider()
        if kpi_provider:
            kpi_registry = kpi_provider.get_all_kpis()
    
    # Check each KPI for required metadata
    incomplete_kpis = []
    
    for name, kpi in kpi_registry.items():
        missing = []
        
        # Check required metadata fields
        if not kpi.thresholds:
            missing.append("thresholds")
        if not kpi.business_processes:
            missing.append("business_processes")
        if not kpi.data_product_id:
            missing.append("data_product_id")
        if not kpi.comparison_methods:
            missing.append("comparison_methods")
        
        # Check dimensions
        if not kpi.dimensions:
            missing.append("dimensions")
        
        # Check positive trend indicator
        if not hasattr(kpi, "positive_trend_is_good"):
            missing.append("positive_trend_is_good")
        
        # Add to issues dict if any found
        if missing:
            incomplete_kpis.append((name, missing))
            logger.warning(f"KPI '{name}':\n  - " + "\n  - ".join(missing))
        else:
            logger.info(f"KPI '{name}': Complete metadata")
    
    if incomplete_kpis:
        logger.warning(f"\nFound {len(incomplete_kpis)} KPIs with metadata gaps out of {len(kpi_registry)}\n")
    else:
        logger.info(f"\nAll {len(kpi_registry)} KPIs have complete metadata\n")

def check_data_model_alignment(contract: Dict, kpi_registry: Dict[str, KPIDefinition]):
    """Check if SAP data model supports all required KPI calculations."""
    logger.info("\n== Checking Data Model Alignment ==\n")
    
    # Extract tables and columns from contract
    tables = {}
    for table in contract.get("tables", []):
        columns = set()
        for column in table.get("columns", []):
            columns.add(column["name"])
        tables[table["name"]] = columns
    
    logger.info(f"Contract defines {len(tables)} tables")
    
    # Check each KPI against available tables
    missing_tables = set()
    missing_columns = set()
    
    for name, kpi in kpi_registry.items():
        # Check base table and column
        if kpi.base_column:
            table_name = kpi.base_column.split(".")[0] if "." in kpi.base_column else None
            column_name = kpi.base_column.split(".")[1] if "." in kpi.base_column else kpi.base_column
            
            if table_name and table_name not in tables:
                missing_tables.add(table_name)
                logger.warning(f"KPI '{name}': Base table '{table_name}' not found in contract")
            elif table_name and column_name not in tables[table_name]:
                missing_columns.add(f"{table_name}.{column_name}")
                logger.warning(f"KPI '{name}': Column '{column_name}' not found in table '{table_name}'")
        
        # Check join tables
        if kpi.join_tables:
            for join_table in kpi.join_tables:
                if join_table not in tables:
                    missing_tables.add(join_table)
                    logger.warning(f"KPI '{name}': Join table '{join_table}' not found in contract")
    
    if missing_tables or missing_columns:
        logger.warning(f"\nData model misalignment detected:\n  - Missing tables: {missing_tables}\n  - Missing columns: {missing_columns}\n")
    else:
        logger.info("\nData model fully supports all KPI calculations\n")

def check_domain_consistency(agent):
    """Check consistency of domain references across the system."""
    logger.info("\n== Checking Domain Consistency ==\n")
    
    # Get target domains from agent config
    target_domains = agent.config.get("target_domains", ["Finance"])
    logger.info(f"Agent configured for domains: {target_domains}")
    
    # Initialize registry factory
    registry_factory = RegistryFactory()
    
    # Get KPIs from registry factory
    kpi_provider = registry_factory.get_kpi_provider()
    
    # If provider is not registered yet, get KPIs directly from agent
    if kpi_provider is None:
        kpis = agent.kpi_registry
    else:
        kpis = kpi_provider.get_all_kpis()
    
    # Extract business processes from KPIs
    kpi_bps = set()
    for kpi in kpis.values():
        if kpi.business_processes:
            for bp in kpi.business_processes:
                kpi_bps.add(bp)
    
    # Get principal profiles from registry factory
    principal_provider = registry_factory.get_principal_profile_provider()
    if principal_provider is None:
        profiles = agent.principal_profiles
    else:
        profiles = principal_provider.get_all_profiles()
    
    profile_bps = set()
    for profile in profiles.values():
        for bp in profile.business_processes:
            profile_bps.add(bp)
    
    # Check KPI business process domains
    kpi_domains = set()
    for kpi in kpis.values():
        for bp in kpi.business_processes:
            if ":" in bp:
                domain = bp.split(":")[0].strip()
                kpi_domains.add(domain)
    
    # Check principal profile business process domains
    profile_domains = set()
    for profile in profiles.values():
        for bp in profile.business_processes:
            if ":" in bp:
                domain = bp.split(":")[0].strip()
                profile_domains.add(domain)
    
    # Report consistency
    logger.info(f"Domains in KPI registry: {kpi_domains}")
    logger.info(f"Domains in principal profiles: {profile_domains}")
    
    # Check for mismatches
    mismatches = []
    for domain in target_domains:
        if domain not in kpi_domains:
            mismatches.append(f"Target domain '{domain}' not found in KPI registry")
        if domain not in profile_domains:
            mismatches.append(f"Target domain '{domain}' not found in principal profiles")
    
    if mismatches:
        logger.warning(f"\nDomain consistency issues:\n  - " + "\n  - ".join(mismatches) + "\n")
    else:
        logger.info(f"\nDomain references consistent across system\n")

async def main():
    """Run all tests."""
    logger.info("\n====== RUNNING SITUATION AWARENESS AGENT TESTS ======\n")
    await test_agent_initialization()
    await test_metadata_alignment()
    logger.info("\n====== ALL TESTS COMPLETED ======\n")

if __name__ == "__main__":
    asyncio.run(main())
