"""
Database Manager Factory for A9 Data Product MCP Service Agent.

This module provides a factory for creating appropriate database manager
instances based on configuration. This enables the agent to support multiple
database backends in a pluggable fashion.
"""

from typing import Any, Dict

# Import the base manager interface
from .database_manager import DatabaseManager

# Import all backend implementations
from .duckdb_manager import DuckDBManager


class DatabaseManagerFactory:
    """
    Factory class for creating database manager instances.
    
    This class enables dynamic selection of the appropriate database backend
    based on configuration, allowing the MCP service to support multiple
    database types.
    """
    
    # Registry of available database backends
    _backends = {
        'duckdb': DuckDBManager,
        # Add other backends as they are implemented:
        # 'hana': HANADBManager,
        # 'snowflake': SnowflakeManager,
        # 'databricks': DatabricksManager,
    }
    
    @classmethod
    def create_manager(cls, db_type: str, config: Dict[str, Any], logger: Any = None) -> DatabaseManager:
        """
        Create and return a database manager instance for the specified type.
        
        Args:
            db_type: The type of database to connect to (e.g., 'duckdb', 'hana')
            config: Configuration dictionary for the database manager
            logger: Logger instance for outputting log messages
            
        Returns:
            An instance of the appropriate DatabaseManager subclass
            
        Raises:
            ValueError: If the specified database type is not supported
        """
        # Normalize database type
        db_type = db_type.lower() if db_type else 'duckdb'
        
        # Log the database type being requested
        if logger:
            logger.info(f"Creating database manager for type: {db_type}")
        
        # Check if the requested backend is supported
        if db_type not in cls._backends:
            error_msg = f"Unsupported database type: {db_type}. Available types: {', '.join(cls._backends.keys())}"
            if logger:
                logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Get the appropriate manager class
        manager_class = cls._backends[db_type]
        
        # Create and return an instance of the manager
        return manager_class(config=config, logger=logger)
    
    @classmethod
    def register_backend(cls, db_type: str, manager_class: type) -> None:
        """
        Register a new database backend with the factory.
        
        This method allows dynamic registration of additional database backends
        without modifying the factory code.
        
        Args:
            db_type: The type name for the database backend
            manager_class: The manager class to associate with this type
            
        Raises:
            ValueError: If the manager class does not inherit from DatabaseManager
        """
        # Ensure the manager class inherits from DatabaseManager
        if not issubclass(manager_class, DatabaseManager):
            raise ValueError(f"Manager class must inherit from DatabaseManager: {manager_class}")
        
        # Register the backend
        cls._backends[db_type.lower()] = manager_class
    
    @classmethod
    def get_supported_backends(cls) -> list:
        """
        Get a list of supported database backend types.
        
        Returns:
            List of supported database type strings
        """
        return list(cls._backends.keys())
