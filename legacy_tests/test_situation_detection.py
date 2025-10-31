#!/usr/bin/env python
"""
Situation Detection Test Script

A focused test for the Situation Awareness Agent's situation detection capability.
Tests the basic flow of the agent with the CFO principal profile.

This script follows the Agent9 architecture where:
1. Decision Studio UI interacts with the Orchestrator Agent
2. Orchestrator Agent manages agent interactions and workflows
3. Individual agents handle domain-specific tasks

Since we don't have a full Orchestrator Agent implementation yet, this script
implements a simplified test harness that mimics the orchestration pattern.
"""

import pytest
pytestmark = pytest.mark.skip(reason="Legacy root-level test not aligned with HERMES test layout; run tests under tests/ instead")

import asyncio
import os
import sys
import uuid
import logging
import argparse
from pprint import pprint
from typing import Dict, Any, List, Optional
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import required models and agent
from src.agents.models.situation_awareness_models import (
    PrincipalRole,
    PrincipalContext,
    BusinessProcess,
    TimeFrame,
    ComparisonType,
    SituationDetectionRequest,
    SituationDetectionResponse
)
from src.agents.new.a9_situation_awareness_agent import create_situation_awareness_agent

# Configure logging - set to DEBUG level to see all logs
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG instead of INFO to see more details
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set all loggers to DEBUG
for logger_name in ['__main__', 'src.agents.new.a9_situation_awareness_agent', 
                   'src.agents.a9_data_product_mcp_service_agent']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info("LOGGER INITIALIZED - ALL DEBUG OUTPUT WILL BE SHOWN")

# Configuration
CONTRACT_PATH = os.path.join(project_root, "src", "contracts", "fi_star_schema.yaml")

# Default configurations
DEFAULT_PRINCIPAL_ROLE = PrincipalRole.CFO
DEFAULT_BUSINESS_PROCESS = BusinessProcess.PROFITABILITY_ANALYSIS
DEFAULT_TIMEFRAME = TimeFrame.CURRENT_QUARTER
DEFAULT_COMPARISON_TYPE = ComparisonType.QUARTER_OVER_QUARTER

# Map string arguments to enum values
PRINCIPAL_ROLE_MAP = {
    "cfo": PrincipalRole.CFO,
    "finance_manager": PrincipalRole.FINANCE_MANAGER
}

BUSINESS_PROCESS_MAP = {
    "profitability": BusinessProcess.PROFITABILITY_ANALYSIS,
    "revenue": BusinessProcess.REVENUE_GROWTH,
    "expense": BusinessProcess.EXPENSE_MANAGEMENT,
    "cashflow": BusinessProcess.CASH_FLOW,
    "budget": BusinessProcess.BUDGET_VS_ACTUALS,
    "all": "ALL"  # Special case for all business processes
}

TIMEFRAME_MAP = {
    "quarter": TimeFrame.CURRENT_QUARTER,
    "month": TimeFrame.CURRENT_MONTH,
    "year": TimeFrame.CURRENT_YEAR
}

COMPARISON_MAP = {
    "qoq": ComparisonType.QUARTER_OVER_QUARTER,
    "yoy": ComparisonType.YEAR_OVER_YEAR,
    "mom": ComparisonType.MONTH_OVER_MONTH,
    "target": ComparisonType.TARGET_VS_ACTUAL,
    "budget": ComparisonType.BUDGET_VS_ACTUAL
}


def parse_args():
    """Parse command line arguments for test customization."""
    parser = argparse.ArgumentParser(description='Test CFO KPI Situation Detection')
    
    parser.add_argument('--role', '-r', 
                        choices=list(PRINCIPAL_ROLE_MAP.keys()),
                        default='cfo',
                        help='Principal role to test (default: cfo)')
                        
    parser.add_argument('--process', '-p',
                        choices=list(BUSINESS_PROCESS_MAP.keys()),
                        default='profitability',
                        help='Business process to test (default: profitability)')
                        
    parser.add_argument('--timeframe', '-t',
                        choices=list(TIMEFRAME_MAP.keys()),
                        default='quarter',
                        help='Timeframe to analyze (default: quarter)')
                        
    parser.add_argument('--comparison', '-c',
                        choices=list(COMPARISON_MAP.keys()),
                        default='qoq',
                        help='Comparison method (default: qoq)')
                        
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Map string args to enum values
    principal_role = PRINCIPAL_ROLE_MAP[args.role]
    timeframe = TIMEFRAME_MAP[args.timeframe]
    comparison_type = COMPARISON_MAP[args.comparison]
    
    # Handle special case for 'all' business processes
    if args.process == 'all':
        business_processes = list(BusinessProcess)
    else:
        business_processes = [BUSINESS_PROCESS_MAP[args.process]]
    
    return principal_role, business_processes, timeframe, comparison_type, args.verbose

