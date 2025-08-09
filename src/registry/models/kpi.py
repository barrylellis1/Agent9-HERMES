"""
KPI Models

Defines the data structures for KPIs in the registry system.
This replaces the enum-based approach with a flexible, data-driven model.
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ComparisonType(str, Enum):
    """Types of comparisons supported for KPIs."""
    QOQ = "qoq"  # Quarter over Quarter
    YOY = "yoy"  # Year over Year
    MOM = "mom"  # Month over Month
    TARGET = "target"  # Against Target
    BUDGET = "budget"  # Against Budget


class KPIEvaluationStatus(str, Enum):
    """Possible evaluation statuses for KPIs."""
    GREEN = "green"  # Performing well
    YELLOW = "yellow"  # Warning/needs attention
    RED = "red"  # Critical/not meeting expectations
    NEUTRAL = "neutral"  # Neutral or informational only
    UNKNOWN = "unknown"  # Not enough data to evaluate


class KPIThreshold(BaseModel):
    """
    Thresholds for determining KPI status.
    
    These thresholds define the boundaries for evaluating a KPI
    as green (good), yellow (warning), or red (critical).
    """
    
    comparison_type: ComparisonType = Field(..., description="Type of comparison")
    green_threshold: Optional[float] = Field(None, description="Threshold for green status")
    yellow_threshold: Optional[float] = Field(None, description="Threshold for yellow status")
    red_threshold: Optional[float] = Field(None, description="Threshold for red status")
    inverse_logic: bool = Field(False, description="If True, lower values are better")


class KPIDimension(BaseModel):
    """
    Dimension for analyzing a KPI.
    
    Dimensions represent different ways to slice and analyze a KPI,
    such as by region, product, customer segment, etc.
    """
    
    name: str = Field(..., description="Name of the dimension")
    field: str = Field(..., description="Field name in the data")
    values: List[str] = Field(default_factory=list, description="Possible values for this dimension")
    description: Optional[str] = Field(None, description="Description of the dimension")


class KPI(BaseModel):
    """
    Represents a KPI (Key Performance Indicator) in the registry.
    
    This model replaces the enum-based approach with a flexible,
    data-driven model that can be extended by customers.
    """
    
    id: str = Field(..., description="Unique identifier for the KPI")
    name: str = Field(..., description="Human-readable name of the KPI")
    domain: str = Field(..., description="Business domain this KPI belongs to (e.g., Finance, HR, Sales)")
    description: Optional[str] = Field(None, description="Detailed description of the KPI")
    unit: Optional[str] = Field(None, description="Unit of measurement (%, $, #, etc.)")
    data_product_id: str = Field(..., description="ID of the data product containing this KPI's data")
    business_process_ids: List[str] = Field(default_factory=list, description="Business processes this KPI belongs to")
    sql_query: str = Field(..., description="SQL query to calculate the KPI")
    thresholds: List[KPIThreshold] = Field(default_factory=list, description="Thresholds for evaluating the KPI")
    dimensions: List[KPIDimension] = Field(default_factory=list, description="Dimensions for analyzing the KPI")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    owner_role: Optional[str] = Field(None, description="Primary role responsible for this KPI")
    stakeholder_roles: List[str] = Field(default_factory=list, description="Roles with a stake in this KPI")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata for extensions")
    
    @classmethod
    def from_enum_value(cls, enum_value: str, domain: str = "Finance") -> "KPI":
        """
        Create a KPI instance from a legacy enum value.
        
        This method provides backward compatibility with the enum-based approach.
        
        Args:
            enum_value: The enum value string (e.g., "GROSS_MARGIN")
            domain: The business domain this KPI belongs to
            
        Returns:
            A KPI instance
        """
        # Create a normalized name from the enum value
        name = " ".join(word.capitalize() for word in enum_value.lower().split("_"))
        
        # Create a normalized ID from the enum value
        kpi_id = enum_value.lower()
        
        return cls(
            id=kpi_id,
            name=name,
            domain=domain,
            description=f"{name} KPI for {domain}",
            unit="%",  # Default unit
            data_product_id="finance_data",  # Default data product
            sql_query=f"SELECT * FROM kpi_{kpi_id}",  # Default query
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
            The legacy enum ID as a string (e.g., "GROSS_MARGIN")
        """
        return self.name.upper().replace(" ", "_").replace("-", "_")
    
    def evaluate(self, value: float, comparison_type: ComparisonType) -> KPIEvaluationStatus:
        """
        Evaluate the KPI based on the provided value and comparison type.
        
        Args:
            value: The value to evaluate
            comparison_type: The type of comparison to use
            
        Returns:
            The evaluation status (GREEN, YELLOW, RED, etc.)
        """
        # Find the threshold for the specified comparison type
        threshold = next((t for t in self.thresholds if t.comparison_type == comparison_type), None)
        
        if not threshold:
            return KPIEvaluationStatus.UNKNOWN
        
        # Apply threshold logic
        if threshold.inverse_logic:
            # For inverse logic, lower is better
            if threshold.green_threshold is not None and value <= threshold.green_threshold:
                return KPIEvaluationStatus.GREEN
            elif threshold.yellow_threshold is not None and value <= threshold.yellow_threshold:
                return KPIEvaluationStatus.YELLOW
            elif threshold.red_threshold is not None and value <= threshold.red_threshold:
                return KPIEvaluationStatus.RED
            else:
                return KPIEvaluationStatus.RED
        else:
            # For normal logic, higher is better
            if threshold.green_threshold is not None and value >= threshold.green_threshold:
                return KPIEvaluationStatus.GREEN
            elif threshold.yellow_threshold is not None and value >= threshold.yellow_threshold:
                return KPIEvaluationStatus.YELLOW
            elif threshold.red_threshold is not None and value >= threshold.red_threshold:
                return KPIEvaluationStatus.RED
            else:
                return KPIEvaluationStatus.RED
