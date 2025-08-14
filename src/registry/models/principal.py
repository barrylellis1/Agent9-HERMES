"""
Principal Profile Models

Defines the data structures for principal profiles in the registry system.
This replaces the hardcoded principal data with a flexible, data-driven model.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class TimeFrame(BaseModel):
    """
    Represents the preferred time frame for a principal.
    """
    
    default_period: str = Field("YTD", description="Default period (e.g., YTD, QTD, MTD)")
    historical_periods: int = Field(4, description="Number of historical periods to show by default")
    forward_looking_periods: int = Field(2, description="Number of forward-looking periods to show by default")


class CommunicationPreference(BaseModel):
    """
    Represents the communication preferences for a principal.
    """
    
    detail_level: str = Field("medium", description="Level of detail preferred (high, medium, low)")
    format_preference: List[str] = Field(default_factory=lambda: ["visual", "text"], 
                                         description="Preferred communication formats")
    emphasis: List[str] = Field(default_factory=lambda: ["trends", "anomalies"], 
                                description="What to emphasize in communications")


class PrincipalProfile(BaseModel):
    """
    Represents a principal profile in the registry.
    
    This model replaces hardcoded principal data with a flexible,
    data-driven model that can be extended by customers.
    """
    
    id: str = Field(..., description="Unique identifier for the principal profile")
    name: str = Field(..., description="Human-readable name of the principal profile")
    title: str = Field(..., description="Title of the principal (e.g., CFO, CEO)")
    description: Optional[str] = Field(None, description="Detailed description of the principal")
    business_processes: List[str] = Field(default_factory=list, 
                                         description="Business processes this principal is responsible for")
    kpis: List[str] = Field(default_factory=list, 
                           description="KPIs this principal monitors")
    responsibilities: List[str] = Field(default_factory=list, 
                                      description="Key responsibilities of this principal")
    default_filters: Dict[str, List[str]] = Field(default_factory=dict, 
                                                description="Default filters for data views")
    time_frame: TimeFrame = Field(default_factory=TimeFrame, 
                                description="Preferred time frame for analysis")
    communication: CommunicationPreference = Field(default_factory=CommunicationPreference, 
                                                 description="Communication preferences")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata for extensions")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return self.model_dump()


# Pre-defined principal profiles
DEFAULT_PRINCIPALS = [
    PrincipalProfile(
        id="cfo_001",
        name="CFO",
        title="Chief Financial Officer",
        description="Responsible for financial planning, risk management, and financial reporting",
        business_processes=[
            "finance_profitability_analysis",
            "finance_revenue_growth",
            "finance_expense_management",
            "finance_cash_flow",
            "finance_budget_vs_actuals"
        ],
        kpis=[
            "gross_margin",
            "net_profit_margin",
            "operating_margin",
            "revenue_growth_rate",
            "opex_ratio",
            "operating_cash_flow"
        ],
        responsibilities=[
            "Financial strategy",
            "Capital allocation",
            "Financial reporting",
            "Risk management",
            "Investor relations"
        ],
        default_filters={
            "region": ["ALL"],
            "product": ["ALL"],
            "customer_segment": ["ALL"]
        },
        time_frame=TimeFrame(
            default_period="QTD",
            historical_periods=4,
            forward_looking_periods=2
        ),
        communication=CommunicationPreference(
            detail_level="high",
            format_preference=["visual", "text", "table"],
            emphasis=["trends", "anomalies", "forecasts"]
        )
    ),
    PrincipalProfile(
        id="finance_manager",  # This already matches the enum value in principal_roles.py
        name="Finance Manager",
        title="Finance Manager",
        description="Manages financial operations and supports financial decision-making",
        business_processes=[
            "finance_profitability_analysis",
            "finance_revenue_growth",
            "finance_expense_management",
            "finance_cash_flow",
            "finance_budget_vs_actuals"
        ],
        kpis=[
            "gross_margin",
            "net_profit_margin",
            "operating_margin",
            "revenue_growth_rate",
            "opex_ratio",
            "operating_cash_flow",
            "budget_variance",
            "forecast_accuracy"
        ],
        responsibilities=[
            "Financial reporting",
            "Budget management",
            "Cost control",
            "Financial analysis"
        ],
        default_filters={
            "region": ["ALL"],
            "product": ["ALL"],
            "customer_segment": ["ALL"]
        },
        time_frame=TimeFrame(
            default_period="MTD",
            historical_periods=6,
            forward_looking_periods=3
        ),
        communication=CommunicationPreference(
            detail_level="high",
            format_preference=["table", "text", "visual"],
            emphasis=["details", "variances", "trends"]
        )
    )
]