class OrchestratorTestHarness:
    """Test harness that mimics an Orchestrator Agent for testing workflows.
    
    This follows the Agent9 architecture pattern where UI interacts with Orchestrator,
    and Orchestrator manages workflows across multiple agents.
    """
    
    def __init__(self, verbose=False):
        """Initialize the test harness.
        
        Args:
            verbose: Whether to log verbose details
        """
        self.logger = logging.getLogger("OrchestratorTestHarness")
        self.situation_awareness_agent = None
        self.principal_contexts = {}
        self.verbose = verbose
    
    async def initialize(self):
        """Initialize all required services and agents."""
        self.logger.info("Initializing Orchestrator Test Harness")
        
        # Initialize the Situation Awareness Agent
        self.logger.info("Creating Situation Awareness Agent")
        self.situation_awareness_agent = create_situation_awareness_agent({
            "contract_path": CONTRACT_PATH
        })
        
        # Connect to the agent
        await self.situation_awareness_agent.connect()
        self.logger.info("Situation Awareness Agent connected successfully")
        
        # Create principal contexts for all supported roles
        self._initialize_principal_contexts()
        
        self.logger.info("Orchestrator Test Harness initialization complete")
    
    def _initialize_principal_contexts(self):
        """Initialize principal contexts for all supported roles."""
        # CFO is focused on financial metrics and processes
        self.principal_contexts[PrincipalRole.CFO] = PrincipalContext(
            role=PrincipalRole.CFO,
            business_processes=[
                BusinessProcess.PROFITABILITY_ANALYSIS,
                BusinessProcess.REVENUE_GROWTH,
                BusinessProcess.EXPENSE_MANAGEMENT,
                BusinessProcess.CASH_FLOW,
                BusinessProcess.BUDGET_VS_ACTUALS
            ],
            default_filters={},
            decision_style="analytical",
            communication_style="detailed",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.CURRENT_YEAR]
        )
        
        # CEO has a broader focus across departments
        self.principal_contexts[PrincipalRole.CEO] = PrincipalContext(
            role=PrincipalRole.CEO,
            business_processes=[
                BusinessProcess.PROFITABILITY_ANALYSIS,
                BusinessProcess.REVENUE_GROWTH_ANALYSIS,
            ],
            default_filters={},
            decision_style="strategic",
            communication_style="concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.CURRENT_YEAR]
        )
        
        # Finance Manager has detailed focus on specific financial processes
        self.principal_contexts[PrincipalRole.FINANCE_MANAGER] = PrincipalContext(
            role=PrincipalRole.FINANCE_MANAGER,
            business_processes=[
                BusinessProcess.EXPENSE_MANAGEMENT,
                BusinessProcess.BUDGET_VS_ACTUALS,
                BusinessProcess.CASH_FLOW_MANAGEMENT
            ],
            default_filters={},
            decision_style="operational",
            communication_style="detailed",
            preferred_timeframes=[TimeFrame.CURRENT_MONTH, TimeFrame.CURRENT_QUARTER]
        )
    
    async def detect_situations(self, principal_role: PrincipalRole,
                               business_processes: List[BusinessProcess],
                               timeframe: TimeFrame,
                               comparison_type: ComparisonType) -> SituationDetectionResponse:
        """Detect situations for the given parameters.
        
        This mimics how an Orchestrator would coordinate this workflow:
        1. Get principal context (internally or from Principal Context Agent)
        2. Create a situation detection request
        3. Delegate to the Situation Awareness Agent
        4. Return the response
        
        Args:
            principal_role: The role to analyze for (CFO, CEO, etc.)
            business_processes: List of business processes to analyze
            timeframe: Time period to consider (quarter, month, year)
            comparison_type: How to compare metrics (YoY, QoQ, etc.)
            
        Returns:
            SituationDetectionResponse with detected situations
        """
        self.logger.info(f"Starting situation detection workflow for {principal_role.value}")
        
        # Get principal context
        principal_context = self.principal_contexts.get(principal_role)
        if not principal_context:
            raise ValueError(f"No principal context available for {principal_role.value}")
        
        # Check if business processes should be filtered to those relevant for the role
        if business_processes == list(BusinessProcess):
            # If 'all' was specified, filter to just the processes for this role
            business_processes = principal_context.business_processes
            self.logger.info(f"Filtered to {len(business_processes)} business processes relevant for {principal_role.value}")
        
        # Log the processes being analyzed
        if self.verbose:
            for process in business_processes:
                self.logger.info(f"Will analyze {process.value} for {principal_role.value}")
        
        # Create the request
        request = SituationDetectionRequest(
            request_id=str(uuid.uuid4()),
            principal_context=principal_context,
            business_processes=business_processes,
            timeframe=timeframe,
            comparison_type=comparison_type,
            filters={}
        )
        
        # Delegate to the Situation Awareness Agent
        process_names = [bp.value for bp in business_processes]
        self.logger.info(f"Delegating to Situation Awareness Agent for {', '.join(process_names)}")
        response = await self.situation_awareness_agent.detect_situations(request)
        
        self.logger.info(f"Situation detection workflow complete with status: {response.status}")
        return response
    
    async def shutdown(self):
        """Clean up resources and disconnect agents."""
        if self.situation_awareness_agent:
            await self.situation_awareness_agent.disconnect()
        
        self.logger.info("Orchestrator Test Harness shutdown complete")


