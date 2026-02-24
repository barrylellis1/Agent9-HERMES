"""
Business Process Models

Defines the data structures for business processes in the registry system.
This replaces the enum-based approach with a flexible, data-driven model.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BusinessProcess(BaseModel):
    """
    Represents a business process in the registry.
    
    This model replaces the enum-based approach with a flexible,
    data-driven model that can be extended by customers.
    """
    
    id: str = Field(..., description="Unique identifier for the business process")
    client_id: str = Field("default", description="Client/tenant scope ('default' = shared across all clients)")
    name: str = Field(..., description="Human-readable name of the business process")
    domain: str = Field(..., description="Business domain this process belongs to (e.g., Finance, HR, Sales)")
    description: Optional[str] = Field(None, description="Detailed description of the business process")
    tags: List[str] = Field(default_factory=list, description="List of tags for categorization")
    owner_role: Optional[str] = Field(None, description="Primary role responsible for this business process")
    stakeholder_roles: List[str] = Field(default_factory=list, description="Roles with a stake in this process")
    display_name: Optional[str] = Field(None, description="Display name in format 'Domain: Name' used for UI and references")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata for extensions")
    
    @classmethod
    def from_enum_value(cls, enum_value: str) -> "BusinessProcess":
        """
        Create a BusinessProcess instance from a legacy enum value.
        
        This method provides backward compatibility with the enum-based approach.
        
        Args:
            enum_value: The enum value string (e.g., "REVENUE_GROWTH")
            
        Returns:
            A BusinessProcess instance
        """
        # Parse domain and process name from enum value format
        parts = enum_value.split(": ", 1) if ": " in enum_value else ["", enum_value]
        domain = parts[0] if len(parts) > 1 else "Finance"
        process_name = parts[1] if len(parts) > 1 else enum_value
        
        # Create a normalized ID from the process name
        process_id = process_name.lower().replace(" ", "_").replace("-", "_")
        
        return cls(
            id=f"{domain.lower()}_{process_id}",
            name=process_name,
            domain=domain,
            description=f"{domain} business process: {process_name}",
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return self.model_dump()
    
    @property
    def legacy_id(self) -> str:
        """
        Get the legacy enum ID for backward compatibility.
        
        This property allows seamless migration from enum-based code.
        
        Returns:
            The legacy enum ID as a string (e.g., "REVENUE_GROWTH")
        """
        return self.name.upper().replace(" ", "_").replace("-", "_")


# Pre-defined business processes for Finance domain
FINANCE_BUSINESS_PROCESSES = [
    BusinessProcess(
        id="finance_profitability_analysis",
        name="Profitability Analysis",
        domain="Finance",
        description="Analysis of profit margins, cost structures, and profit drivers",
        owner_role="CFO",
        stakeholder_roles=["CEO", "Finance Manager"],
        tags=["finance", "profitability", "margin", "analysis"],
    ),
    BusinessProcess(
        id="finance_revenue_growth_analysis",
        name="Revenue Growth Analysis",
        domain="Finance",
        description="Analysis of revenue growth trends, patterns, and drivers across products and regions",
        owner_role="CFO",
        stakeholder_roles=["CEO", "Sales Director", "Finance Manager"],
        tags=["finance", "revenue", "growth", "analysis"],
    ),
    BusinessProcess(
        id="finance_expense_management",
        name="Expense Management",
        domain="Finance",
        description="Tracking and controlling operational and capital expenses across the organization",
        owner_role="CFO",
        stakeholder_roles=["Finance Manager", "Department Heads"],
        tags=["finance", "expense", "cost", "management"],
    ),
    BusinessProcess(
        id="finance_cash_flow_management",
        name="Cash Flow Management",
        domain="Finance",
        description="Monitoring and optimization of cash inflows and outflows to ensure liquidity",
        owner_role="CFO",
        stakeholder_roles=["Finance Manager", "Treasury Manager"],
        tags=["finance", "cash flow", "liquidity", "working capital"],
    ),
    BusinessProcess(
        id="finance_budget_vs_actuals",
        name="Budget vs. Actuals",
        domain="Finance",
        description="Comparison of budgeted figures with actual financial results to identify variances",
        owner_role="CFO",
        stakeholder_roles=["Finance Manager", "Department Heads"],
        tags=["finance", "budget", "variance", "planning"],
    ),
]

# Legacy enum value to BusinessProcess mapping for backward compatibility
LEGACY_MAP = {
    "PROFITABILITY_ANALYSIS": FINANCE_BUSINESS_PROCESSES[0],
    "REVENUE_GROWTH_ANALYSIS": FINANCE_BUSINESS_PROCESSES[1],
    "EXPENSE_MANAGEMENT": FINANCE_BUSINESS_PROCESSES[2],
    "CASH_FLOW_MANAGEMENT": FINANCE_BUSINESS_PROCESSES[3],
    "BUDGET_VS_ACTUALS": FINANCE_BUSINESS_PROCESSES[4],
}
