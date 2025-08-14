"""
Pydantic models for the Situation Awareness Agent.
Focused on Finance KPIs from the FI Star Schema for MVP implementation.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Enums for standard types
class SituationSeverity(str, Enum):
    """Severity levels for detected situations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    INFORMATION = "information"

class BusinessProcess(str, Enum):
    """Finance business processes from FI Star Schema."""
    PROFITABILITY_ANALYSIS = "Finance: Profitability Analysis"
    REVENUE_GROWTH = "Finance: Revenue Growth Analysis"
    EXPENSE_MANAGEMENT = "Finance: Expense Management" 
    CASH_FLOW = "Finance: Cash Flow Management"
    BUDGET_VS_ACTUALS = "Finance: Budget vs. Actuals"

class PrincipalRole(str, Enum):
    """Principal roles for personalization.
    
    For MVP, we're focusing only on finance roles (CFO, Finance Manager).
    These roles should match the lowercase values in principal_registry.principal_roles 
    but use title case for display.
    """
    CFO = "CFO"  # Maps to "cfo" in registry
    FINANCE_MANAGER = "Finance Manager"  # Maps to "manager" in registry with finance focus
    
class TimeFrame(str, Enum):
    """Time frames for analysis."""
    CURRENT_MONTH = "current_month"
    CURRENT_QUARTER = "current_quarter"
    CURRENT_YEAR = "current_year"
    YEAR_TO_DATE = "year_to_date"
    QUARTER_TO_DATE = "quarter_to_date"
    MONTH_TO_DATE = "month_to_date"
    LAST_MONTH = "last_month"
    LAST_QUARTER = "last_quarter"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"

class ComparisonType(str, Enum):
    """Types of comparisons for KPIs."""
    YEAR_OVER_YEAR = "year_over_year"
    QUARTER_OVER_QUARTER = "quarter_over_quarter"
    MONTH_OVER_MONTH = "month_over_month"
    BUDGET_VS_ACTUAL = "budget_vs_actual"
    TARGET_VS_ACTUAL = "target_vs_actual"
    BENCHMARK = "benchmark"

class HITLDecision(str, Enum):
    """Human-in-the-loop decision types."""
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    ESCALATED = "escalated"

# Base models for requests and responses
class BaseRequest(BaseModel):
    """Base model for all requests."""
    request_id: str = Field(description="Unique ID for the request")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    
    model_config = ConfigDict(extra="allow")

class BaseResponse(BaseModel):
    """Base model for all responses."""
    request_id: str = Field(description="ID of the corresponding request")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    status: str = Field(description="Status of the response (success/error)")
    message: Optional[str] = Field(None, description="Additional message")
    
    model_config = ConfigDict(extra="allow")

# Principal Context Models
class PrincipalContextRequest(BaseRequest):
    """Request for principal context."""
    principal_role: PrincipalRole = Field(description="Role of the principal")
    principal_id: Optional[str] = Field(None, description="Optional identifier for specific principal")

class PrincipalContext(BaseModel):
    """Principal context for personalization."""
    role: PrincipalRole = Field(description="Role of the principal")
    business_processes: List[BusinessProcess] = Field(description="Business processes relevant to the principal")
    default_filters: Dict[str, Any] = Field(description="Default filters for the principal")
    decision_style: str = Field(description="Decision-making style of the principal") 
    communication_style: str = Field(description="Communication style of the principal")
    preferred_timeframes: List[TimeFrame] = Field(description="Preferred timeframes for analysis")

class PrincipalContextResponse(BaseResponse):
    """Response with principal context."""
    principal_context: PrincipalContext = Field(description="Principal context")

# KPI Models
class KPIDefinition(BaseModel):
    """KPI definition from the contract."""
    name: str = Field(description="Name of the KPI")
    description: str = Field(description="Description of the KPI") 
    data_product_id: str = Field(description="Data product ID")
    calculation: Optional[Any] = Field(None, description="Calculation logic or query template")
    diagnostic_questions: Optional[List[str]] = Field(None, description="Diagnostic questions for the KPI")
    thresholds: Optional[Dict[str, float]] = Field(None, description="Thresholds for the KPI")
    business_processes: Optional[List[str]] = Field(None, description="Related business processes")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    positive_trend_is_good: Optional[bool] = Field(None, description="Whether a positive trend is good for this KPI")

class KPIValue(BaseModel):
    """KPI value with context."""
    kpi_name: str = Field(description="Name of the KPI")
    value: float = Field(description="Current value of the KPI")
    comparison_value: Optional[float] = Field(None, description="Value for comparison")
    comparison_type: Optional[ComparisonType] = Field(None, description="Type of comparison")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    timeframe: TimeFrame = Field(description="Time frame of the KPI")
    dimensions: Optional[Dict[str, Any]] = Field(None, description="Dimensions of the KPI")
    
# Situation Models
class Situation(BaseModel):
    """Detected situation for a KPI."""
    situation_id: str = Field(description="Unique ID for the situation")
    kpi_name: str = Field(description="Name of the KPI")
    kpi_value: KPIValue = Field(description="Value of the KPI")
    severity: SituationSeverity = Field(description="Severity of the situation")
    description: str = Field(description="Description of the situation")
    business_impact: str = Field(description="Business impact of the situation")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested actions")
    diagnostic_questions: Optional[List[str]] = Field(None, description="Diagnostic questions")
    timestamp: datetime = Field(default_factory=datetime.now, description="Detection timestamp")

# Situation Detection Request/Response
class SituationDetectionRequest(BaseRequest):
    """Request for situation detection."""
    principal_context: PrincipalContext = Field(description="Principal context for personalization")
    business_processes: List[BusinessProcess] = Field(description="Business processes to analyze")
    timeframe: TimeFrame = Field(description="Time frame for analysis")
    comparison_type: Optional[ComparisonType] = Field(None, description="Type of comparison")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    
class SituationDetectionResponse(BaseResponse):
    """Response with detected situations."""
    situations: List[Situation] = Field(description="Detected situations")
    
# NLP Query Request/Response
class NLQueryRequest(BaseRequest):
    """Request for natural language query processing."""
    principal_context: PrincipalContext = Field(description="Principal context for personalization")
    query: str = Field(description="Natural language query")
    
class NLQueryResponse(BaseResponse):
    """Response from natural language query processing."""
    answer: str = Field(description="Answer to the query")
    kpi_values: Optional[List[KPIValue]] = Field(None, description="KPI values related to the query")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    
# HITL Models
class HITLRequest(BaseRequest):
    """Request for human-in-the-loop review."""
    situation_id: str = Field(description="ID of the situation for review")
    comment: Optional[str] = Field(None, description="Comment from the human")
    decision: HITLDecision = Field(description="Human decision")
    modified_data: Optional[Dict[str, Any]] = Field(None, description="Modified data if applicable")
    
class HITLResponse(BaseResponse):
    """Response after human-in-the-loop review."""
    updated_situation: Optional[Situation] = Field(None, description="Updated situation if applicable")
