"""
MCP Manager - DatabaseManager implementation for vendor-managed MCP servers.

Implements the DatabaseManager ABC to provide read-only schema discovery and query
execution via vendor-managed MCP servers (Snowflake, Databricks, BigQuery).

Vendor-specific tool mapping:
- Snowflake: Uses Cortex Analyst semantic views + SQL execution
- Databricks: Uses Unity Catalog metadata + SQL execution
- BigQuery: Uses INFORMATION_SCHEMA queries via MCP

Design:
- Wraps MCPClient for HTTP transport and authentication
- Per-vendor tool name mapping to handle API differences
- Parses MCP text results (JSON/CSV) into pandas DataFrames
- Phase 10C stance: read-only (write methods return False/empty)
"""

import json
import logging
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.database.manager_interface import DatabaseManager
from src.database.mcp_client import MCPClient, MCPError


# Per-vendor tool name mappings for MCP servers
# Maps logical operation → vendor-specific MCP tool name
VENDOR_TOOL_MAPS = {
    "snowflake": {
        "execute_query": "sql_execute",
        "list_views": "list_tables",  # Fallback to SQL if not available
        "get_metadata": "get_database_info",
    },
    "databricks": {
        "execute_query": "sql_execute",
        "list_views": "list_tables",
        "get_metadata": "get_catalog_info",
    },
    "bigquery": {
        "execute_query": "bigquery_run_query",
        "list_views": "bigquery_list_tables",
        "get_metadata": "bigquery_get_dataset_info",
    },
}

# SQL-based fallback for listing views (when MCP tool not available)
INFORMATION_SCHEMA_QUERIES = {
    "snowflake": "SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}' AND table_type = 'VIEW'",
    "databricks": "SELECT name FROM information_schema.tables WHERE table_schema = '{schema}' AND table_type = 'VIEW'",
    "bigquery": "SELECT table_name FROM `{project}.{schema}.INFORMATION_SCHEMA.TABLES` WHERE table_type = 'VIEW'",
}


