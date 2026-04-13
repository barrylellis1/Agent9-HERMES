"""
Databricks Manager - Implementation of the database manager interface for Databricks.

This module implements the DatabaseManager interface for Databricks SQL Connector,
providing query execution and metadata helpers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.database.manager_interface import DatabaseManager

try:  # pragma: no cover
    from databricks import sql
except Exception:  # pragma: no cover
    sql = None  # type: ignore


class DatabricksManager(DatabaseManager):
    """
    DatabaseManager implementation for Databricks.
    Provides curated view discovery and SQL execution capabilities.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        self.conn: Optional["sql.sql.Connection"] = None  # type: ignore
        self.server_hostname: Optional[str] = self.config.get("server_hostname")
        self.http_path: Optional[str] = self.config.get("http_path")
        self.catalog: Optional[str] = self.config.get("catalog")
        self.schema: Optional[str] = self.config.get("schema")

    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a Databricks SQL connection using the provided parameters.

        Args:
            connection_params: Dict with 'access_token' (personal access token)

        Returns:
            True if connection successful, False otherwise
        """
        if sql is None:
            self.logger.error("databricks-sql-connector package is not installed")
            return False

        try:
            params = dict(self.config)
            params.update(connection_params or {})

            conn_kwargs = {
                "server_hostname": params.get("server_hostname") or self.server_hostname,
                "http_path": params.get("http_path") or self.http_path,
                "access_token": params.get("access_token"),
            }

            if not conn_kwargs["access_token"]:
                self.logger.error("'access_token' must be provided for Databricks connection")
                return False

            # Optional: catalog and schema
            if params.get("catalog") or self.catalog:
                conn_kwargs["catalog"] = params.get("catalog") or self.catalog
            if params.get("schema") or self.schema:
                conn_kwargs["schema"] = params.get("schema") or self.schema

            # Remove None values
            conn_kwargs = {k: v for k, v in conn_kwargs.items() if v is not None}

            # Create connection in thread pool
            self.conn = await asyncio.to_thread(sql.connect, **conn_kwargs)

            self.logger.info(
                "Connected to Databricks at '%s' (catalog=%s, schema=%s)",
                self.server_hostname,
                self.catalog,
                self.schema,
            )
            return True
        except Exception as exc:
            self.logger.error("Failed to connect to Databricks: %s", exc)
            self.conn = None
            return False

    async def disconnect(self) -> bool:
        """
        Close the Databricks connection.
        """
        try:
            if self.conn:
                await asyncio.to_thread(self.conn.close)
                self.conn = None
            return True
        except Exception as exc:
            self.logger.warning("Error closing Databricks connection: %s", exc)
            return False

    async def execute_query(
        self,
        sql_query: str,
        parameters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.
        """
        if not self.conn:
            raise RuntimeError("Databricks connection not established. Call connect() first.")

        try:
            self.logger.debug(f"[{transaction_id}] Executing query: {sql_query[:200]}...")

            # Execute query in thread pool
            cursor = await asyncio.to_thread(self.conn.cursor)
            await asyncio.to_thread(cursor.execute, sql_query, parameters)

            # Fetch results and convert to DataFrame
            # Databricks SQL Connector returns pyarrow Table, convert to pandas
            results = await asyncio.to_thread(cursor.fetchall_arrow)
            df = results.to_pandas() if results else pd.DataFrame()
            await asyncio.to_thread(cursor.close)

            self.logger.debug(f"[{transaction_id}] Query returned {len(df)} rows")
            return df
        except Exception as exc:
            self.logger.error(f"[{transaction_id}] Query execution failed: {exc}")
            raise

    async def create_view(
        self,
        view_name: str,
        sql_def: str,
        replace_existing: bool = True,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Create a view in Databricks.

        Note: For Phase 10C, views are customer-managed in curated layer.
        This method provides testing support.
        """
        try:
            if replace_existing:
                drop_sql = f"DROP VIEW IF EXISTS {view_name}"
                await self.execute_query(drop_sql, transaction_id=transaction_id)

            create_sql = f"CREATE OR REPLACE VIEW {view_name} AS\n{sql_def}"
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
            sql_query = f"""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = '{self.schema}'
            ORDER BY table_name
            """
            df = await self.execute_query(sql_query, transaction_id=transaction_id)
            return df["table_name"].tolist() if not df.empty else []
        except Exception as exc:
            self.logger.warning(f"[{transaction_id}] Failed to list views: {exc}")
            return []

    async def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL by checking for DDL/DML statements (not allowed).
        Only SELECT/WITH queries permitted.
        """
        normalized = sql_query.strip().upper()

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
            return view_name.lower() in [v.lower() for v in views]
        except Exception:
            return False

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about the Databricks connection.
        """
        return {
            "database_type": "databricks",
            "server_hostname": self.server_hostname,
            "catalog": self.catalog,
            "schema": self.schema,
        }

    async def register_data_source(
        self, source_info: Dict[str, Any], transaction_id: Optional[str] = None
    ) -> bool:
        """
        Register a data source (views are pre-registered in curated layer).
        Returns False — not implemented for Databricks in Phase 10C.
        """
        self.logger.warning("register_data_source not implemented for Databricks")
        return False

    async def create_fallback_views(
        self, view_names: List[str], transaction_id: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Create fallback views (not implemented for Databricks).
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
        self.logger.warning("upsert_record not implemented for Databricks")
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
        self.logger.warning("get_record not implemented for Databricks")
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
        self.logger.warning("delete_record not implemented for Databricks")
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
        self.logger.warning("fetch_records not implemented for Databricks")
        return []
