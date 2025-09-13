"""
A9_Data_Product_Agent - Centralized data access for data products.

This agent provides a standardized interface for data access operations,
acting as the single authoritative layer for all dynamic SQL generation
using registry-driven SELECT, JOIN, GROUP BY, and aggregation SQL.

It is designed to provide business-ready, summarized, filtered, and pre-joined
data products to other agents and services within the system.

Protocol compliance:
- Explicitly implements DataProductProtocol
- All request/response models inherit from A9AgentBaseModel
- Factory method pattern for orchestrator-driven lifecycle
- Standardized error handling and logging
- Protocol-compliant request/response models
"""

import asyncio
import datetime
import logging
import os
import re
import time
import traceback
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple, ClassVar, Set

from src.agents.agent_config_models import A9_Data_Product_Agent_Config
from src.agents.protocols.data_product_protocol import DataProductProtocol
from src.agents.shared.a9_agent_base_model import A9AgentBaseModel
from src.database.db_manager import DatabaseManager
from src.registry.factory import RegistryFactory
from src.registry.providers.data_product_provider import DataProductProvider
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.view_provider import ViewProvider

logger = logging.getLogger(__name__)

class A9_Data_Product_Agent:
    """
    Data Product Agent - Implements DataProductProtocol
    
    This agent is responsible for:
    - Managing data products and their metadata
    - Generating SQL for data access
    - Creating and managing views
    - Executing SQL queries
    - Providing data to other agents
    """
    
    @classmethod
    async def create(cls, config: Dict[str, Any]) -> 'A9_Data_Product_Agent':
        """
        Factory method to create and initialize a Data Product Agent.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initialized Data Product Agent
        """
        # Create instance
        instance = cls(config)
        
        # Initialize async resources
        await instance._async_init()
        
        return instance
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Data Product Agent.
        
        Args:
            config: Configuration dictionary
        """
        # Parse config
        self.config = A9_Data_Product_Agent_Config(**config)
        
        # Set up logging
        self.logger = logger
        
        # Initialize database connection
        self.db_type = self.config.db_type or "duckdb"
        self.db_path = os.path.join(self.config.data_directory or "data", self.config.db_name or "agent9-hermes.duckdb")
        self.logger.info(f"Initializing database connection with type: {self.db_type}, path: {self.db_path}")
        
        # Initialize database manager
        self.db_manager = DatabaseManager(db_type=self.db_type, db_path=self.db_path)
        self.logger.info("Database connection initialized successfully")
        
        # Initialize registry providers
        self.registry_factory = RegistryFactory()
        self.data_product_provider = self.registry_factory.get_provider("data_product") or DataProductProvider()
        self.view_provider = self.registry_factory.get_provider("view") or ViewProvider()
        self.kpi_provider = self.registry_factory.get_provider("kpi") or KPIProvider()
        self.logger.info("Registry providers initialized successfully")
        
        # Load registry
        self._load_registry()
    
    async def _async_init(self):
        """Initialize async resources."""
        # Nothing to initialize asynchronously for now
        pass
    
    def _load_registry(self):
        """Load data product registry."""
        transaction_id = str(uuid.uuid4())
        registry_path = self.config.registry_path
        
        if registry_path:
            self.logger.info(f"[TXN:{transaction_id}] Loading data product registry from: {registry_path}")
            self.data_product_provider.load_from_yaml(registry_path)
        else:
            self.logger.warning(f"[TXN:{transaction_id}] No registry path specified, using default data products")
            self._load_default_data_products()
        
        # Log registry status
        registry = self.data_product_provider.get_registry()
        has_data_products = registry and "data_products" in registry
        self.logger.info(f"[TXN:{transaction_id}] Registry status: registry={type(registry)}, has_data_products={has_data_products}")
        
        # Log number of data products
        data_products = self.data_product_provider.get_all()
        self.logger.info(f"Data Product Agent initialized with {len(data_products)} data products")
    
    def _load_default_data_products(self):
        """Load default data products when no registry is available."""
        transaction_id = str(uuid.uuid4())
        self.logger.warning(f"[TXN:{transaction_id}] Loading default data products")
        
        # Create a default data product
        default_dp = {
            "id": "default",
            "name": "Default Data Product",
            "description": "Default data product for testing",
            "tables": [
                {
                    "name": "sales",
                    "description": "Sales data",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "description": "Sale ID"},
                        {"name": "date", "type": "DATE", "description": "Sale date"},
                        {"name": "amount", "type": "DECIMAL", "description": "Sale amount"},
                        {"name": "customer_id", "type": "INTEGER", "description": "Customer ID"},
                        {"name": "product_id", "type": "INTEGER", "description": "Product ID"}
                    ]
                }
            ]
        }
        
        # Register the default data product
        self.data_product_provider.register(default_dp)
        self.logger.info(f"[TXN:{transaction_id}] Loaded default data product")
    
    def _get_data_product_by_id(self, data_product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a data product by ID.
        
        Args:
            data_product_id: ID of the data product to retrieve
            
        Returns:
            Data product dictionary if found, None otherwise
        """
        if not self.data_product_provider:
            return None
        
        return self.data_product_provider.get(data_product_id)
    
    async def get_data_product(self, data_product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a data product by ID.
        
        Args:
            data_product_id: ID of the data product to retrieve
            
        Returns:
            DataProduct object if found, None otherwise
        """
        # Simple wrapper to make the synchronous method async-compatible
        return self._get_data_product_by_id(data_product_id)
    
    def _generate_sql_for_kpi(self, kpi_definition: Any, timeframe: Any = None, filters: Dict[str, Any] = None) -> str:
        """Generate SQL query for a KPI definition.

        Args:
            kpi_definition: KPI definition object
            timeframe: Optional timeframe to filter by
            filters: Optional additional filters

        Returns:
            SQL query string
        """
        # Start with the base query template from the KPI definition
        base_query = ""
        calc = getattr(kpi_definition, "calculation", None)
        if isinstance(calc, dict):
            base_query = calc.get("query_template", "")
        elif isinstance(calc, str):
            # Allow plain string expressions/templates
            base_query = calc
        elif calc is None:
            self.logger.warning(f"KPI {kpi_definition.name} has no calculation; cannot generate SQL")
            return ""
        else:
            # Unsupported type
            self.logger.warning(f"KPI {kpi_definition.name} calculation has unsupported type {type(calc)}; cannot generate SQL")
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
        
        # Use provided view name or default
        view_name = self._get_default_view_name()
        
        # Construct the final query
        base_lower = base_query.strip().lower()
        if base_lower.startswith("select "):
            # Full query provided; use as-is
            sql = base_query
        else:
            # Support inline WHERE in calculation strings like "SUM(col) WHERE ..."
            expr = base_query
            inline_where = None
            if " where " in base_lower:
                parts = base_query.split(" where ", 1)
                expr = parts[0]
                inline_where = parts[1]
            
            # Construct the query
            sql = f"SELECT {expr} FROM {view_name}"
            
            # Add WHERE clause
            if inline_where and where_clause:
                # Both inline and external conditions
                sql += f" WHERE {inline_where} AND {' AND '.join(all_conditions)}"
            elif inline_where:
                # Only inline conditions
                sql += f" WHERE {inline_where}"
            elif where_clause:
                # Only external conditions
                sql += f" {where_clause}"
        
        return sql
    
    def _get_timeframe_condition(self, timeframe: Any) -> Optional[str]:
        """
        Generate SQL condition for timeframe.
        
        Args:
            timeframe: Timeframe object or string
            
        Returns:
            SQL condition string or None
        """
        if not timeframe:
            return None
        
        # Handle string timeframes like "last_30_days", "this_quarter", etc.
        if isinstance(timeframe, str):
            timeframe_lower = timeframe.lower()
            date_col = "date"  # Default date column
            
            if timeframe_lower == "this_quarter":
                return f"{date_col} >= date_trunc('quarter', CURRENT_DATE) AND {date_col} < date_trunc('quarter', CURRENT_DATE) + INTERVAL '3 months'"
            elif timeframe_lower == "last_quarter":
                return f"{date_col} >= date_trunc('quarter', CURRENT_DATE) - INTERVAL '3 months' AND {date_col} < date_trunc('quarter', CURRENT_DATE)"
            elif timeframe_lower == "this_year":
                return f"{date_col} >= date_trunc('year', CURRENT_DATE) AND {date_col} < date_trunc('year', CURRENT_DATE) + INTERVAL '1 year'"
            elif timeframe_lower == "last_year":
                return f"{date_col} >= date_trunc('year', CURRENT_DATE) - INTERVAL '1 year' AND {date_col} < date_trunc('year', CURRENT_DATE)"
            elif timeframe_lower == "this_month":
                return f"{date_col} >= date_trunc('month', CURRENT_DATE) AND {date_col} < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
            elif timeframe_lower == "last_month":
                return f"{date_col} >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 month' AND {date_col} < date_trunc('month', CURRENT_DATE)"
            elif timeframe_lower == "last_7_days":
                return f"{date_col} >= CURRENT_DATE - INTERVAL '7 days' AND {date_col} <= CURRENT_DATE"
            elif timeframe_lower == "last_30_days":
                return f"{date_col} >= CURRENT_DATE - INTERVAL '30 days' AND {date_col} <= CURRENT_DATE"
            elif timeframe_lower == "last_90_days":
                return f"{date_col} >= CURRENT_DATE - INTERVAL '90 days' AND {date_col} <= CURRENT_DATE"
            elif timeframe_lower == "ytd":
                return f"{date_col} >= date_trunc('year', CURRENT_DATE) AND {date_col} <= CURRENT_DATE"
        
        # Handle object timeframes with start_date and end_date
        start_date = getattr(timeframe, "start_date", None)
        end_date = getattr(timeframe, "end_date", None)
        date_col = getattr(timeframe, "date_column", "date")
        
        conditions = []
        if start_date:
            conditions.append(f"{date_col} >= '{start_date}'")
        if end_date:
            conditions.append(f"{date_col} <= '{end_date}'")
        
        if conditions:
            return " AND ".join(conditions)
        
        return None
    
    def _get_default_view_name(self) -> str:
        """
        Get the default view name for SQL generation.
        
        Returns:
            Default view name
        """
        # For MVP, use a simple default view
        return "sales"
    
    def _generate_sql_from_nl_query(self, nl_query: str, filters: Dict[str, Any] = None, data_product: Dict[str, Any] = None) -> str:
        """
        Generate SQL from a natural language query.
        
        Args:
            nl_query: Natural language query
            filters: Optional filters to apply
            data_product: Optional data product context
            
        Returns:
            Generated SQL query
        """
        # For MVP, use a simplified approach
        # In production, this would call the LLM Service Agent
        
        # Extract key terms from the query
        query_lower = nl_query.lower()
        
        # Default SQL components
        select_clause = "SELECT *"
        from_clause = "FROM sales"
        where_clause = ""
        group_by_clause = ""
        order_by_clause = ""
        limit_clause = "LIMIT 100"
        
        # Check for aggregation terms
        if "total" in query_lower or "sum" in query_lower:
            if "revenue" in query_lower or "sales" in query_lower:
                select_clause = "SELECT SUM(amount) as total_revenue"
            elif "orders" in query_lower or "transactions" in query_lower:
                select_clause = "SELECT COUNT(*) as total_orders"
        
        # Check for time periods
        if "this quarter" in query_lower:
            where_clause = "WHERE date >= date_trunc('quarter', CURRENT_DATE) AND date < date_trunc('quarter', CURRENT_DATE) + INTERVAL '3 months'"
        elif "last quarter" in query_lower:
            where_clause = "WHERE date >= date_trunc('quarter', CURRENT_DATE) - INTERVAL '3 months' AND date < date_trunc('quarter', CURRENT_DATE)"
        elif "this year" in query_lower:
            where_clause = "WHERE date >= date_trunc('year', CURRENT_DATE) AND date < date_trunc('year', CURRENT_DATE) + INTERVAL '1 year'"
        elif "last year" in query_lower:
            where_clause = "WHERE date >= date_trunc('year', CURRENT_DATE) - INTERVAL '1 year' AND date < date_trunc('year', CURRENT_DATE)"
        elif "this month" in query_lower:
            where_clause = "WHERE date >= date_trunc('month', CURRENT_DATE) AND date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
        elif "last month" in query_lower:
            where_clause = "WHERE date >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 month' AND date < date_trunc('month', CURRENT_DATE)"
        
        # Check for grouping
        if "by product" in query_lower:
            group_by_clause = "GROUP BY product_id"
            order_by_clause = "ORDER BY total_revenue DESC"
        elif "by customer" in query_lower:
            group_by_clause = "GROUP BY customer_id"
            order_by_clause = "ORDER BY total_revenue DESC"
        elif "by date" in query_lower:
            group_by_clause = "GROUP BY date"
            order_by_clause = "ORDER BY date"
        
        # Combine all clauses
        sql = f"{select_clause} {from_clause}"
        if where_clause:
            sql += f" {where_clause}"
        if group_by_clause:
            sql += f" {group_by_clause}"
        if order_by_clause:
            sql += f" {order_by_clause}"
        if limit_clause:
            sql += f" {limit_clause}"
        
        return sql
    
    async def list_data_products(self) -> List[Dict[str, Any]]:
        """
        List all available data products.
        
        Returns:
            List of data product dictionaries
        """
        if not self.data_product_provider:
            return []
        
        return self.data_product_provider.get_all()
    
    async def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a SQL query.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            Dictionary with query results and metadata
        """
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Executing SQL: {sql}")
        
        try:
            # Execute the query
            start_time = time.time()
            result = self.db_manager.execute_query(sql, params or {})
            end_time = time.time()
            
            # Calculate execution time
            execution_time = end_time - start_time
            
            # Format results
            columns = result.get("columns", [])
            rows = result.get("rows", [])
            
            self.logger.info(f"[TXN:{transaction_id}] SQL executed successfully in {execution_time:.2f}s, returned {len(rows)} rows")
            
            return {
                "transaction_id": transaction_id,
                "sql": sql,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time": execution_time,
                "success": True,
                "message": f"Query executed successfully in {execution_time:.2f}s, returned {len(rows)} rows"
            }
            
        except Exception as e:
            error_msg = f"Error executing SQL: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            
            return {
                "transaction_id": transaction_id,
                "sql": sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time": 0,
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    async def create_view(self, view_name: str, sql: str) -> Dict[str, Any]:
        """
        Create a database view.
        
        Args:
            view_name: Name of the view to create
            sql: SQL query defining the view
            
        Returns:
            Dictionary with view creation status
        """
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Creating view {view_name} with SQL: {sql}")
        
        try:
            # Create the view
            create_view_sql = f"CREATE OR REPLACE VIEW {view_name} AS {sql}"
            self.db_manager.execute_query(create_view_sql)
            
            # Register the view in the view provider
            if self.view_provider:
                view_def = {
                    "name": view_name,
                    "sql": sql,
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat()
                }
                self.view_provider.register(view_def)
            
            self.logger.info(f"[TXN:{transaction_id}] View {view_name} created successfully")
            
            return {
                "transaction_id": transaction_id,
                "view_name": view_name,
                "sql": sql,
                "success": True,
                "message": f"View {view_name} created successfully"
            }
            
        except Exception as e:
            error_msg = f"Error creating view {view_name}: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            
            return {
                "transaction_id": transaction_id,
                "view_name": view_name,
                "sql": sql,
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
    
    async def generate_sql(self, nl_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate SQL from a natural language query.

        Args:
            nl_query: Natural language query
            context: Optional context for the query generation
            
        Returns:
            Dictionary containing the generated SQL and metadata
        """
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Generating SQL for query: {nl_query}")
        
        try:
            # Extract context variables
            data_product_id = context.get('data_product_id') if context else None
            filters = context.get('filters', {}) if context else {}
            kpi_values = context.get('kpi_values') if context else None
            
            # Get data product if specified
            data_product = None
            if data_product_id:
                data_product = self._get_data_product_by_id(data_product_id)
            
            # If KPI values are provided, use the dedicated method
            if kpi_values:
                self.logger.info(f"[TXN:{transaction_id}] Using KPI values for SQL generation")
                # Use the first KPI value for simplicity in MVP
                if len(kpi_values) > 0:
                    kpi_value = kpi_values[0]
                    kpi_def = None
                    
                    # Try to get KPI definition from provider
                    if hasattr(kpi_value, 'kpi_name') and self.kpi_provider:
                        kpi_def = self.kpi_provider.get(kpi_value.kpi_name)
                    
                    if kpi_def:
                        # Get timeframe and filters from KPI value
                        timeframe = getattr(kpi_value, 'timeframe', None)
                        filters = getattr(kpi_value, 'dimensions', {})
                        
                        # Generate SQL using KPI definition
                        sql = self._generate_sql_for_kpi(kpi_def, timeframe, filters)
                        return {
                            'sql': sql,
                            'kpi_name': kpi_value.kpi_name,
                            'transaction_id': transaction_id,
                            'success': True,
                            'message': f"SQL generated successfully for KPI: {kpi_value.kpi_name}"
                        }
            
            # If no KPI or data product found, generate SQL based on natural language query
            # For MVP, use a simplified approach
            sql = self._generate_sql_from_nl_query(nl_query, filters, data_product)
            
            return {
                'sql': sql,
                'nl_query': nl_query,
                'data_product_id': data_product_id,
                'transaction_id': transaction_id,
                'success': True,
                'message': "SQL generated successfully"
            }
            
        except Exception as e:
            error_msg = f"Error generating SQL: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            return {
                'sql': "",
                'nl_query': nl_query,
                'transaction_id': transaction_id,
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
