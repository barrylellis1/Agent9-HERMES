"""
Database Manager Interface - Abstract base class for all database backend implementations.

This module defines the interface that all database backend implementations must adhere to,
ensuring consistent behavior across different database platforms including DuckDB, HANA DB,
Snowflake, and Databricks.

This interface is part of the Multi-Cloud Platform (MCP) service architecture,
providing a unified data access layer regardless of the underlying database technology.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import logging


class DatabaseManager(ABC):
    """
    Abstract base class defining the interface for database backend implementations.
    All database managers (DuckDB, HANA, Snowflake, etc.) must implement this interface.
    """
    
    @abstractmethod
    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a connection to the database using the provided parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters
            
        Returns:
            True if connection established successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close the connection to the database.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_query(self, sql: str, parameters: Optional[Dict[str, Any]] = None,
                          transaction_id: Optional[str] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return the results as a pandas DataFrame.
        
        Args:
            sql: SQL query to execute
            parameters: Optional parameters for parameterized queries
            transaction_id: Optional transaction identifier for logging
            
        Returns:
            DataFrame containing query results
        """
        pass
    
    @abstractmethod
    async def create_view(self, view_name: str, sql: str, 
                        replace_existing: bool = True,
                        transaction_id: Optional[str] = None) -> bool:
        """
        Create a database view with the specified name and SQL definition.
        
        Args:
            view_name: Name of the view to create
            sql: SQL definition of the view
            replace_existing: Whether to replace the view if it already exists
            transaction_id: Optional transaction identifier for logging
            
        Returns:
            True if view creation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """
        Get a list of all views in the database.
        
        Args:
            transaction_id: Optional transaction identifier for logging
            
        Returns:
            List of view names
        """
        pass
    
    @abstractmethod
    async def register_data_source(self, source_info: Dict[str, Any], 
                                 transaction_id: Optional[str] = None) -> bool:
        """
        Register a data source (file, table, etc.) with the database.
        
        Args:
            source_info: Dictionary containing information about the data source
            transaction_id: Optional transaction identifier for logging
            
        Returns:
            True if registration was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query for security and correctness.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the database connection.
        
        Returns:
            Dictionary with database metadata
        """
        pass

    @abstractmethod
    async def check_view_exists(self, view_name: str) -> bool:
        """
        Check if a view exists in the database.
        
        Args:
            view_name: Name of the view to check
            
        Returns:
            True if the view exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def create_fallback_views(self, view_names: List[str], 
                                  transaction_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Create emergency fallback views if original sources are unavailable.
        
        Args:
            view_names: List of view names to create fallbacks for
            transaction_id: Optional transaction identifier for logging
            
        Returns:
            Dictionary mapping view names to success status
        """
        pass
