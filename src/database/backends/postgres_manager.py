"""
PostgreSQL Manager Implementation for Agent9.

This module implements the DatabaseManager interface for PostgreSQL (and Supabase).
It supports the "Hybrid Schema" pattern where core identity columns are first-class,
and the full object definition is stored in a JSONB column.
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import asyncpg

from src.database.manager_interface import DatabaseManager

logger = logging.getLogger(__name__)

class PostgresManager(DatabaseManager):
    """
    PostgreSQL implementation of the DatabaseManager interface.
    Uses asyncpg for high-performance async database access.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the Postgres manager.

        Args:
            config: Configuration dictionary containing:
                - host (str)
                - port (int)
                - user (str)
                - password (str)
                - database (str)
                - schema (str, optional)
                - ssl (str/bool, optional)
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.pool: Optional[asyncpg.Pool] = None
        self._is_connected = False

    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a connection pool to the database.
        
        Args:
            connection_params: Connection parameters (can override init config)
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Merge init config with connection_params
            params = {**self.config, **connection_params}
            
            # Construct DSN if provided, otherwise build from components
            dsn = params.get("dsn")
            if not dsn:
                # Fallback to manual construction
                user = params.get("user") or params.get("username")
                password = params.get("password")
                host = params.get("host", "localhost")
                port = params.get("port", 5432)
                database = params.get("database") or params.get("dbname")
                dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

            self.logger.info(f"Connecting to Postgres at {params.get('host', 'unknown')}:{params.get('port', 5432)}")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=params.get("min_pool_size", 1),
                max_size=params.get("max_pool_size", 10),
                ssl=params.get("ssl", "require") # Default to require for cloud DBs like Supabase
            )
            
            self._is_connected = True
            self.logger.info("Successfully connected to Postgres")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Postgres: {str(e)}")
            self._is_connected = False
            return False

    async def disconnect(self) -> bool:
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._is_connected = False
            self.logger.info("Disconnected from Postgres")
        return True

    async def execute_query(self, sql: str, parameters: Optional[Dict[str, Any]] = None,
                          transaction_id: Optional[str] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.
        Note: asyncpg uses $1, $2 for params, but we support named params via wrapper logic if needed.
        For now, assuming standard SQL.
        """
        if not self.pool:
            raise RuntimeError("Not connected to database")

        try:
            async with self.pool.acquire() as conn:
                # asyncpg fetch returns Record objects
                # We need to handle parameter substitution if dict is provided
                # For simplicity in this v1, we assume the SQL handles its own params or uses lists
                # If named params are strictly required, we'd need a transformer.
                
                # Simple execution for now
                if parameters:
                    # TODO: Implement named parameter to positional conversion
                    # For now, simplistic implementation assuming no params or raw SQL
                    self.logger.warning("Named parameters not fully supported in execute_query yet")
                    records = await conn.fetch(sql)
                else:
                    records = await conn.fetch(sql)
                
                if not records:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                columns = records[0].keys()
                data = [dict(r) for r in records]
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise

    async def upsert_record(self, table: str, record: Dict[str, Any], key_fields: List[str], 
                          transaction_id: Optional[str] = None) -> bool:
        """
        Upsert a record using ON CONFLICT logic.
        Assumes "Hybrid Schema": core columns match keys in record, others go into JSONB.
        However, for generic usage, we'll try to map all record keys to columns first.
        """
        if not self.pool:
            return False

        try:
            # 1. Separate columns
            # In a full hybrid schema implementation, we would map specific fields to columns
            # and the rest to a 'definition' JSONB column. 
            # For this generic implementation, we assume the table columns match the record keys.
            
            columns = list(record.keys())
            values = list(record.values())
            
            # 2. Build SQL
            # INSERT INTO table (col1, col2) VALUES ($1, $2)
            # ON CONFLICT (key_col) DO UPDATE SET col1 = EXCLUDED.col1...
            
            placeholders = [f"${i+1}" for i in range(len(columns))]
            col_str = ", ".join(columns)
            val_str = ", ".join(placeholders)
            
            # Build UPDATE clause
            update_assignments = []
            for col in columns:
                if col not in key_fields:
                    update_assignments.append(f"{col} = EXCLUDED.{col}")
            
            conflict_target = ", ".join(key_fields)
            
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({val_str})"
            if key_fields:
                sql += f" ON CONFLICT ({conflict_target}) DO"
                if update_assignments:
                    sql += f" UPDATE SET {', '.join(update_assignments)}"
                else:
                    sql += " NOTHING"
            
            # 3. Execute
            async with self.pool.acquire() as conn:
                await conn.execute(sql, *values)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Upsert failed for table {table}: {str(e)}")
            return False

    async def get_record(self, table: str, key_field: str, key_value: Any, 
                       transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a single record."""
        if not self.pool:
            return None
            
        sql = f"SELECT * FROM {table} WHERE {key_field} = $1 LIMIT 1"
        try:
            async with self.pool.acquire() as conn:
                record = await conn.fetchrow(sql, key_value)
                return dict(record) if record else None
        except Exception as e:
            self.logger.error(f"Get record failed: {str(e)}")
            return None

    async def delete_record(self, table: str, key_field: str, key_value: Any, 
                          transaction_id: Optional[str] = None) -> bool:
        """Delete a record."""
        if not self.pool:
            return False
            
        sql = f"DELETE FROM {table} WHERE {key_field} = $1"
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(sql, key_value)
                return True
        except Exception as e:
            self.logger.error(f"Delete record failed: {str(e)}")
            return False

    async def fetch_records(self, table: str, filters: Optional[Dict[str, Any]] = None, 
                          transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch multiple records with optional AND filtering."""
        if not self.pool:
            return []
            
        sql = f"SELECT * FROM {table}"
        values = []
        if filters:
            conditions = []
            for i, (k, v) in enumerate(filters.items()):
                conditions.append(f"{k} = ${i+1}")
                values.append(v)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        try:
            async with self.pool.acquire() as conn:
                records = await conn.fetch(sql, *values)
                return [dict(r) for r in records]
        except Exception as e:
            self.logger.error(f"Fetch records failed: {str(e)}")
            return []

    # --- Standard DatabaseManager Methods ---

    async def create_view(self, view_name: str, sql: str, replace_existing: bool = True,
                        transaction_id: Optional[str] = None) -> bool:
        if not self.pool:
            return False
        
        try:
            modifier = "OR REPLACE" if replace_existing else ""
            create_sql = f"CREATE {modifier} VIEW {view_name} AS {sql}"
            async with self.pool.acquire() as conn:
                await conn.execute(create_sql)
            return True
        except Exception as e:
            self.logger.error(f"Create view failed: {str(e)}")
            return False

    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        if not self.pool:
            return []
        
        sql = """
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        """
        try:
            async with self.pool.acquire() as conn:
                records = await conn.fetch(sql)
                return [r['table_name'] for r in records]
        except Exception as e:
            self.logger.error(f"List views failed: {str(e)}")
            return []

    async def register_data_source(self, source_info: Dict[str, Any], 
                                 transaction_id: Optional[str] = None) -> bool:
        # Postgres typically doesn't need explicit file registration like DuckDB
        # But could be used for FDW (Foreign Data Wrappers) in future
        self.logger.info("register_data_source not implemented/needed for standard Postgres usage")
        return True

    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        # Basic validation
        if not sql or not sql.strip():
            return False, "Empty SQL"
        
        forbidden = ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "DELETE FROM", "UPDATE"]
        upper_sql = sql.upper()
        for term in forbidden:
            if term in upper_sql:
                return False, f"Potentially destructive command '{term}' detected"
        
        return True, None

    async def get_metadata(self) -> Dict[str, Any]:
        if not self.pool:
            return {"connected": False}
        
        try:
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                return {
                    "connected": True,
                    "type": "postgres",
                    "version": version
                }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def check_view_exists(self, view_name: str) -> bool:
        views = await self.list_views()
        return view_name in views

    async def create_fallback_views(self, view_names: List[str], 
                                  transaction_id: Optional[str] = None) -> Dict[str, bool]:
        # Not typically applicable for transactional DBs like Postgres
        return {name: False for name in view_names}
