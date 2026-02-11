"""
Database Manager Factory - Creates and manages database backend instances.

This module implements the factory pattern to create the appropriate database
manager implementation based on the configuration. It serves as the entry point
for the agent to interact with different database backends (DuckDB, HANA DB,
Snowflake, Databricks, etc.).

This is a key component of the Multi-Cloud Platform (MCP) service architecture,
allowing the agent to seamlessly work with different database technologies.
"""

import logging
from typing import Dict, Any, Optional, Type, Union

from src.database.manager_interface import DatabaseManager

# Import all backend implementations
# These will be registered in the factory
# Note: Import statements will be uncommented as backends are implemented
from src.database.backends.duckdb_manager import DuckDBManager
from src.database.backends.bigquery_manager import BigQueryManager
from src.database.backends.postgres_manager import PostgresManager
# from src.database.backends.hana_manager import HANAManager
# from src.database.backends.snowflake_manager import SnowflakeManager
# from src.database.backends.databricks_manager import DatabricksManager


class DatabaseManagerFactory:
    """
    Factory class responsible for creating and managing database backend instances.
    This class implements the factory pattern to provide the appropriate database
    manager implementation based on the configuration.
    """
    
    # Registry of available database backends
    # Maps database type string to manager class
    _registry: Dict[str, Type[DatabaseManager]] = {
        'duckdb': DuckDBManager,
        'bigquery': BigQueryManager,
        'postgres': PostgresManager,
        'postgresql': PostgresManager,
        'supabase': PostgresManager,
        # 'hana': HANAManager,
        # 'snowflake': SnowflakeManager,
        # 'databricks': DatabricksManager,
    }
    
    @classmethod
    def register_backend(cls, db_type: str, manager_class: Type[DatabaseManager]) -> None:
        """
        Register a new database backend with the factory.
        
        Args:
            db_type: String identifier for the database type
            manager_class: DatabaseManager implementation class
        """
        cls._registry[db_type.lower()] = manager_class
        logging.info(f"Registered database backend: {db_type}")
    
    @classmethod
    def create_manager(cls, db_type: str, config: Dict[str, Any], logger: Optional[logging.Logger] = None) -> DatabaseManager:
        """
        Create a new database manager instance based on the specified type.
        
        Args:
            db_type: Type of database to create manager for
            config: Configuration dictionary for the database manager
            logger: Optional logger instance to use
            
        Returns:
            Instance of appropriate DatabaseManager implementation
            
        Raises:
            ValueError: If the specified database type is not supported
        """
        db_type = db_type.lower()
        if db_type not in cls._registry:
            supported = ", ".join(cls._registry.keys())
            raise ValueError(f"Unsupported database type: {db_type}. Supported types: {supported}")
        
        # Create the manager instance
        manager_class = cls._registry[db_type]
        manager = manager_class(config, logger)
        
        logging.info(f"Created database manager for type: {db_type}")
        return manager
    
    @classmethod
    def get_supported_backends(cls) -> Dict[str, Type[DatabaseManager]]:
        """
        Get a dictionary of all supported database backends.
        
        Returns:
            Dictionary mapping database type strings to manager classes
        """
        return cls._registry.copy()
