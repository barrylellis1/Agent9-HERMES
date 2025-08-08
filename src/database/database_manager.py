"""
Database Manager Interface for A9 Data Product MCP Service Agent.

This module defines the abstract base class that all database managers must implement.
The DatabaseManager provides a common interface for different database backends,
allowing the agent to interact with various databases in a consistent manner.
"""

import abc
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


class DatabaseManager(abc.ABC):
    """
    Abstract base class for database managers.
    
    All database backends must implement this interface to provide
    consistent database operations for the MCP service agent.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Any = None):
        """
        Initialize the database manager with configuration.
        
        Args:
            config: Dictionary containing database configuration parameters
            logger: Logger instance for outputting log messages
        """
        self.config = config
        self.logger = logger
        self.connection = None
        self.is_connected = False
    
    @abc.abstractmethod
    async def connect(self, params: Dict[str, Any] = None) -> bool:
        """
        Connect to the database with optional parameters.
        
        Args:
            params: Optional connection parameters
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the database and clean up resources.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None, 
                           transaction_id: str = None) -> pd.DataFrame:
        """
        Execute a query and return results as a DataFrame.
        
        Args:
            query: SQL query string
            parameters: Optional query parameters
            transaction_id: Optional transaction ID for logging
            
        Returns:
            DataFrame containing query results
            
        Raises:
            RuntimeError: If query execution fails
        """
        pass
    
    @abc.abstractmethod
    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL statement for security and correctness.
        
        Args:
            sql: SQL statement to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abc.abstractmethod
    async def create_view(self, view_name: str, view_query: str, transaction_id: str = None) -> bool:
        """
        Create a view in the database.
        
        Args:
            view_name: Name of the view to create
            view_query: SQL query that defines the view
            transaction_id: Optional transaction ID for logging
            
        Returns:
            True if view was created successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def import_csv(self, file_path: str, table_name: str, options: Dict[str, Any] = None,
                        transaction_id: str = None) -> bool:
        """
        Import data from a CSV file into a database table.
        
        Args:
            file_path: Path to the CSV file
            table_name: Name of the table to create
            options: Optional import options (delimiter, encoding, etc.)
            transaction_id: Optional transaction ID for logging
            
        Returns:
            True if import was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the database connection.
        
        Returns:
            Dictionary containing database metadata (version, engine type, etc.)
        """
        pass
    
    @abc.abstractmethod
    def transform_sql(self, sql: str, dialect: str = None) -> str:
        """
        Transform SQL to the appropriate dialect for this database.
        
        Args:
            sql: Standard SQL query
            dialect: Source dialect of the SQL (if different from standard)
            
        Returns:
            Transformed SQL compatible with this database
        """
        pass