class MCPManager(DatabaseManager):
    """
    DatabaseManager implementation for vendor-managed MCP servers.

    Supports Snowflake, Databricks, and BigQuery MCP servers with platform-adaptive
    schema discovery and query execution.

    Lifecycle:
    1. __init__: Store vendor type
    2. connect(): Initialize MCPClient with auth credentials
    3. discover_tables(), profile_table(), execute_query(), etc.
    4. disconnect(): Close MCPClient

    Read-only stance: execute_query() and list_views() work; write methods return False.
    """

    def __init__(
        self,
        vendor: str,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize MCPManager for a specific vendor.

        Args:
            vendor: Vendor type: "snowflake", "databricks", or "bigquery"
            config: Configuration dict containing MCP connection details:
                - mcp_endpoint: Base URL of MCP server
                - mcp_auth_type: Auth type ("bearer", "pat", "gcp_oidc")
                - schema: Default schema/database name
            logger: Optional logger instance
        """
        self.vendor = vendor.lower()
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.mcp_client: Optional[MCPClient] = None
        self.schema = config.get("schema", "")
        self.connected = False

    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish connection to MCP server.

        Args:
            connection_params: Runtime parameters containing:
                - mcp_endpoint: MCP server endpoint URL
                - auth_token: Bearer token or callable returning token
                - mcp_auth_type: Auth type (bearer, pat, gcp_oidc)

        Returns:
            True if connection successful, False otherwise
        """
        try:
            endpoint = connection_params.get("mcp_endpoint")
            auth_token = connection_params.get("auth_token")
            auth_type = connection_params.get("mcp_auth_type", "bearer")

            if not endpoint or not auth_token:
                self.logger.error("MCP endpoint and auth_token are required")
                return False

            self.mcp_client = MCPClient(
                endpoint=endpoint,
                auth_token=auth_token,
                auth_type=auth_type,
                logger=self.logger,
            )

            # Test connection by listing tools
            tools = await self.mcp_client.list_tools()
            if not tools:
                self.logger.warning(f"MCP server at {endpoint} returned empty tool list")

            self.connected = True
            self.logger.info(f"Connected to {self.vendor} MCP server at {endpoint}")
            return True
        except MCPError as exc:
            self.logger.error(f"MCP connection failed: {exc}")
            return False
        except Exception as exc:
            self.logger.error(f"Unexpected error during MCP connect: {exc}")
            return False

    async def disconnect(self) -> bool:
        """Close MCP server connection."""
        if self.mcp_client:
            try:
                await self.mcp_client.close()
                self.connected = False
                self.logger.info(f"Disconnected from {self.vendor} MCP server")
                return True
            except Exception as exc:
                self.logger.error(f"Error disconnecting from MCP: {exc}")
                return False
        return True

    async def execute_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query via MCP server.

        Args:
            sql: SQL query to execute
            parameters: Optional query parameters (not used in MCP context)
            transaction_id: Optional transaction ID for logging

        Returns:
            DataFrame with query results, or empty DataFrame on error
        """
        if not self.mcp_client or not self.connected:
            self.logger.error("MCP client not connected")
            return pd.DataFrame()

        try:
            tool_name = VENDOR_TOOL_MAPS.get(self.vendor, {}).get("execute_query", "sql_execute")
            result = await self.mcp_client.call_tool(tool_name, {"sql": sql})

            if result.is_error:
                self.logger.error(f"MCP query error: {result.get_text()}")
                return pd.DataFrame()

            # Parse result text as JSON or CSV
            text = result.get_text()
            if not text:
                return pd.DataFrame()

            try:
                # Try JSON first
                data = json.loads(text)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict):
                    return pd.DataFrame([data])
            except json.JSONDecodeError:
                # Fallback to CSV
                try:
                    return pd.read_csv(StringIO(text))
                except Exception as exc:
                    self.logger.error(f"Failed to parse query result as JSON or CSV: {exc}")
                    return pd.DataFrame()

        except MCPError as exc:
            self.logger.error(f"MCP query execution failed: {exc}")
            return pd.DataFrame()

    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """
        List available views in the schema.

        Args:
            transaction_id: Optional transaction ID for logging

        Returns:
            List of view names, or empty list on error
        """
        if not self.mcp_client or not self.connected:
            self.logger.error("MCP client not connected")
            return []

        try:
            # Try vendor-specific tool first
            tool_name = VENDOR_TOOL_MAPS.get(self.vendor, {}).get("list_views")
            if tool_name:
                try:
                    result = await self.mcp_client.call_tool(tool_name, {"schema": self.schema})
                    text = result.get_text()
                    if text:
                        data = json.loads(text)
                        if isinstance(data, list):
                            return [item.get("name", "") if isinstance(item, dict) else str(item) for item in data]
                except (MCPError, json.JSONDecodeError):
                    pass

            # Fallback to INFORMATION_SCHEMA query
            query = INFORMATION_SCHEMA_QUERIES.get(self.vendor, "").format(schema=self.schema)
            if query:
                df = await self.execute_query(query)
                if not df.empty:
                    col_name = df.columns[0] if len(df.columns) > 0 else None
                    if col_name:
                        return df[col_name].tolist()

            return []
        except Exception as exc:
            self.logger.error(f"Error listing views: {exc}")
            return []

    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query for security and correctness.

        Uses a local allowlist (same as Phase 10C managers): allows SELECT/WITH,
        blocks DDL/DML (INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE).

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not isinstance(sql, str):
            return False, "SQL query must be a non-empty string"

        normalized = sql.strip().upper()

        # Allowlist safe read operations
        safe_starts = ("SELECT", "WITH")
        if normalized.startswith(safe_starts):
            return True, None

        # Blocklist dangerous operations
        dangerous_starts = ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE", "MERGE")
        if normalized.startswith(dangerous_starts):
            return False, f"Query blocked: {dangerous_starts[0]} not allowed (read-only mode)"

        return False, "Query must be a SELECT or WITH statement"

    async def create_view(
        self,
        view_name: str,
        sql: str,
        replace_existing: bool = True,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """Phase 10C stance: write operations not supported via MCP."""
        self.logger.warning(f"create_view not supported via MCP (read-only mode)")
        return False

    async def register_data_source(
        self,
        source_info: Dict[str, Any],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """Phase 10C stance: write operations not supported via MCP."""
        self.logger.warning("register_data_source not supported via MCP (read-only mode)")
        return False

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the MCP server connection.

        Returns:
            Dict with connection and vendor info
        """
        if not self.mcp_client or not self.connected:
            return {}

        return {
            "vendor": self.vendor,
            "endpoint": self.mcp_client.endpoint,
            "auth_type": self.mcp_client.auth_type,
            "schema": self.schema,
            "connected": True,
        }

    async def check_view_exists(self, view_name: str) -> bool:
        """
        Check if a view exists in the schema.

        Args:
            view_name: Name of view to check

        Returns:
            True if view exists, False otherwise
        """
        views = await self.list_views()
        return view_name.lower() in [v.lower() for v in views]

    async def create_fallback_views(
        self,
        view_names: List[str],
        transaction_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Phase 10C stance: write operations not supported via MCP."""
        self.logger.warning("create_fallback_views not supported via MCP (read-only mode)")
        return {name: False for name in view_names}

    async def upsert_record(
        self,
        table: str,
        record: Dict[str, Any],
        key_fields: List[str],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """Phase 10C stance: write operations not supported via MCP."""
        self.logger.warning(f"upsert_record not supported via MCP (read-only mode)")
        return False

    async def get_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Phase 10C stance: record access not supported via MCP."""
        return None

    async def delete_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """Phase 10C stance: write operations not supported via MCP."""
        self.logger.warning(f"delete_record not supported via MCP (read-only mode)")
        return False

    async def fetch_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Phase 10C stance: record access not supported via MCP."""
        return []
