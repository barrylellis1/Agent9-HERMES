def generate_sql_for_kpi(
    self,
    kpi_definition: Dict[str, Any],
    timeframe: str,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate SQL for a KPI based on its definition, timeframe, and filters.
    
    Args:
        kpi_definition: KPI definition dictionary with calculation and other properties
        timeframe: Time frame for analysis (e.g., CURRENT_MONTH, CURRENT_QUARTER)
        filters: Additional filters to apply
        
    Returns:
        SQL query string
    """
    transaction_id = str(uuid.uuid4())
    self.logger.info(f"[TXN:{transaction_id}] Generating SQL for KPI {kpi_definition.get('name', 'unknown')}")
    
    # Start with the base query template from the KPI definition
    base_query = ""
    calc = kpi_definition.get("calculation", None)
    if isinstance(calc, dict):
        base_query = calc.get("query_template", "")
    elif isinstance(calc, str):
        # Allow plain string expressions/templates
        base_query = calc
    elif calc is None:
        self.logger.warning(f"KPI {kpi_definition.get('name', 'unknown')} has no calculation; cannot generate SQL")
        return ""
    else:
        # Unsupported type
        self.logger.warning(f"KPI {kpi_definition.get('name', 'unknown')} calculation has unsupported type {type(calc)}; cannot generate SQL")
        return ""
    
    # Add timeframe filter
    timeframe_condition = self._get_timeframe_condition(timeframe)
    
    # Add any additional filters
    filter_conditions = []
    if filters:
        for column, value in filters.items():
            filter_conditions.append(f'"{column}" = \'{value}\'')
    
    # Add KPI-specific filters defined in calculation if present
    if isinstance(calc, dict):
        calc_filters = calc.get("filters")
        if isinstance(calc_filters, list):
            for filter_condition in calc_filters:
                filter_conditions.append(filter_condition)
    
    # Combine all conditions
    where_clause = ""
    all_conditions = []
    if timeframe_condition:
        all_conditions.append(timeframe_condition)
    if filter_conditions:
        all_conditions.extend(filter_conditions)
    
    if all_conditions:
        where_clause = f"WHERE {' AND '.join(all_conditions)}"
    
    # Construct the final query
    view_name = kpi_definition.get("view_name", "FI_Star_View")  # Default to FI_Star_View if not specified
    base_lower = base_query.strip().lower()
    if base_lower.startswith("select "):
        # Full query provided; use as-is
        sql = base_query
    else:
        # Support inline WHERE in calculation strings like "SUM(col) WHERE ..."
        expr = base_query
        inline_where = None
        if " where " in base_lower:
            # Split only on first occurrence to preserve additional clauses
            idx = base_lower.find(" where ")
            expr = base_query[:idx]
            inline_where = base_query[idx + len(" where "):]  # preserve original casing/content
        # Merge WHERE clauses
        merged_conditions = []
        if inline_where:
            merged_conditions.append(f"({inline_where.strip()})")
        if where_clause.strip().startswith("WHERE "):
            merged_conditions.append(where_clause.strip()[6:])
        final_where = f" WHERE {' AND '.join(merged_conditions)}" if merged_conditions else ""
        sql = f"SELECT {expr.strip()} FROM {view_name}{final_where}"
    
    self.logger.info(f"[TXN:{transaction_id}] Generated SQL: {sql[:100]}...")
    return sql

def generate_sql_for_kpi_comparison(
    self,
    kpi_definition: Dict[str, Any],
    timeframe: str,
    comparison_type: str,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate SQL for a KPI comparison.
    
    Args:
        kpi_definition: KPI definition dictionary
        timeframe: Current time frame
        comparison_type: Type of comparison (e.g., YEAR_OVER_YEAR, QUARTER_OVER_QUARTER)
        filters: Additional filters
        
    Returns:
        SQL query string for comparison
    """
    # Determine the comparison timeframe based on the comparison type
    comparison_timeframe = timeframe
    if comparison_type == "YEAR_OVER_YEAR":
        # Use same timeframe but previous year
        comparison_timeframe = self._get_previous_year_timeframe(timeframe)
    elif comparison_type == "QUARTER_OVER_QUARTER":
        # Use previous quarter
        comparison_timeframe = self._get_previous_quarter_timeframe(timeframe)
    elif comparison_type == "MONTH_OVER_MONTH":
        # Use previous month
        comparison_timeframe = self._get_previous_month_timeframe(timeframe)
    
    # Generate SQL with the comparison timeframe
    return self.generate_sql_for_kpi(kpi_definition, comparison_timeframe, filters)

def _get_timeframe_condition(self, timeframe: str) -> str:
    """
    Get SQL condition for a timeframe.
    
    Args:
        timeframe: Time frame string (e.g., CURRENT_MONTH, CURRENT_QUARTER)
        
    Returns:
        SQL condition string
    """
    # For MVP, we'll use a simplified approach with fiscal flags
    if timeframe == "CURRENT_MONTH":
        return '"Fiscal MTD Flag" = 1'
    elif timeframe == "CURRENT_QUARTER":
        return '"Fiscal QTD Flag" = 1'
    elif timeframe == "CURRENT_YEAR":
        return '"Fiscal YTD Flag" = 1'
    elif timeframe == "YEAR_TO_DATE":
        return '"Fiscal YTD Flag" = 1'
    elif timeframe == "QUARTER_TO_DATE":
        return '"Fiscal QTD Flag" = 1'
    elif timeframe == "MONTH_TO_DATE":
        return '"Fiscal MTD Flag" = 1'
    else:
        # Default to current quarter
        return '"Fiscal QTD Flag" = 1'

def _get_previous_year_timeframe(self, current_timeframe: str) -> str:
    """Get equivalent timeframe for previous year."""
    # For MVP, simplistic implementation - just return the same timeframe
    # In production, this would calculate the actual previous year timeframe
    return current_timeframe

def _get_previous_quarter_timeframe(self, current_timeframe: str) -> str:
    """Get equivalent timeframe for previous quarter."""
    # For MVP, simplistic implementation - just return the same timeframe
    # In production, this would calculate the actual previous quarter timeframe
    return current_timeframe

def _get_previous_month_timeframe(self, current_timeframe: str) -> str:
    """Get equivalent timeframe for previous month."""
    # For MVP, simplistic implementation - just return the same timeframe
    # In production, this would calculate the actual previous month timeframe
    return current_timeframe
