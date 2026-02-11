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
        
    async def connect(self, connection_params: Dict[str, Any] = None) -> bool:
        """
        Establish a connection to DuckDB using the provided parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters
                              (for DuckDB, typically just includes database_path)
            
        Returns:
            True if connection established successfully, False otherwise
        """
        try:
            # Extract parameters
            params = connection_params or {}
            
            # Prioritize params, then config, then default
            database_path = params.get('database_path')
            if not database_path:
                # Try to get from config
                database_path = self.config.get('database_path')
                if not database_path and self.config.get('dsn'):
                    # Handle DSN style: duckdb:///path or duckdb://:memory:
                    dsn = self.config.get('dsn', '')
                    if dsn.startswith('duckdb://'):
                        database_path = dsn.replace('duckdb://', '')
                        
            # Default to memory if still nothing
            database_path = database_path or ':memory:'
            
            self.database_path = database_path
            self.logger.info(f"Connecting to DuckDB at {self.database_path}")

            if self.database_path not in (":memory:", ""):
                db_path = Path(self.database_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a new DuckDB connection
            self.duckdb_conn = duckdb.connect(self.database_path)

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
            raise  # Re-raise the exception to allow caller to handle it
    
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
                csv_options = source_info.get('csv_options', {})
                
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
                
                # Determine delimiter
                delimiter = csv_options.get('delimiter')
                if not delimiter:
                    # Auto-detect delimiter by checking first line of file
                    delimiter = ','
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            first_line = f.readline()
                            if ';' in first_line and ',' not in first_line:
                                delimiter = ';'
                            elif first_line.count(';') > first_line.count(','):
                                delimiter = ';'
                    except Exception:
                        pass
                
                # Determine decimal separator
                decimal = csv_options.get('decimal_separator', '.')
                
                # Build options string
                options_parts = [
                    f"delim='{delimiter}'",
                    "header=true",
                    "ignore_errors=true",
                    "all_varchar=true"  # Load as varchar first to avoid type casting errors with European format
                ]
                
                # If explicit decimal separator is provided, we might want to let DuckDB handle it,
                # but read_csv_auto with all_varchar=True allows us to post-process if needed.
                # However, read_csv_auto DOES support decimal_separator.
                if decimal != '.':
                     options_parts.append(f"decimal_separator='{decimal}'")
                     # If we are specifying decimal separator, we should probably try to infer types again
                     # or trust DuckDB's auto detection with the hint.
                     # Let's remove all_varchar=true if we have a specific decimal separator to allow proper type inference
                     if "all_varchar=true" in options_parts:
                         options_parts.remove("all_varchar=true")

                options_str = ", ".join(options_parts)
                
                self.duckdb_conn.execute(
                    f"CREATE OR REPLACE TABLE {schema}.{table_name} AS SELECT * FROM read_csv_auto('{path}', {options_str})"
                )
                
                self.logger.info(f"[TXN:{tx_id}] Registered CSV file {path} as {schema}.{table_name} with options: {options_str}")
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
        
        # Check if the statement is a SELECT/WITH statement
        lower_sql = normalized_sql.lower()
        if not (lower_sql.startswith('select') or lower_sql.startswith('with')):
            error_msg = f"Invalid SQL statement (not a SELECT/WITH): {sql}"
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

    async def upsert_record(self, table: str, record: Dict[str, Any], key_fields: List[str], 
                          transaction_id: Optional[str] = None) -> bool:
        """
        Insert or update a record in the specified table.
        For DuckDB, we'll use DELETE + INSERT as a simple upsert strategy.
        """
        if not self.duckdb_conn or not self.is_connected:
            return False

        try:
            # Clean table name
            table = re.sub(r'[^\w_]', '', table)
            
            # Use thread executor for blocking operations
            loop = asyncio.get_event_loop()
            
            # 1. Check if record exists based on keys
            where_clauses = []
            params = []
            for key in key_fields:
                if key in record:
                    where_clauses.append(f"{key} = ?")
                    params.append(record[key])
            
            if where_clauses:
                where_sql = " AND ".join(where_clauses)
                check_sql = f"SELECT count(*) FROM {table} WHERE {where_sql}"
                
                result = await loop.run_in_executor(
                    None, lambda: self.duckdb_conn.execute(check_sql, params).fetchone()
                )
                exists = result[0] > 0 if result else False
                
                if exists:
                    # Update
                    update_fields = [f"{k} = ?" for k in record.keys() if k not in key_fields]
                    if update_fields:
                        update_sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE {where_sql}"
                        # params for update set + params for where clause
                        update_vals = [record[k] for k in record.keys() if k not in key_fields]
                        update_params = update_vals + params
                        
                        await loop.run_in_executor(
                            None, lambda: self.duckdb_conn.execute(update_sql, update_params)
                        )
                    return True

            # Insert
            cols = ", ".join(record.keys())
            placeholders = ", ".join(["?" for _ in record])
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            insert_params = list(record.values())
            
            await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(insert_sql, insert_params)
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Upsert failed: {str(e)}")
            return False

    async def get_record(self, table: str, key_field: str, key_value: Any, 
                       transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by its key."""
        if not self.duckdb_conn or not self.is_connected:
            return None
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table} WHERE {key_field} = ? LIMIT 1"
            
            loop = asyncio.get_event_loop()
            # fetchdf returns a DataFrame
            df = await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, [key_value]).fetchdf()
            )
            
            if not df.empty:
                # Convert first row to dict
                return df.iloc[0].to_dict()
            return None
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Get record failed: {str(e)}")
            return None

    async def delete_record(self, table: str, key_field: str, key_value: Any, 
                          transaction_id: Optional[str] = None) -> bool:
        """Delete a record by its key."""
        if not self.duckdb_conn or not self.is_connected:
            return False
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"DELETE FROM {table} WHERE {key_field} = ?"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, [key_value])
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Delete record failed: {str(e)}")
            return False

    async def fetch_records(self, table: str, filters: Optional[Dict[str, Any]] = None, 
                          transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch multiple records from a table, optionally filtered."""
        if not self.duckdb_conn or not self.is_connected:
            return []
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table}"
            params = []
            
            if filters:
                conditions = []
                for k, v in filters.items():
                    conditions.append(f"{k} = ?")
                    params.append(v)
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, params).fetchdf()
            )
            
            return df.to_dict(orient='records')
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Fetch records failed: {str(e)}")
            return []

    async def upsert_record(self, table: str, record: Dict[str, Any], key_fields: List[str], 
                          transaction_id: Optional[str] = None) -> bool:
        """
        Insert or update a record in the specified table.
        For DuckDB, we'll use DELETE + INSERT as a simple upsert strategy.
        """
        if not self.duckdb_conn or not self.is_connected:
            return False

        try:
            # Clean table name
            table = re.sub(r'[^\w_]', '', table)
            
            # Use thread executor for blocking operations
            loop = asyncio.get_event_loop()
            
            # 1. Check if record exists based on keys
            where_clauses = []
            params = []
            for key in key_fields:
                if key in record:
                    where_clauses.append(f"{key} = ?")
                    params.append(record[key])
            
            if where_clauses:
                where_sql = " AND ".join(where_clauses)
                check_sql = f"SELECT count(*) FROM {table} WHERE {where_sql}"
                
                result = await loop.run_in_executor(
                    None, lambda: self.duckdb_conn.execute(check_sql, params).fetchone()
                )
                exists = result[0] > 0 if result else False
                
                if exists:
                    # Update
                    update_fields = [f"{k} = ?" for k in record.keys() if k not in key_fields]
                    if update_fields:
                        update_sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE {where_sql}"
                        # params for update set + params for where clause
                        update_vals = [record[k] for k in record.keys() if k not in key_fields]
                        update_params = update_vals + params
                        
                        await loop.run_in_executor(
                            None, lambda: self.duckdb_conn.execute(update_sql, update_params)
                        )
                    return True

            # Insert
            cols = ", ".join(record.keys())
            placeholders = ", ".join(["?" for _ in record])
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            insert_params = list(record.values())
            
            await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(insert_sql, insert_params)
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Upsert failed: {str(e)}")
            return False

    async def get_record(self, table: str, key_field: str, key_value: Any, 
                       transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by its key."""
        if not self.duckdb_conn or not self.is_connected:
            return None
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table} WHERE {key_field} = ? LIMIT 1"
            
            loop = asyncio.get_event_loop()
            # fetchdf returns a DataFrame
            df = await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, [key_value]).fetchdf()
            )
            
            if not df.empty:
                # Convert first row to dict
                # Handle pandas timestamp conversion to string if needed
                record = df.iloc[0].to_dict()
                return record
            return None
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Get record failed: {str(e)}")
            return None

    async def delete_record(self, table: str, key_field: str, key_value: Any, 
                          transaction_id: Optional[str] = None) -> bool:
        """Delete a record by its key."""
        if not self.duckdb_conn or not self.is_connected:
            return False
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"DELETE FROM {table} WHERE {key_field} = ?"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, [key_value])
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Delete record failed: {str(e)}")
            return False

    async def fetch_records(self, table: str, filters: Optional[Dict[str, Any]] = None, 
                          transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch multiple records from a table, optionally filtered."""
        if not self.duckdb_conn or not self.is_connected:
            return []
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table}"
            params = []
            
            if filters:
                conditions = []
                for k, v in filters.items():
                    conditions.append(f"{k} = ?")
                    params.append(v)
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, params).fetchdf()
            )
            
            return df.to_dict(orient='records')
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Fetch records failed: {str(e)}")
            return []

    async def upsert_record(self, table: str, record: Dict[str, Any], key_fields: List[str], 
                          transaction_id: Optional[str] = None) -> bool:
        """
        Insert or update a record in the specified table.
        For DuckDB, we'll use DELETE + INSERT as a simple upsert strategy.
        """
        if not self.duckdb_conn or not self.is_connected:
            return False

        try:
            # Clean table name
            table = re.sub(r'[^\w_]', '', table)
            
            # Use thread executor for blocking operations
            loop = asyncio.get_event_loop()
            
            # 1. Check if record exists based on keys
            where_clauses = []
            params = []
            for key in key_fields:
                if key in record:
                    where_clauses.append(f"{key} = ?")
                    params.append(record[key])
            
            if where_clauses:
                where_sql = " AND ".join(where_clauses)
                check_sql = f"SELECT count(*) FROM {table} WHERE {where_sql}"
                
                result = await loop.run_in_executor(
                    None, lambda: self.duckdb_conn.execute(check_sql, params).fetchone()
                )
                exists = result[0] > 0 if result else False
                
                if exists:
                    # Update
                    update_fields = [f"{k} = ?" for k in record.keys() if k not in key_fields]
                    if update_fields:
                        update_sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE {where_sql}"
                        # params for update set + params for where clause
                        update_vals = [record[k] for k in record.keys() if k not in key_fields]
                        update_params = update_vals + params
                        
                        await loop.run_in_executor(
                            None, lambda: self.duckdb_conn.execute(update_sql, update_params)
                        )
                    return True

            # Insert
            cols = ", ".join(record.keys())
            placeholders = ", ".join(["?" for _ in record])
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            insert_params = list(record.values())
            
            await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(insert_sql, insert_params)
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Upsert failed: {str(e)}")
            return False

    async def get_record(self, table: str, key_field: str, key_value: Any, 
                       transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by its key."""
        if not self.duckdb_conn or not self.is_connected:
            return None
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table} WHERE {key_field} = ? LIMIT 1"
            
            loop = asyncio.get_event_loop()
            # fetchdf returns a DataFrame
            df = await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, [key_value]).fetchdf()
            )
            
            if not df.empty:
                # Convert first row to dict
                return df.iloc[0].to_dict()
            return None
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Get record failed: {str(e)}")
            return None

    async def delete_record(self, table: str, key_field: str, key_value: Any, 
                          transaction_id: Optional[str] = None) -> bool:
        """Delete a record by its key."""
        if not self.duckdb_conn or not self.is_connected:
            return False
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"DELETE FROM {table} WHERE {key_field} = ?"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, [key_value])
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Delete record failed: {str(e)}")
            return False

    async def fetch_records(self, table: str, filters: Optional[Dict[str, Any]] = None, 
                          transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch multiple records from a table, optionally filtered."""
        if not self.duckdb_conn or not self.is_connected:
            return []
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table}"
            params = []
            
            if filters:
                conditions = []
                for k, v in filters.items():
                    conditions.append(f"{k} = ?")
                    params.append(v)
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: self.duckdb_conn.execute(sql, params).fetchdf()
            )
            
            return df.to_dict(orient='records')
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Fetch records failed: {str(e)}")
            return []
