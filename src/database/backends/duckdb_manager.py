"""
DuckDB Manager - Implementation of the database manager interface for DuckDB.

This module implements the DatabaseManager interface for the DuckDB database engine.
It handles all DuckDB-specific operations including connection management,
query execution, view creation, and data source registration.

As part of the Multi-Cloud Platform (MCP) service architecture, this implementation
provides database-specific logic while adhering to the common interface.
"""

import os
import re
import uuid
import asyncio
import traceback
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

import pandas as pd
import duckdb

from src.database.manager_interface import DatabaseManager


class DuckDBManager(DatabaseManager):
    """
    DatabaseManager implementation for DuckDB.
    Handles all DuckDB-specific operations while adhering to the common interface.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the DuckDB manager.
        
        Args:
            config: Configuration dictionary
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.duckdb_conn = None
        self.data_product_views = {}
        
    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a connection to DuckDB using the provided parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters
                              (for DuckDB, typically just includes database_path)
            
        Returns:
            True if connection established successfully, False otherwise
        """
        try:
            # If a database_path is provided, use it, otherwise use in-memory
            database_path = connection_params.get('database_path', ':memory:')
            self.logger.info(f"Connecting to DuckDB at {database_path}")

            if database_path not in (":memory:", ""):
                db_path = Path(database_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a new DuckDB connection
            self.duckdb_conn = duckdb.connect(database_path)

            # Configure DuckDB settings for proper decimal handling and other optimizations
            # Note: 'format' is not a valid DuckDB configuration parameter
            # self.duckdb_conn.execute("SET format='EUROPEAN'")

            return True
        except Exception as e:
            self.logger.error(f"Error connecting to DuckDB: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Close the connection to DuckDB.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        try:
            if self.duckdb_conn:
                self.duckdb_conn.close()
                self.duckdb_conn = None
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from DuckDB: {str(e)}")
            return False
    
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
        tx_id = transaction_id or str(uuid.uuid4())
        
        try:
            self.logger.info(f"[TXN:{tx_id}] Executing SQL: {sql[:100]}...")
            
            # Execute the query
            if parameters:
                result = self.duckdb_conn.execute(sql, parameters).fetchdf()
            else:
                result = self.duckdb_conn.execute(sql).fetchdf()
            
            self.logger.info(f"[TXN:{tx_id}] Query execution successful. Rows: {len(result)}")
            return result
        except Exception as e:
            self.logger.error(f"[TXN:{tx_id}] Error executing query: {str(e)}")
            # Return empty DataFrame on error
            return pd.DataFrame()
    
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
        tx_id = transaction_id or str(uuid.uuid4())
        
        try:
            # Check if view already exists
            if not replace_existing:
                exists = await self.check_view_exists(view_name)
                if exists:
                    self.logger.info(f"[TXN:{tx_id}] View {view_name} already exists and replace_existing is False")
                    return False
            
            # Drop any old alias/base to avoid lingering recursive definitions
            lowercase_view_name = view_name.lower()
            try:
                self.duckdb_conn.execute(f'DROP VIEW IF EXISTS {lowercase_view_name}')
            except Exception:
                pass
            try:
                self.duckdb_conn.execute(f'DROP VIEW IF EXISTS "{view_name}"')
            except Exception:
                pass

            # Create or replace only the quoted base view (no alias) to avoid ambiguity
            create_sql = f'CREATE OR REPLACE VIEW "{view_name}" AS {sql}'
            self.duckdb_conn.execute(create_sql)
            
            self.logger.info(f"[TXN:{tx_id}] Created view: {view_name}")
            return True
        except Exception as e:
            self.logger.error(f"[TXN:{tx_id}] Error creating view {view_name}: {str(e)}")
            return False
    
    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """
        Get a list of all views in the database.
        
        Args:
            transaction_id: Optional transaction identifier for logging
            
        Returns:
            List of view names
        """
        tx_id = transaction_id or str(uuid.uuid4())
        
        try:
            # Execute SHOW VIEWS command
            result = self.duckdb_conn.execute("SHOW VIEWS").fetchall()
            view_names = [row[0] for row in result]
            self.logger.info(f"[TXN:{tx_id}] Listed {len(view_names)} views")
            return view_names
        except Exception as e:
            self.logger.error(f"[TXN:{tx_id}] Error listing views: {str(e)}")
            return []
    
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
        tx_id = transaction_id or str(uuid.uuid4())
        
        try:
            source_type = source_info.get('type', 'unknown')
            
            if source_type == 'csv':
                # Register a CSV file
                path = source_info.get('path')
                schema = source_info.get('schema', 'main')
                table_name = source_info.get('table_name')
                
                if not path or not table_name:
                    self.logger.error(f"[TXN:{tx_id}] Missing required parameters for CSV registration")
                    return False
                
                # Check if path exists
                if not os.path.exists(path):
                    self.logger.error(f"[TXN:{tx_id}] CSV file not found: {path}")
                    return False
                
                # Register the CSV file
                self.duckdb_conn.execute(
                    f"CREATE SCHEMA IF NOT EXISTS {schema}"
                )
                self.duckdb_conn.execute(
                    f"CREATE OR REPLACE TABLE {schema}.{table_name} AS SELECT * FROM read_csv_auto('{path}')"
                )
                
                self.logger.info(f"[TXN:{tx_id}] Registered CSV file {path} as {schema}.{table_name}")
                return True
            else:
                self.logger.error(f"[TXN:{tx_id}] Unsupported data source type: {source_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"[TXN:{tx_id}] Error registering data source: {str(e)}")
            return False
    
    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query for security and correctness.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Normalize SQL (remove comments, extra spaces)
        normalized_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        normalized_sql = re.sub(r'/\*[\s\S]*?\*/', '', normalized_sql)
        normalized_sql = normalized_sql.strip()
        
        # Check if the statement is a SELECT statement
        if not normalized_sql.lower().startswith('select '):
            error_msg = f"Invalid SQL statement (not a SELECT): {sql}"
            self.logger.warning(error_msg)
            return False, error_msg
        
        # Check for disallowed operations (DDL, DML)
        disallowed_patterns = [
            r'\bcreate\b', r'\bdrop\b', r'\balter\b', r'\btruncate\b', 
            r'\binsert\b', r'\bupdate\b', r'\bdelete\b', r'\bmerge\b',
            r'\bgrant\b', r'\brevoke\b', r'\bbegin\b', r'\bcommit\b',
            r'\brollback\b', r'\bcall\b', r'\bexec\b'
        ]
        
        for pattern in disallowed_patterns:
            if re.search(pattern, normalized_sql.lower()):
                error_msg = f"SQL statement contains disallowed operation: {pattern}"
                self.logger.warning(error_msg)
                return False, error_msg
        
        return True, None
    
    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the database connection.
        
        Returns:
            Dictionary with database metadata
        """
        if not self.duckdb_conn:
            return {'status': 'disconnected'}
        
        try:
            # Get DuckDB version
            version_result = self.duckdb_conn.execute("SELECT VERSION()").fetchone()
            version = version_result[0] if version_result else 'unknown'
            
            # Get schema information
            schema_result = self.duckdb_conn.execute("SELECT schema_name FROM information_schema.schemata").fetchall()
            schemas = [row[0] for row in schema_result]
            
            # Get table count
            table_result = self.duckdb_conn.execute("SELECT COUNT(*) FROM information_schema.tables").fetchone()
            table_count = table_result[0] if table_result else 0
            
            # Get view count
            view_result = self.duckdb_conn.execute("SELECT COUNT(*) FROM information_schema.views").fetchone()
            view_count = view_result[0] if view_result else 0
            
            return {
                'status': 'connected',
                'database_type': 'duckdb',
                'version': version,
                'schemas': schemas,
                'table_count': table_count,
                'view_count': view_count
            }
        except Exception as e:
            self.logger.error(f"Error getting database metadata: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def check_view_exists(self, view_name: str) -> bool:
        """
        Check if a view exists in the database.
        
        Args:
            view_name: Name of the view to check
            
        Returns:
            True if the view exists, False otherwise
        """
        try:
            # Using information_schema to check for view existence
            result = self.duckdb_conn.execute(
                "SELECT COUNT(*) FROM information_schema.views WHERE table_name = ?",
                (view_name.lower(),)
            ).fetchone()
            
            return result[0] > 0
        except Exception as e:
            self.logger.error(f"Error checking view existence for {view_name}: {str(e)}")
            return False
    
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
        tx_id = transaction_id or str(uuid.uuid4())
        results = {}
        
        for view_name in view_names:
            try:
                if view_name == 'fi_sales_by_customer_type_view':
                    self.logger.info(f"[TXN:{tx_id}] Creating fallback {view_name}")
                    self.duckdb_conn.execute("""
                        CREATE OR REPLACE VIEW fi_sales_by_customer_type_view AS
                        SELECT 
                            'Type ' || CAST(ABS(RANDOM()) % 5 + 1 AS VARCHAR) AS customertypeid,
                            ABS(RANDOM() % 1000000) / 100.0 AS value,
                            DATE_SUB(CURRENT_DATE, INTERVAL (ABS(RANDOM()) % 365 * 2) DAY) AS date
                        FROM range(0, 100)
                    """)
                    results[view_name] = True
                    self.data_product_views[view_name] = 'dp_fi_20250516_001'
                    
                elif view_name == 'fi_financial_transactions_view':
                    self.logger.info(f"[TXN:{tx_id}] Creating fallback {view_name}")
                    self.duckdb_conn.execute("""
                        CREATE OR REPLACE VIEW fi_financial_transactions_view AS
                        SELECT 
                            'TX' || CAST(i AS VARCHAR) AS transaction_id,
                            DATE_SUB(CURRENT_DATE, INTERVAL (ABS(RANDOM()) % 365) DAY) AS transaction_date,
                            'Account' || CAST(ABS(RANDOM()) % 10 + 1 AS VARCHAR) AS account_id,
                            (ABS(RANDOM()) % 20000) + 5000 AS value,
                            CASE WHEN ABS(RANDOM()) % 2 = 0 THEN 'Debit' ELSE 'Credit' END AS type
                        FROM range(0, 100) t(i)
                    """)
                    results[view_name] = True
                    self.data_product_views[view_name] = 'dp_fi_20250516_001'
                    
                elif view_name == 'fi_customer_transactions_view':
                    self.logger.info(f"[TXN:{tx_id}] Creating fallback {view_name}")
                    self.duckdb_conn.execute("""
                        CREATE OR REPLACE VIEW fi_customer_transactions_view AS
                        SELECT 
                            'TX' || CAST(i AS VARCHAR) AS transaction_id,
                            'CUST' || CAST(ABS(RANDOM()) % 100 + 1 AS VARCHAR) AS customer_id,
                            DATE_SUB(CURRENT_DATE, INTERVAL (ABS(RANDOM()) % 365) DAY) AS transaction_date,
                            (ABS(RANDOM()) % 10000) + 1000 AS amount,
                            'Type ' || CAST(ABS(RANDOM()) % 5 + 1 AS VARCHAR) AS customer_type
                        FROM range(0, 100) t(i)
                    """)
                    results[view_name] = True
                    self.data_product_views[view_name] = 'dp_fi_20250516_001'
                    
                else:
                    self.logger.warning(f"[TXN:{tx_id}] No fallback template for view: {view_name}")
                    results[view_name] = False
                
            except Exception as e:
                self.logger.error(f"[TXN:{tx_id}] Error creating fallback view {view_name}: {str(e)}")
                results[view_name] = False
                
        return results