def get_severity_color(severity):
    """Return color code based on severity."""
    if severity == "critical":
        return Fore.RED
    elif severity == "high":
        return Fore.MAGENTA
    elif severity == "medium":
        return Fore.YELLOW
    elif severity == "low":
        return Fore.GREEN
    return Fore.WHITE


def get_change_color(change_pct):
    """Return color code based on percentage change direction."""
    if change_pct > 10:
        return Fore.BRIGHT_GREEN
    elif change_pct > 0:
        return Fore.GREEN
    elif change_pct < -10:
        return Fore.BRIGHT_RED
    elif change_pct < 0:
        return Fore.RED
    return Fore.WHITE


def format_kpi_table(situations):
    """Format KPI situations as a table."""
    table_data = []
    headers = ["KPI", "Current", "Previous", "Change", "Severity"]
    
    for situation in situations:
        kpi_value = situation.kpi_value.value
        comparison_value = situation.kpi_value.comparison_value or 0
        
        # Calculate change percentage
        if comparison_value != 0:
            change_pct = ((kpi_value - comparison_value) / comparison_value) * 100
        else:
            change_pct = 0 if kpi_value == 0 else 100
            
        # Format with appropriate precision
        if abs(kpi_value) < 10:
            current_fmt = f"{kpi_value:.2f}"
            prev_fmt = f"{comparison_value:.2f}"
        else:
            current_fmt = f"{kpi_value:.1f}"
            prev_fmt = f"{comparison_value:.1f}"
            
        table_data.append([
            situation.kpi_name,
            current_fmt,
            prev_fmt,
            f"{change_pct:+.1f}%",
            situation.severity.value.upper()
        ])
        
    return tabulate(table_data, headers=headers, tablefmt="grid")


