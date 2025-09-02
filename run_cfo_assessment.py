#!/usr/bin/env python
"""
CFO KPI Assessment Automation

This script automates KPI assessment for the CFO persona:
1. Evaluates all finance KPIs
2. Determines which KPIs warrant a situation for deep analysis
3. Generates a comprehensive report of findings

Usage:
    python run_cfo_assessment.py
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid
import json

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import required models and agent
from src.agents.models.situation_awareness_models import (
    PrincipalContext, 
    PrincipalRole,
    BusinessProcess,
    TimeFrame, 
    ComparisonType,
    SituationSeverity,
    SituationDetectionRequest,
    NLQueryRequest
)
from src.agents.a9_situation_awareness_agent import create_situation_awareness_agent

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONTRACT_PATH = os.path.join(project_root, "src", "contracts", "fi_star_schema.yaml")
OUTPUT_DIR = os.path.join(project_root, "output")
PRINCIPAL_ROLE = PrincipalRole.CFO
BUSINESS_PROCESSES = [
    BusinessProcess.PROFITABILITY_ANALYSIS,
    BusinessProcess.REVENUE_GROWTH,
    BusinessProcess.EXPENSE_MANAGEMENT,
    BusinessProcess.CASH_FLOW,
    BusinessProcess.BUDGET_VS_ACTUALS
]
TIMEFRAMES = [
    TimeFrame.CURRENT_QUARTER,
    TimeFrame.LAST_QUARTER
]
COMPARISON_TYPES = [
    ComparisonType.QUARTER_OVER_QUARTER,
    ComparisonType.BUDGET_VS_ACTUAL
]

class SituationReportGenerator:
    """Generates comprehensive situation reports for the CFO."""
    
    def __init__(self, agent):
        """Initialize with a situation awareness agent."""
        self.agent = agent
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "principal": PRINCIPAL_ROLE.value,
            "summaries": {},
            "situations": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [],
                "information": []
            },
            "compliant_kpis": []
        }
        
    async def get_principal_context(self) -> PrincipalContext:
        """Get the principal context for the CFO."""
        logger.info(f"Getting principal context for {PRINCIPAL_ROLE.value}")
        return await self.agent.get_principal_context(PRINCIPAL_ROLE)
    
    async def generate_situation_report(self):
        """Generate a comprehensive situation report."""
        # Get principal context
        principal_context = await self.get_principal_context()
        logger.info(f"Received principal context for {principal_context.role.value}")
        
        # Process each timeframe and comparison type
        for timeframe in TIMEFRAMES:
            for comparison_type in COMPARISON_TYPES:
                await self.detect_situations(principal_context, timeframe, comparison_type)
        
        # Generate summary
        self.generate_summary()
        
        # Save report
        self.save_report()
        
        return self.report_data
    
    async def detect_situations(self, principal_context, timeframe, comparison_type):
        """Detect situations for a specific timeframe and comparison type."""
        logger.info(f"Detecting situations for {timeframe.value} with {comparison_type.value} comparison")
        
        # Create request
        request = SituationDetectionRequest(
            request_id=str(uuid.uuid4()),
            principal_context=principal_context,
            business_processes=BUSINESS_PROCESSES,
            timeframe=timeframe,
            comparison_type=comparison_type,
            filters={}
        )
        
        # Detect situations
        response = await self.agent.detect_situations(request)
        
        # Process response
        if response.status == "success":
            logger.info(f"Detected {len(response.situations)} situations")
            
            # Store situations by severity
            for situation in response.situations:
                self.report_data["situations"][situation.severity.value].append({
                    "id": situation.situation_id,
                    "kpi_name": situation.kpi_name,
                    "description": situation.description,
                    "severity": situation.severity.value,
                    "business_impact": situation.business_impact,
                    "value": situation.kpi_value.value,
                    "comparison_value": situation.kpi_value.comparison_value,
                    "timeframe": situation.kpi_value.timeframe.value,
                    "comparison_type": situation.kpi_value.comparison_type.value if situation.kpi_value.comparison_type else None,
                    "suggested_actions": situation.suggested_actions,
                    "diagnostic_questions": situation.diagnostic_questions
                })
                
            # Store KPIs without situations
            kpi_names_with_situations = set([s["kpi_name"] for severity in self.report_data["situations"].values() for s in severity])
            all_kpis = await self.agent.get_kpi_names_for_business_processes(BUSINESS_PROCESSES)
            compliant_kpis = [kpi for kpi in all_kpis if kpi not in kpi_names_with_situations]
            
            for kpi in compliant_kpis:
                if kpi not in self.report_data["compliant_kpis"]:
                    self.report_data["compliant_kpis"].append(kpi)
        else:
            logger.error(f"Error detecting situations: {response.message}")
    
    def generate_summary(self):
        """Generate summary of the report."""
        total_situations = sum(len(situations) for situations in self.report_data["situations"].values())
        critical_high = len(self.report_data["situations"]["critical"]) + len(self.report_data["situations"]["high"])
        
        self.report_data["summaries"] = {
            "total_kpis": len(self.report_data["compliant_kpis"]) + total_situations,
            "compliant_kpis": len(self.report_data["compliant_kpis"]),
            "total_situations": total_situations,
            "critical_high_situations": critical_high,
            "situation_breakdown": {
                severity: len(situations) for severity, situations in self.report_data["situations"].items()
            },
            "overall_health": self._calculate_overall_health()
        }
        
        logger.info(f"Generated summary: {critical_high} critical/high situations out of {total_situations} total situations")
    
    def _calculate_overall_health(self):
        """Calculate overall financial health based on situations."""
        critical_count = len(self.report_data["situations"]["critical"])
        high_count = len(self.report_data["situations"]["high"])
        medium_count = len(self.report_data["situations"]["medium"])
        total_kpis = sum(len(situations) for situations in self.report_data["situations"].values()) + len(self.report_data["compliant_kpis"])
        
        if critical_count > 0:
            return "Critical Attention Required"
        elif high_count > 2:
            return "Significant Issues"
        elif high_count > 0 or medium_count > 3:
            return "Moderate Concerns"
        elif medium_count > 0:
            return "Generally Healthy with Minor Issues"
        else:
            return "Healthy"
    
    def save_report(self):
        """Save report to file."""
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cfo_situation_report_{timestamp}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Write report to file
        with open(filepath, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        logger.info(f"Report saved to {filepath}")
        
    def print_report_summary(self):
        """Print a summary of the report to console."""
        print("\n" + "="*80)
        print(f"CFO SITUATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Print overall health
        print(f"\nOVERALL FINANCIAL HEALTH: {self.report_data['summaries']['overall_health']}")
        
        # Print situation summary
        print(f"\nSITUATION SUMMARY:")
        print(f"  Total KPIs evaluated: {self.report_data['summaries']['total_kpis']}")
        print(f"  Compliant KPIs: {self.report_data['summaries']['compliant_kpis']}")
        print(f"  Total situations detected: {self.report_data['summaries']['total_situations']}")
        
        # Print situation breakdown
        print(f"\nSITUATION BREAKDOWN:")
        for severity, count in self.report_data['summaries']['situation_breakdown'].items():
            print(f"  {severity.title()}: {count}")
        
        # Print critical and high situations
        if self.report_data['situations']['critical'] or self.report_data['situations']['high']:
            print(f"\nCRITICAL AND HIGH PRIORITY SITUATIONS:")
            for situation in self.report_data['situations']['critical'] + self.report_data['situations']['high']:
                print(f"  • {situation['kpi_name']} - {situation['description']}")
                print(f"    Impact: {situation['business_impact']}")
                if situation['comparison_value']:
                    change = ((situation['value'] - situation['comparison_value']) / situation['comparison_value']) * 100
                    print(f"    Value: {situation['value']:,.2f} ({change:+.1f}% from {situation['comparison_value']:,.2f})")
                else:
                    print(f"    Value: {situation['value']:,.2f}")
        
        # Print compliant KPIs
        if self.report_data['compliant_kpis']:
            print(f"\nCOMPLIANT KPIs:")
            for kpi in self.report_data['compliant_kpis']:
                print(f"  • {kpi}")
        
        print("\n" + "="*80)
        print(f"For detailed analysis, see: {os.path.join(OUTPUT_DIR, f'cfo_situation_report_*.json')}")
        print("="*80 + "\n")


async def main():
    """Main function to run the CFO KPI assessment."""
    logger.info("Starting CFO KPI assessment")
    
    try:
        # Initialize agent
        logger.info("Initializing Situation Awareness Agent")
        agent = create_situation_awareness_agent({
            "contract_path": CONTRACT_PATH
        })
        
        # Connect to agent
        await agent.connect()
        logger.info("Successfully connected to agent")
        
        # Generate report
        report_generator = SituationReportGenerator(agent)
        await report_generator.generate_situation_report()
        report_generator.print_report_summary()
        
        # Cleanup
        await agent.close()
        logger.info("Assessment completed successfully")
        
    except Exception as e:
        logger.error(f"Error during assessment: {str(e)}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Assessment interrupted by user")
        sys.exit(1)
