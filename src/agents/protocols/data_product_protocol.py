"""
Protocol definition for the Data Product Agent.
Defines the interface that must be implemented by any agent providing data product capabilities.
"""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from datetime import datetime
import pandas as pd

@runtime_checkable
class DataProductProtocol(Protocol):
    """
    Protocol for Data Product Agent.
    
    This protocol defines the methods that must be implemented by any agent
    providing data product capabilities for SQL generation, execution, and data access.
    """
    
    async def execute_sql(
        self, 
        sql_query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return the results as a pandas DataFrame.
        
        Args:
            sql_query: SQL query to execute
            parameters: Optional parameters for the SQL query
            
        Returns:
            pandas DataFrame with query results
        """
        ...
    
    async def generate_sql(
        self,
        nl_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL from a natural language query.
        
        Args:
            nl_query: Natural language query
            context: Optional context for the query generation
            
        Returns:
            Dictionary containing the generated SQL and metadata
        """
        ...
    
    async def get_data_product(
        self,
        data_product_id: str
    ) -> Dict[str, Any]:
        """
        Get a data product by ID.
        
        Args:
            data_product_id: ID of the data product
            
        Returns:
            Dictionary containing the data product definition
        """
        ...
    
    async def list_data_products(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List available data products.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of data product definitions
        """
        ...
    
    async def create_view(
        self,
        view_name: str,
        sql_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a view from a SQL query.
        
        Args:
            view_name: Name of the view to create
            sql_query: SQL query defining the view
            metadata: Optional metadata for the view
            
        Returns:
            Dictionary containing the view definition
        """
        ...
