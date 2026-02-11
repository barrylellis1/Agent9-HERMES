"""
DuckDB Manager Implementation for A9 Data Product MCP Service Agent.

This module implements the DatabaseManager interface for DuckDB.
"""

import asyncio
import os
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

import duckdb
import pandas as pd

import logging
from .manager_interface import DatabaseManager

class DuckDBManager(DatabaseManager):
    """
    DuckDB implementation of the DatabaseManager interface.
    
    This class provides DuckDB-specific implementation of database operations
    required by the MCP service agent.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Any = None):
        """
        Initialize the DuckDB manager with configuration.
        
        Args:
            config: Dictionary containing database configuration
            logger: Logger instance for outputting log messages
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.connection = None
        self.database_path = None
        self.is_connected = False
        
    async def connect(self, params: Dict[str, Any] = None) -> bool:
        """
        Connect to DuckDB with optional parameters.
        
        Args:
            params: Optional connection parameters including database_path
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Extract parameters
            params = params or {}
            self.database_path = params.get('database_path', ':memory:')
            data_directory = params.get('data_directory', None)
            
            # Log connection attempt with detailed parameters
            self.logger.info(f"Connecting to DuckDB at {self.database_path}")
            self.logger.info(f"Connection parameters: {params}")
            if data_directory:
                self.logger.info(f"Data directory exists: {os.path.exists(data_directory)}")
                if os.path.exists(data_directory):
                    self.logger.info(f"Data directory contents: {os.listdir(data_directory)[:10]}")
            
            # Create connection using thread executor since duckdb.connect is blocking
            self.logger.info("Attempting to create DuckDB connection...")
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None, lambda: duckdb.connect(self.database_path)
            )
            self.logger.info("DuckDB connection created successfully")
            
            # Set configuration options for DuckDB
            self.logger.info("Setting DuckDB configuration options...")
            # Note: Use SET commands rather than PRAGMA to ensure compatibility with all versions
            await loop.run_in_executor(None, lambda: self.connection.execute("SET timezone='UTC'"))
            self.logger.info("Timezone set to UTC")
            # Note: 'format' is not a valid DuckDB configuration parameter, use locale settings if needed instead
            # await loop.run_in_executor(None, lambda: self.connection.execute("SET format='EUROPEAN'"))
            
            # Mark as connected
            self.is_connected = True
            self.logger.info("Connected to DuckDB successfully")
            
            return True
        except Exception as e:
            error_msg = f"Error connecting to DuckDB: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from DuckDB and clean up resources.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.connection:
            return True
            
        try:
            # Close connection using thread executor since it's blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.connection.close())
            
            self.connection = None
            self.is_connected = False
            self.logger.info("Disconnected from DuckDB")
            
            return True
        except Exception as e:
            error_msg = f"Error disconnecting from DuckDB: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return False
    
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
        if not self.connection or not self.is_connected:
            error_msg = "Not connected to DuckDB"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}")
            raise RuntimeError(error_msg)
            
        try:
            # Log query execution
            query_preview = query[:100] + "..." if len(query) > 100 else query
            self.logger.info(f"[TXN:{transaction_id}] Executing query: {query_preview}")
            
            # Execute query using thread executor since it's blocking
            loop = asyncio.get_event_loop()
            
            if parameters:
                result = await loop.run_in_executor(
                    None, lambda: self.connection.execute(query, parameters).fetchdf()
                )
            else:
                result = await loop.run_in_executor(
                    None, lambda: self.connection.execute(query).fetchdf()
                )
                
            self.logger.info(f"[TXN:{transaction_id}] Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            raise RuntimeError(error_msg) from e
    
    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL statement for security and correctness for DuckDB.
        
        Args:
            sql: SQL statement to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not isinstance(sql, str):
            return False, "Empty or invalid SQL statement"
            
        # Basic validation - must start with SELECT
        if not re.match(r'^\s*SELECT\s+', sql, re.IGNORECASE):
            return False, "Only SELECT statements are allowed"
        
        # Check for potentially dangerous operations
        dangerous_patterns = [
            r'\bDROP\b', r'\bTRUNCATE\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', 
            r'\bALTER\b', r'\bCREATE\b', r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return False, f"Potentially dangerous operation detected: {pattern}"
        
        # Try to prepare the statement if connection exists (syntax validation)
        if self.connection and self.is_connected:
            try:
                # Use thread executor since it's blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, lambda: self.connection.prepare(sql)
                )
            except Exception as e:
                return False, f"SQL syntax error: {str(e)}"
        
        return True, None
    
    async def create_view(self, view_name: str, view_query: str, transaction_id: str = None) -> bool:
        """
        Create a view in DuckDB.
        
        Args:
            view_name: Name of the view to create
            view_query: SQL query that defines the view
            transaction_id: Optional transaction ID for logging
            
        Returns:
            True if view was created successfully, False otherwise
        """
        if not self.connection or not self.is_connected:
            self.logger.error(f"[TXN:{transaction_id}] Not connected to DuckDB")
            return False
        
        try:
            # Clean the view name and query to prevent injection
            view_name = re.sub(r'[^\w_]', '', view_name)
            
            # Format the CREATE VIEW statement
            create_view_sql = f"CREATE OR REPLACE VIEW {view_name} AS {view_query}"
            
            # Log view creation
            self.logger.info(f"[TXN:{transaction_id}] Creating view: {view_name}")
            
            # Execute query using thread executor since it's blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self.connection.execute(create_view_sql)
            )
            
            self.logger.info(f"[TXN:{transaction_id}] View created successfully: {view_name}")
            return True
        except Exception as e:
            error_msg = f"Error creating view: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            return False
    
    async def import_csv(self, file_path: str, table_name: str, options: Dict[str, Any] = None,
                        transaction_id: str = None) -> bool:
        """
        Import data from a CSV file into a DuckDB table.
        
        Args:
            file_path: Path to the CSV file
            table_name: Name of the table to create
            options: Optional import options (delimiter, encoding, etc.)
            transaction_id: Optional transaction ID for logging
            
        Returns:
            True if import was successful, False otherwise
        """
        if not self.connection or not self.is_connected:
            self.logger.error(f"[TXN:{transaction_id}] Not connected to DuckDB")
            return False
            
        if not os.path.exists(file_path):
            self.logger.error(f"[TXN:{transaction_id}] CSV file not found: {file_path}")
            return False
        
        try:
            # Extract options with defaults
            options = options or {}
            delimiter = options.get('delimiter', ',')
            header = options.get('header', True)
            auto_detect = options.get('auto_detect', True)
            
            # Clean the table name to prevent injection
            table_name = re.sub(r'[^\w_]', '', table_name)
            
            # Log import operation
            self.logger.info(f"[TXN:{transaction_id}] Importing CSV file to table {table_name}: {file_path}")
            
            # Import CSV using thread executor since it's blocking
            loop = asyncio.get_event_loop()
            
            # Use appropriate import method based on options
            import_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} AS 
                SELECT * FROM read_csv_auto(
                    '{file_path.replace("'", "''")}',
                    delim='{delimiter}',
                    header={str(header).lower()},
                    auto_detect={str(auto_detect).lower()}
                )
            """
            
            await loop.run_in_executor(
                None, lambda: self.connection.execute(import_sql)
            )
            
            # Verify table creation by counting rows
            row_count_sql = f"SELECT COUNT(*) FROM {table_name}"
            result = await loop.run_in_executor(
                None, lambda: self.connection.execute(row_count_sql).fetchone()
            )
            
            row_count = result[0] if result else 0
            self.logger.info(f"[TXN:{transaction_id}] Imported {row_count} rows into table {table_name}")
            
            return True
        except Exception as e:
            error_msg = f"Error importing CSV file: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            return False
    
    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the DuckDB connection.
        
        Returns:
            Dictionary containing database metadata (version, engine type, etc.)
        """
        metadata = {
            'type': 'duckdb',
            'path': self.database_path,
            'connected': self.is_connected
        }
        
        if self.connection and self.is_connected:
            try:
                # Get version using thread executor since it's blocking
                loop = asyncio.get_event_loop()
                version_result = await loop.run_in_executor(
                    None, lambda: self.connection.execute("SELECT version()").fetchone()
                )
                
                if version_result:
                    metadata['version'] = version_result[0]
            except Exception:
                # Ignore errors in metadata collection
                pass
        
        return metadata
    
    def transform_sql(self, sql: str, dialect: str = None) -> str:
        """
        Transform SQL to DuckDB dialect.
        
        Args:
            sql: Standard SQL query
            dialect: Source dialect of the SQL (if different from standard)
            
        Returns:
            Transformed SQL compatible with DuckDB
        """
        if not sql:
            return sql
            
        # Currently, handle only basic transformations
        transformed_sql = sql
        
        # Handle dialect-specific transformations
        if dialect and dialect.lower() in ['postgres', 'postgresql']:
            # Replace PostgreSQL-specific functions
            transformed_sql = transformed_sql.replace('NOW()', 'CURRENT_TIMESTAMP')
        
        return transformed_sql

    async def upsert_record(self, table: str, record: Dict[str, Any], key_fields: List[str], 
                          transaction_id: Optional[str] = None) -> bool:
        """
        Insert or update a record in the specified table.
        For DuckDB, we'll use INSERT OR REPLACE if available, or DELETE + INSERT.
        """
        if not self.connection or not self.is_connected:
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
                    None, lambda: self.connection.execute(check_sql, params).fetchone()
                )
                exists = result[0] > 0 if result else False
                
                if exists:
                    # Update
                    update_fields = [f"{k} = ?" for k in record.keys() if k not in key_fields]
                    if update_fields:
                        update_sql = f"UPDATE {table} SET {', '.join(update_fields)} WHERE {where_sql}"
                        update_params = [record[k] for k in record.keys() if k not in key_fields] + params
                        await loop.run_in_executor(
                            None, lambda: self.connection.execute(update_sql, update_params)
                        )
                    return True

            # Insert
            cols = ", ".join(record.keys())
            placeholders = ", ".join(["?" for _ in record])
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            insert_params = list(record.values())
            
            await loop.run_in_executor(
                None, lambda: self.connection.execute(insert_sql, insert_params)
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Upsert failed: {str(e)}")
            return False

    async def get_record(self, table: str, key_field: str, key_value: Any, 
                       transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by its key."""
        if not self.connection or not self.is_connected:
            return None
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"SELECT * FROM {table} WHERE {key_field} = ? LIMIT 1"
            
            loop = asyncio.get_event_loop()
            # fetchdf returns a DataFrame
            df = await loop.run_in_executor(
                None, lambda: self.connection.execute(sql, [key_value]).fetchdf()
            )
            
            if not df.empty:
                return df.iloc[0].to_dict()
            return None
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Get record failed: {str(e)}")
            return None

    async def delete_record(self, table: str, key_field: str, key_value: Any, 
                          transaction_id: Optional[str] = None) -> bool:
        """Delete a record by its key."""
        if not self.connection or not self.is_connected:
            return False
            
        try:
            table = re.sub(r'[^\w_]', '', table)
            sql = f"DELETE FROM {table} WHERE {key_field} = ?"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self.connection.execute(sql, [key_value])
            )
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Delete record failed: {str(e)}")
            return False

    async def fetch_records(self, table: str, filters: Optional[Dict[str, Any]] = None, 
                          transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch multiple records from a table, optionally filtered."""
        if not self.connection or not self.is_connected:
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
                None, lambda: self.connection.execute(sql, params).fetchdf()
            )
            
            return df.to_dict(orient='records')
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Fetch records failed: {str(e)}")
            return []

    async def check_view_exists(self, view_name: str) -> bool:
        """Check if a view exists."""
        try:
            # DuckDB-specific check
            sql = "SELECT count(*) FROM information_schema.tables WHERE table_name = ? AND table_type = 'VIEW'"
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self.connection.execute(sql, [view_name]).fetchone()
            )
            return result[0] > 0 if result else False
        except Exception:
            return False

    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """List all views."""
        try:
            sql = "SELECT table_name FROM information_schema.tables WHERE table_type = 'VIEW'"
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: self.connection.execute(sql).fetchdf()
            )
            return df['table_name'].tolist()
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] List views failed: {str(e)}")
            return []

    async def create_fallback_views(self, view_names: List[str], 
                                  transaction_id: Optional[str] = None) -> Dict[str, bool]:
        """Create empty fallback views."""
        results = {}
        for view_name in view_names:
            try:
                # Create a simple view selecting NULLs or 0s
                # We need to know the schema ideally, but for generic fallback we might just use SELECT 1
                sql = f"CREATE OR REPLACE VIEW {view_name} AS SELECT 1 as dummy"
                success = await self.create_view(view_name, "SELECT 1 as dummy", transaction_id)
                results[view_name] = success
            except Exception:
                results[view_name] = False
        return results

    async def register_data_source(self, source_info: Dict[str, Any], 
                                 transaction_id: Optional[str] = None) -> bool:
        """
        Register a data source. For DuckDB, this often means creating a view or table
        from a file (CSV, Parquet, JSON).
        """
        source_type = source_info.get("type", "").lower()
        path = source_info.get("path")
        name = source_info.get("name")
        
        if not path or not name:
            return False
            
        if source_type == "csv":
            return await self.import_csv(path, name, source_info.get("options"), transaction_id)
        
        # Add other types as needed
        return False
