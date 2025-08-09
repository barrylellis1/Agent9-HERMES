"""
Adapter module providing KPI model definitions for the registry.
These models define the structure expected by the KPI registry system.
"""

from typing import Dict, List, Optional, Any, Union


class KPIThreshold:
    """
    Defines warning and critical thresholds for KPI monitoring.
    """
    def __init__(self, warning: Optional[float] = None, critical: Optional[float] = None):
        self.warning = warning
        self.critical = critical


class KPIComparisonMethod:
    """
    Defines a comparison method for a KPI, including type and time frame logic.
    """
    def __init__(self, type: str, description: str, timeframe_logic: str):
        self.type = type
        self.description = description
        self.timeframe_logic = timeframe_logic


class KPI:
    """
    Defines a Key Performance Indicator with all necessary metadata.
    """
    def __init__(
        self,
        name: str,
        description: str,
        type: str,
        calculation: str,
        aggregation: str,
        base_column: Optional[str] = None,
        join_tables: Optional[List[str]] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        dimensions: Optional[List[str]] = None,
        thresholds: Optional[KPIThreshold] = None,
        positive_trend_is_good: bool = True,
        business_processes: Optional[List[str]] = None,
        default_comparison: Optional[str] = None,
        comparison_methods: Optional[List[KPIComparisonMethod]] = None,
        window: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
        top_n: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        data_product_id: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.type = type
        self.calculation = calculation
        self.aggregation = aggregation
        self.base_column = base_column
        self.join_tables = join_tables or []
        self.filters = filters or []
        self.dimensions = dimensions or []
        self.thresholds = thresholds or KPIThreshold()
        self.positive_trend_is_good = positive_trend_is_good
        self.business_processes = business_processes or []
        self.default_comparison = default_comparison
        self.comparison_methods = comparison_methods or []
        self.window = window
        self.partition_by = partition_by or []
        self.order_by = order_by or []
        self.top_n = top_n
        self.dependencies = dependencies or []
        self.data_product_id = data_product_id
