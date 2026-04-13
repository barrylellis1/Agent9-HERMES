"""
Snowflake Manager - Implementation of the database manager interface for Snowflake.

This module implements the DatabaseManager interface for Snowflake, providing
query execution and metadata helpers via the snowflake-connector-python SDK.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.database.manager_interface import DatabaseManager

try:  # pragma: no cover
    import snowflake.connector
    from snowflake.connector import ProgrammingError
except Exception:  # pragma: no cover
    snowflake = None  # type: ignore
    ProgrammingError = Exception  # type: ignore


class SnowflakeManager(DatabaseManager):
    """
    DatabaseManager implementation for Snowflake.
    Provides curated view discovery and SQL execution capabilities.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        self.conn: Optional["snowflake.connector.SnowflakeConnection"] = None  # type: ignore
        self.account: Optional[str] = self.config.get("account")
        self.warehouse: Optional[str] = self.config.get("warehouse")
        self.database: Optional[str] = self.config.get("database")
        self.schema: Optional[str] = self.config.get("schema")
        self.role: Optional[str] = self.config.get("role")

    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a Snowflake connection using the provided parameters.

        Args:
            connection_params: Dict with 'user', 'password' (or 'private_key')

        Returns:
            True if connection successful, False otherwise
        """
        if snowflake is None:
            self.logger.error("snowflake-connector-python package is not installed")
            return False

        try:
            params = dict(self.config)
            params.update(connection_params or {})

            conn_kwargs = {
                "account": params.get("account") or self.account,
                "user": params.get("user"),
                "warehouse": params.get("warehouse") or self.warehouse,
                "database": params.get("database") or self.database,
                "schema": params.get("schema") or self.schema,
            }

            # Add password or private key
            if params.get("password"):
                conn_kwargs["password"] = params["password"]
            elif params.get("private_key"):
                conn_kwargs["private_key"] = params["private_key"]
            else:
                self.logger.error("Either 'password' or 'private_key' must be provided")
                return False

            # Add optional role
            if params.get("role") or self.role:
                conn_kwargs["role"] = params.get("role") or self.role

            # Remove None values
            conn_kwargs = {k: v for k, v in conn_kwargs.items() if v is not None}

            # Create connection in thread pool
            self.conn = await asyncio.to_thread(snowflake.connector.connect, **conn_kwargs)

            self.logger.info(
                "Connected to Snowflake account '%s' (database=%s, schema=%s)",
                self.account,
                self.database,
                self.schema,
            )
            return True
        except Exception as exc:
            self.logger.error("Failed to connect to Snowflake: %s", exc)
            self.conn = None
            return False

    async def disconnect(self) -> bool:
        """
        Close the Snowflake connection.
        """
        try:
            if self.conn:
                await asyncio.to_thread(self.conn.close)
                self.conn = None
            return True
        except Exception as exc:
            self.logger.warning("Error closing Snowflake connection: %s", exc)
            return False

    async def execute_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.
        """
        if not self.conn:
            raise RuntimeError("Snowflake connection not established. Call connect() first.")

        try:
            self.logger.debug(f"[{transaction_id}] Executing query: {sql[:200]}...")

            # Execute query in thread pool
            cursor = await asyncio.to_thread(self.conn.cursor)
            await asyncio.to_thread(cursor.execute, sql, parameters)

            # Fetch results and convert to DataFrame
            df = await asyncio.to_thread(cursor.fetch_pandas_all)
            await asyncio.to_thread(cursor.close)

            self.logger.debug(f"[{transaction_id}] Query returned {len(df)} rows")
            return df
        except Exception as exc:
            self.logger.error(f"[{transaction_id}] Query execution failed: {exc}")
            raise

    async def create_view(
        self,
        view_name: str,
        sql: str,
        replace_existing: bool = True,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Create a view in Snowflake.

        Note: For Phase 10C, views are customer-managed in curated layer.
        This method provides testing support.
        """
        try:
            if replace_existing:
                drop_sql = f'DROP VIEW IF EXISTS "{view_name}"'
                await self.execute_query(drop_sql, transaction_id=transaction_id)

            create_sql = f'CREATE OR REPLACE VIEW "{view_name}" AS\n{sql}'
            await self.execute_query(create_sql, transaction_id=transaction_id)

            self.logger.info(f"[{transaction_id}] Created view {view_name}")
            return True
        except Exception as exc:
            self.logger.error(f"[{transaction_id}] Failed to create view: {exc}")
            return False

    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """
        List all views in the current schema via INFORMATION_SCHEMA.
        """
        try:
            sql = f"""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_SCHEMA = '{self.schema}'
            ORDER BY TABLE_NAME
            """
            df = await self.execute_query(sql, transaction_id=transaction_id)
            return df["TABLE_NAME"].tolist() if not df.empty else []
        except Exception as exc:
            self.logger.warning(f"[{transaction_id}] Failed to list views: {exc}")
            return []

    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL by checking for DDL/DML statements (not allowed).
        Only SELECT/WITH queries permitted.
        """
        normalized = sql.strip().upper()

        # Allowed: SELECT, WITH (CTE)
        if normalized.startswith("SELECT") or normalized.startswith("WITH"):
            return True, None

        # Blocked: DDL/DML
        blocked_keywords = ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE", "MERGE"]
        for keyword in blocked_keywords:
            if normalized.startswith(keyword):
                return False, f"DDL/DML statements ({keyword}) not allowed"

        return False, "Only SELECT/WITH queries are permitted"

    async def check_view_exists(self, view_name: str) -> bool:
        """
        Check if a view exists in the schema.
        """
        try:
            views = await self.list_views()
            return view_name.upper() in [v.upper() for v in views]
        except Exception:
            return False

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about the Snowflake connection.
        """
        return {
            "database_type": "snowflake",
            "account": self.account,
            "database": self.database,
            "schema": self.schema,
            "warehouse": self.warehouse,
        }

    async def register_data_source(
        self, source_info: Dict[str, Any], transaction_id: Optional[str] = None
    ) -> bool:
        """
        Register a data source (views are pre-registered in curated layer).
        Returns False — not implemented for Snowflake in Phase 10C.
        """
        self.logger.warning("register_data_source not implemented for Snowflake")
        return False

    async def create_fallback_views(
        self, view_names: List[str], transaction_id: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Create fallback views (not implemented for Snowflake).
        Returns False for all views.
        """
        return {name: False for name in view_names}

    async def upsert_record(
        self,
        table: str,
        record: Dict[str, Any],
        key_fields: List[str],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Upsert a record (not implemented for read-only Phase 10C).
        """
        self.logger.warning("upsert_record not implemented for Snowflake")
        return False

    async def get_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single record (not implemented for read-only Phase 10C).
        """
        self.logger.warning("get_record not implemented for Snowflake")
        return None

    async def delete_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a record (not implemented for read-only Phase 10C).
        """
        self.logger.warning("delete_record not implemented for Snowflake")
        return False

    async def fetch_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch records from a table (not implemented for read-only Phase 10C).
        """
        self.logger.warning("fetch_records not implemented for Snowflake")
        return []