async def test_situation_detection():
    """Test the situation detection functionality using the orchestrator pattern."""
    # Parse command line arguments
    principal_role, business_processes, timeframe, comparison_type, verbose = parse_args()
    
    logger.info(f"Starting test with Orchestrator Test Harness for {principal_role.value}")
    
    try:
        # Create and initialize the orchestrator test harness
        orchestrator = OrchestratorTestHarness(verbose=verbose)
        await orchestrator.initialize()
        
        # Request situation detection through the orchestrator
        logger.info(f"Requesting situation detection for {principal_role.value}")
        response = await orchestrator.detect_situations(
            principal_role=principal_role,
            business_processes=business_processes,
            timeframe=timeframe,
            comparison_type=comparison_type
        )
        
        # Print results with color formatting
        if response.status == "success":
            # Print header
            role_color = Fore.CYAN
            header = f"{role_color}CFO KPI SITUATION DETECTION RESULTS{Style.RESET_ALL}"
            process_info = f"{Fore.WHITE}Role: {Fore.CYAN}{principal_role.value}{Fore.WHITE}"
            timeframe_info = f"Timeframe: {Fore.CYAN}{timeframe.value}{Fore.WHITE}"
            comparison_info = f"Comparison: {Fore.CYAN}{comparison_type.value}{Style.RESET_ALL}"
            
            print("\n" + "="*80)
            print(f"{header}")
            print(f"{process_info} | {timeframe_info} | {comparison_info}")
            print("="*80)
            
            # Group situations by business process
            process_situations = {}
            
            for situation in response.situations:
                # Skip situations without business process (shouldn't happen, but just in case)
                if not hasattr(situation, 'business_process') or not situation.business_process:
                    continue
                    
                bp = situation.business_process
                if bp not in process_situations:
                    process_situations[bp] = []
                process_situations[bp].append(situation)
            
            # Display a summary table of all KPIs
            if response.situations:
                print(f"\n{Fore.CYAN}SUMMARY OF DETECTED SITUATIONS:{Style.RESET_ALL}")
                print(format_kpi_table(response.situations))
                print(f"Total situations detected: {Fore.YELLOW}{len(response.situations)}{Style.RESET_ALL}\n")
                
                # Print detailed information for each business process
                for process, situations in process_situations.items():
                    print(f"\n{Fore.BLUE}╔══ {process} ══╗{Style.RESET_ALL}")
                    print(f"Found {len(situations)} situations for this business process")
                    
                    for idx, situation in enumerate(situations, 1):
                        severity_color = get_severity_color(situation.severity.value)
                        
                        # Format KPI name and severity
                        print(f"\n{severity_color}■ {situation.kpi_name} ({situation.severity.value.upper()}){Style.RESET_ALL}")
                        print(f"  {Fore.WHITE}Description: {situation.description}{Style.RESET_ALL}")
                        print(f"  {Fore.WHITE}Business Impact: {situation.business_impact}{Style.RESET_ALL}")
                        
                        # Format KPI values with color based on direction
                        current_value = situation.kpi_value.value
                        comparison_value = situation.kpi_value.comparison_value
                        
                        print(f"  {Fore.WHITE}Current Value: {Fore.CYAN}{current_value}{Style.RESET_ALL}")
                        if comparison_value is not None:
                            change = ((current_value - comparison_value) / 
                                      comparison_value) * 100 if comparison_value != 0 else 0
                            change_color = get_change_color(change)
                            print(f"  {Fore.WHITE}Previous Value: {Fore.CYAN}{comparison_value} {change_color}({change:+.1f}%){Style.RESET_ALL}")
                        
                        # Format actions and questions
                        if situation.suggested_actions:
                            print(f"  {Fore.WHITE}Suggested Actions:{Style.RESET_ALL}")
                            for action in situation.suggested_actions:
                                print(f"    {Fore.GREEN}→ {action}{Style.RESET_ALL}")
                                
                        if situation.diagnostic_questions:
                            print(f"  {Fore.WHITE}Diagnostic Questions:{Style.RESET_ALL}")
                            for question in situation.diagnostic_questions:
                                print(f"    {Fore.YELLOW}? {question}{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.YELLOW}No situations detected.{Style.RESET_ALL}")
                
            print("\n" + "="*80)
        else:
            logger.error(f"Error detecting situations: {response.message}")
        
        # Clean up
        await orchestrator.shutdown()
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    print(f"{Fore.CYAN}CFO KPI Situation Detection Test{Style.RESET_ALL}")
    print(f"Run with -h for available options\n")
    
    try:
        asyncio.run(test_situation_detection())
        print(f"\n{Fore.GREEN}Test completed successfully!{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        logger.exception("Unhandled exception in test script")
    finally:
        print(f"\nUse the following options to test different scenarios:")
        print(f"{Fore.CYAN}--role/-r{Style.RESET_ALL}: cfo, finance_manager")
        print(f"{Fore.CYAN}--process/-p{Style.RESET_ALL}: profitability, revenue, expense, cashflow, budget, all")
        print(f"{Fore.CYAN}--timeframe/-t{Style.RESET_ALL}: quarter, month, year")
        print(f"{Fore.CYAN}--comparison/-c{Style.RESET_ALL}: qoq, yoy, mom, target, budget")
