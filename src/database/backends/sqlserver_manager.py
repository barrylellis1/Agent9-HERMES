"""
SQL Server / Azure SQL Manager Implementation for Agent9.

This module implements the DatabaseManager interface for Microsoft SQL Server
and Azure SQL Database. It uses pyodbc with asyncio.to_thread() for async
compatibility, following the same pattern as BigQuery's synchronous SDK wrapper.

Covers the largest ICP segment (~50-60% of target mid-market) running SQL Server
on-premises or Azure SQL in the cloud.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import pyodbc
    _PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None  # type: ignore
    _PYODBC_AVAILABLE = False

from src.database.manager_interface import DatabaseManager

logger = logging.getLogger(__name__)

# Preferred ODBC drivers in order of preference
_PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server",  # legacy Windows driver — always present on Windows
]


def _detect_driver() -> str:
    """Return the best available SQL Server ODBC driver."""
    if not _PYODBC_AVAILABLE:
        raise RuntimeError(
            "pyodbc is not available. Install unixODBC system library and pyodbc."
        )
    available = pyodbc.drivers()
    for preferred in _PREFERRED_DRIVERS:
        if preferred in available:
            return preferred
    sql_drivers = [d for d in available if "SQL Server" in d]
    if sql_drivers:
        return sql_drivers[0]
    raise RuntimeError(
        "No SQL Server ODBC driver found. "
        "Install 'ODBC Driver 18 for SQL Server' from "
        "https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
    )


_DEFAULT_DRIVER = "ODBC Driver 18 for SQL Server"
_DEFAULT_PORT = 1433
_DEFAULT_SCHEMA = "dbo"


class SqlServerManager(DatabaseManager):
    """
    SQL Server / Azure SQL implementation of the DatabaseManager interface.

    Uses pyodbc wrapped with asyncio.to_thread() for async compatibility.
    Supports both on-premises SQL Server and Azure SQL Database.

    Connection can be provided as an explicit connection string or built from
    individual components (host, port, database, username, password, driver).

    Azure SQL-specific options (encrypt, trust_server_certificate) are supported
    via config keys.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the SQL Server manager.

        Args:
            config: Configuration dictionary containing:
                - host (str): Server hostname or IP
                - port (int, optional): TCP port, default 1433
                - database (str): Database name
                - username (str): Login username (also accepted as 'user')
                - password (str): Login password
                - driver (str, optional): ODBC driver name, default 'ODBC Driver 18 for SQL Server'
                - schema (str, optional): Default schema, default 'dbo'
                - encrypt (bool, optional): Require encrypted connection, default True
                - trust_server_certificate (bool, optional): Trust self-signed cert, default False
                - connection_string (str, optional): Explicit ODBC connection string; overrides
                  all individual component settings when provided
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._connection: Optional[pyodbc.Connection] = None
        self._is_connected = False
        self._schema = config.get("schema", _DEFAULT_SCHEMA)

    # ------------------------------------------------------------------
    # Public property accessors (used by tests and external callers)
    # ------------------------------------------------------------------

    @property
    def connection(self) -> Optional[pyodbc.Connection]:
        return self._connection

    @connection.setter
    def connection(self, value: Optional[pyodbc.Connection]) -> None:
        self._connection = value

    @property
    def connected(self) -> bool:
        return self._is_connected

    @connected.setter
    def connected(self, value: bool) -> None:
        self._is_connected = value

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a connection to the SQL Server database.

        Merges init config with connection_params. Accepts either an explicit
        'connection_string' key or builds one from individual components.

        Args:
            connection_params: Connection parameters (can override init config)

        Returns:
            True if connection successful, False otherwise
        """
        if not _PYODBC_AVAILABLE:
            self.logger.error(
                "Cannot connect to SQL Server: pyodbc/unixODBC not available in this environment."
            )
            return False

        try:
            params = {**self.config, **connection_params}

            conn_str = params.get("connection_string")
            if not conn_str:
                conn_str = self._build_connection_string(params)

            self.logger.info(
                "Connecting to SQL Server at %s:%s",
                params.get("host", "unknown"),
                params.get("port", _DEFAULT_PORT),
            )

            # pyodbc.connect is synchronous — offload to a thread
            self._connection = await asyncio.to_thread(
                pyodbc.connect, conn_str, autocommit=True
            )
            self._is_connected = True
            self.logger.info("Successfully connected to SQL Server")
            return True

        except Exception as exc:
            self.logger.error("Failed to connect to SQL Server: %s", exc)
            self._is_connected = False
            return False

    async def disconnect(self) -> bool:
        """Close the connection to SQL Server."""
        if self._connection:
            try:
                await asyncio.to_thread(self._connection.close)
            except Exception as exc:
                self.logger.warning("Error closing SQL Server connection: %s", exc)
            finally:
                self._connection = None
                self._is_connected = False
                self.logger.info("Disconnected from SQL Server")
        return True

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    async def execute_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.

        Wraps synchronous pyodbc cursor execution with asyncio.to_thread().
        Named parameters are not supported by pyodbc; use '?' placeholders and
        pass a list/tuple via parameters if positional binding is needed.
        Passing a dict will log a warning and execute without parameters.

        Args:
            sql: SQL query to execute
            parameters: Optional parameters. If a dict is provided a warning is
                logged; positional '?' binding is pyodbc's native style.
            transaction_id: Optional transaction identifier for logging

        Returns:
            DataFrame containing query results (empty DataFrame if no rows)
        """
        if not self._connection:
            raise RuntimeError("Not connected to SQL Server database")

        def _run() -> pd.DataFrame:
            cursor = self._connection.cursor()
            try:
                if parameters:
                    if isinstance(parameters, dict):
                        self.logger.warning(
                            "pyodbc uses positional '?' placeholders — "
                            "named dict parameters are not supported; executing without params"
                        )
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, parameters)
                else:
                    cursor.execute(sql)

                if cursor.description is None:
                    # Non-SELECT statement (DDL, DML)
                    return pd.DataFrame()

                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                if not rows:
                    return pd.DataFrame(columns=columns)

                return pd.DataFrame.from_records(rows, columns=columns)
            finally:
                cursor.close()

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            self.logger.error("Query execution failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # View management
    # ------------------------------------------------------------------

    async def create_view(
        self,
        view_name: str,
        sql: str,
        replace_existing: bool = True,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Create a database view.

        Uses 'CREATE OR ALTER VIEW' (SQL Server 2016+ syntax) when
        replace_existing is True; plain 'CREATE VIEW' otherwise.

        Args:
            view_name: Name of the view to create (bracket-quoted automatically)
            sql: SELECT statement that defines the view
            replace_existing: If True use CREATE OR ALTER VIEW
            transaction_id: Optional transaction identifier for logging

        Returns:
            True if the view was created successfully, False otherwise
        """
        if not self._connection:
            return False

        try:
            quoted_name = self._quote_identifier(view_name)
            if replace_existing:
                ddl = f"CREATE OR ALTER VIEW {quoted_name} AS {sql}"
            else:
                ddl = f"CREATE VIEW {quoted_name} AS {sql}"

            await asyncio.to_thread(self._execute_non_query, ddl)
            return True
        except Exception as exc:
            self.logger.error("Create view failed: %s", exc)
            return False

    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """
        List all views in the configured schema (default: dbo).

        Queries INFORMATION_SCHEMA.VIEWS filtered by TABLE_SCHEMA.

        Returns:
            List of view names
        """
        if not self._connection:
            return []

        sql = (
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS "
            "WHERE TABLE_SCHEMA = ?"
        )

        def _run() -> List[str]:
            cursor = self._connection.cursor()
            try:
                cursor.execute(sql, self._schema)
                return [row[0] for row in cursor.fetchall()]
            finally:
                cursor.close()

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            self.logger.error("List views failed: %s", exc)
            return []

    async def check_view_exists(self, view_name: str) -> bool:
        """Check whether a view exists in the configured schema."""
        views = await self.list_views()
        return view_name in views

    async def create_fallback_views(
        self,
        view_names: List[str],
        transaction_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Create emergency fallback views.

        Not applicable for SQL Server — returns False for all requested names,
        matching the Postgres pattern.
        """
        return {name: False for name in view_names}

    # ------------------------------------------------------------------
    # Data registration
    # ------------------------------------------------------------------

    async def register_data_source(
        self,
        source_info: Dict[str, Any],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Register a data source.

        Not applicable for SQL Server (tables/views are created directly).
        Logs the intent and returns True, matching the Postgres pattern.
        """
        self.logger.info(
            "register_data_source not required for SQL Server; source_info keys: %s",
            list(source_info.keys()),
        )
        return True

    # ------------------------------------------------------------------
    # SQL validation
    # ------------------------------------------------------------------

    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query for safety.

        Rejects queries containing potentially destructive statements:
        DROP TABLE, DROP DATABASE, TRUNCATE, DELETE FROM, UPDATE.
        Allows SELECT and WITH (CTE) queries.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL"

        forbidden = ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "DELETE FROM", "UPDATE"]
        upper_sql = sql.upper()
        for term in forbidden:
            if term in upper_sql:
                return False, f"Potentially destructive command '{term}' detected"

        return True, None

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Retrieve metadata about the SQL Server connection.

        Queries @@VERSION for the server version string.

        Returns:
            Dictionary with connection state, type, and version
        """
        if not self._connection:
            return {"connected": False}

        def _run() -> str:
            cursor = self._connection.cursor()
            try:
                cursor.execute("SELECT @@VERSION")
                row = cursor.fetchone()
                return row[0] if row else "unknown"
            finally:
                cursor.close()

        try:
            version = await asyncio.to_thread(_run)
            return {
                "connected": True,
                "type": "sqlserver",
                "version": version,
                "schema": self._schema,
            }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    async def upsert_record(
        self,
        table: str,
        record: Dict[str, Any],
        key_fields: List[str],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Insert or update a record using the SQL Server MERGE statement.

        Constructs a MERGE … USING (VALUES …) AS src ON <key match>
        WHEN MATCHED THEN UPDATE … WHEN NOT MATCHED THEN INSERT … pattern.

        Args:
            table: Target table name
            record: Dictionary mapping column names to values
            key_fields: Column(s) used to identify an existing row
            transaction_id: Optional transaction identifier for logging

        Returns:
            True if the MERGE completed without error, False otherwise
        """
        if not self._connection:
            return False

        try:
            columns = list(record.keys())
            values = list(record.values())
            quoted_table = self._quote_identifier(table)

            # Source alias columns and placeholders
            src_cols = ", ".join(
                f"{self._quote_identifier(c)} = ?" for c in columns
            )
            # Build ON clause for key fields
            on_clauses = " AND ".join(
                f"tgt.{self._quote_identifier(k)} = src.{self._quote_identifier(k)}"
                for k in key_fields
            )

            # UPDATE SET — only non-key columns
            update_cols = [c for c in columns if c not in key_fields]
            update_set = ", ".join(
                f"tgt.{self._quote_identifier(c)} = src.{self._quote_identifier(c)}"
                for c in update_cols
            )

            # INSERT columns and values
            insert_cols = ", ".join(self._quote_identifier(c) for c in columns)
            insert_src_cols = ", ".join(
                f"src.{self._quote_identifier(c)}" for c in columns
            )

            # Source row: VALUES (?, ?, ...) AS src (col1, col2, ...)
            placeholders = ", ".join("?" * len(columns))
            src_alias_cols = ", ".join(self._quote_identifier(c) for c in columns)

            merge_sql = (
                f"MERGE {quoted_table} AS tgt "
                f"USING (SELECT {src_cols.replace('= ?', '')}) "  # replaced below
            )

            # Reconstruct using the proper VALUES pattern
            merge_sql = (
                f"MERGE {quoted_table} AS tgt "
                f"USING (VALUES ({placeholders})) AS src ({src_alias_cols}) "
                f"ON ({on_clauses}) "
            )
            if update_cols:
                merge_sql += f"WHEN MATCHED THEN UPDATE SET {update_set} "
            merge_sql += (
                f"WHEN NOT MATCHED THEN INSERT ({insert_cols}) "
                f"VALUES ({insert_src_cols});"
            )

            def _run():
                cursor = self._connection.cursor()
                try:
                    cursor.execute(merge_sql, values)
                    cursor.commit() if not self._connection.autocommit else None
                finally:
                    cursor.close()

            await asyncio.to_thread(_run)
            return True

        except Exception as exc:
            self.logger.error("Upsert (MERGE) failed for table %s: %s", table, exc)
            return False

    async def get_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single record by its key.

        Uses SELECT TOP 1 to match SQL Server syntax (no LIMIT clause).

        Returns:
            Dictionary representing the row if found, None otherwise
        """
        if not self._connection:
            return None

        quoted_table = self._quote_identifier(table)
        quoted_key = self._quote_identifier(key_field)
        sql = f"SELECT TOP 1 * FROM {quoted_table} WHERE {quoted_key} = ?"

        def _run() -> Optional[Dict[str, Any]]:
            cursor = self._connection.cursor()
            try:
                cursor.execute(sql, key_value)
                row = cursor.fetchone()
                if row is None:
                    return None
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            finally:
                cursor.close()

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            self.logger.error("Get record failed for table %s: %s", table, exc)
            return None

    async def delete_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a record by its key.

        Returns:
            True if the DELETE executed without error, False on exception
        """
        if not self._connection:
            return False

        quoted_table = self._quote_identifier(table)
        quoted_key = self._quote_identifier(key_field)
        sql = f"DELETE FROM {quoted_table} WHERE {quoted_key} = ?"

        def _run():
            cursor = self._connection.cursor()
            try:
                cursor.execute(sql, key_value)
            finally:
                cursor.close()

        try:
            await asyncio.to_thread(_run)
            return True
        except Exception as exc:
            self.logger.error("Delete record failed for table %s: %s", table, exc)
            return False

    async def fetch_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple records from a table with optional AND-combined filters.

        Uses '?' positional placeholders (pyodbc standard).

        Returns:
            List of row dictionaries; empty list on error or no results
        """
        if not self._connection:
            return []

        quoted_table = self._quote_identifier(table)
        sql = f"SELECT * FROM {quoted_table}"
        values: List[Any] = []

        if filters:
            conditions = [
                f"{self._quote_identifier(k)} = ?" for k in filters
            ]
            values = list(filters.values())
            sql += " WHERE " + " AND ".join(conditions)

        def _run() -> List[Dict[str, Any]]:
            cursor = self._connection.cursor()
            try:
                cursor.execute(sql, values) if values else cursor.execute(sql)
                rows = cursor.fetchall()
                if not rows:
                    return []
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            finally:
                cursor.close()

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            self.logger.error("Fetch records failed for table %s: %s", table, exc)
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_connection_string(self, params: Dict[str, Any]) -> str:
        """
        Build an ODBC connection string from individual config parameters.

        Args:
            params: Merged config dictionary

        Returns:
            ODBC connection string suitable for pyodbc.connect()
        """
        driver = params.get("driver") or _detect_driver()
        host = params.get("host", "localhost")
        port = params.get("port", _DEFAULT_PORT)
        database = params.get("database", "")
        username = params.get("username") or params.get("user", "")
        password = params.get("password", "")

        # SQL Server connection string uses SERVER=host,port notation
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
        )

        # Encryption settings — Azure SQL requires Encrypt=yes by default
        encrypt = params.get("encrypt", True)
        trust_cert = params.get("trust_server_certificate", False)
        conn_str += f"Encrypt={'yes' if encrypt else 'no'};"
        conn_str += f"TrustServerCertificate={'yes' if trust_cert else 'no'};"

        return conn_str

    def _quote_identifier(self, name: str) -> str:
        """
        Bracket-quote a SQL Server identifier.

        Handles schema-qualified names (schema.table) by quoting each part
        separately. Existing brackets are stripped before re-quoting to avoid
        double-quoting.

        Args:
            name: Identifier string (may contain dots for schema qualification)

        Returns:
            Bracket-quoted identifier string
        """
        parts = name.split(".")
        quoted_parts = []
        for part in parts:
            clean = part.strip("[]")
            quoted_parts.append(f"[{clean}]")
        return ".".join(quoted_parts)

    def _execute_non_query(self, sql: str) -> None:
        """
        Execute a non-SELECT statement synchronously (intended for use inside
        asyncio.to_thread calls).

        Args:
            sql: SQL statement to execute
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql)
        finally:
            cursor.close()
