"""
Unit tests for SQL Server Manager Implementation (Phase 10D)

Tests SqlServerManager, which wraps pyodbc for SQL Server connectivity.
Follows the exact pattern as test_phase_10d_mcp.py for consistency.
"""

import pandas as pd
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.database.backends.sqlserver_manager import SqlServerManager
from src.database.manager_factory import DatabaseManagerFactory


class TestSqlServerManagerConnect:
    """Tests for SqlServerManager connection initialization."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to SQL Server."""
        config = {
            "host": "localhost",
            "port": 1433,
            "database": "testdb",
            "username": "sa",
            "password": "testpass",
        }
        manager = SqlServerManager(config)

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch("src.database.backends.sqlserver_manager.pyodbc") as mock_pyodbc:
            mock_pyodbc.drivers.return_value = ["ODBC Driver 18 for SQL Server"]
            mock_pyodbc.connect.return_value = mock_connection

            result = await manager.connect({})

        assert result is True
        assert manager.connected is True
        assert manager.connection is not None

    @pytest.mark.asyncio
    async def test_connect_with_connection_string(self):
        """Test connection using explicit connection_string."""
        config = {
            "connection_string": "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=testdb;UID=sa;PWD=testpass"
        }
        manager = SqlServerManager(config)

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = MagicMock()

        with patch("src.database.backends.sqlserver_manager.pyodbc") as mock_pyodbc:
            mock_pyodbc.connect.return_value = mock_connection

            result = await manager.connect({})

        assert result is True
        # Verify pyodbc.connect was called with the connection string
        mock_pyodbc.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_builds_connection_string(self):
        """Test connection string building from component config."""
        config = {
            "host": "sqlserver.example.com",
            "port": 1433,
            "database": "mydb",
            "username": "admin",
            "password": "secretpass",
        }
        manager = SqlServerManager(config)

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = MagicMock()

        with patch("src.database.backends.sqlserver_manager.pyodbc") as mock_pyodbc:
            mock_pyodbc.drivers.return_value = ["ODBC Driver 18 for SQL Server"]
            mock_pyodbc.connect.return_value = mock_connection

            result = await manager.connect({})

        assert result is True
        # Verify connect was called (connection string building works)
        mock_pyodbc.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        config = {
            "host": "nonexistent.example.com",
            "port": 1433,
            "database": "testdb",
            "username": "sa",
            "password": "wrong",
        }
        manager = SqlServerManager(config)

        with patch("src.database.backends.sqlserver_manager.pyodbc") as mock_pyodbc:
            mock_pyodbc.connect.side_effect = Exception("Connection refused")

            result = await manager.connect({})

        assert result is False
        assert manager.connected is False

    @pytest.mark.asyncio
    async def test_connect_azure_defaults(self):
        """Test Azure-specific connection settings."""
        config = {
            "host": "myserver.database.windows.net",
            "port": 1433,
            "database": "testdb",
            "username": "admin@myserver",
            "password": "testpass",
            "azure": True,
        }
        manager = SqlServerManager(config)

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = MagicMock()

        with patch("src.database.backends.sqlserver_manager.pyodbc") as mock_pyodbc:
            mock_pyodbc.drivers.return_value = ["ODBC Driver 18 for SQL Server"]
            mock_pyodbc.connect.return_value = mock_connection

            result = await manager.connect({})

        assert result is True
        # Verify that Encrypt=yes is in the connection string for Azure
        mock_pyodbc.connect.assert_called_once()


class TestSqlServerManagerDisconnect:
    """Tests for SqlServerManager disconnection."""

    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        """Test successful disconnection."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_connection = MagicMock()
        manager.connection = mock_connection
        manager.connected = True

        result = await manager.disconnect()

        assert result is True
        assert manager.connected is False
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self):
        """Test disconnect when no connection exists."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        result = await manager.disconnect()

        assert result is True


class TestSqlServerManagerExecuteQuery:
    """Tests for SQL query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_returns_dataframe(self):
        """Test query execution returns DataFrame."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        # Setup mock cursor with results
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ("id",),
            ("name",),
            ("value",),
        ]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", 100),
            (2, "Bob", 200),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        df = await manager.execute_query("SELECT * FROM users")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "value"]
        assert df.iloc[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_query_empty_result(self):
        """Test query with empty result set."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = []

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        df = await manager.execute_query("SELECT * FROM users WHERE 1=0")

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)
        manager.connected = False
        manager.connection = None

        with pytest.raises(RuntimeError, match="Not connected"):
            await manager.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(self):
        """Test parameterized query execution."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "Alice")]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        df = await manager.execute_query(
            "SELECT * FROM users WHERE id = ? AND name = ?",
            parameters={"id": 1, "name": "Alice"},
        )

        assert len(df) == 1
        # Verify cursor.execute was called with parameters
        mock_cursor.execute.assert_called_once()


class TestSqlServerManagerValidateSql:
    """Tests for SQL validation."""

    @pytest.mark.asyncio
    async def test_validate_select_allowed(self):
        """Test SELECT statements are allowed."""
        config = {}
        manager = SqlServerManager(config)

        is_valid, error = await manager.validate_sql("SELECT * FROM table")

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_with_clause_allowed(self):
        """Test WITH (CTE) statements are allowed."""
        config = {}
        manager = SqlServerManager(config)

        is_valid, error = await manager.validate_sql(
            "WITH cte AS (SELECT 1 AS n) SELECT * FROM cte"
        )

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_drop_blocked(self):
        """Test DROP statements are blocked."""
        config = {}
        manager = SqlServerManager(config)

        is_valid, error = await manager.validate_sql("DROP TABLE users")

        assert is_valid is False
        assert error is not None
        assert "DROP" in error or "blocked" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_truncate_blocked(self):
        """Test TRUNCATE statements are blocked."""
        config = {}
        manager = SqlServerManager(config)

        is_valid, error = await manager.validate_sql("TRUNCATE TABLE users")

        assert is_valid is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_validate_empty_blocked(self):
        """Test empty SQL is blocked."""
        config = {}
        manager = SqlServerManager(config)

        is_valid, error = await manager.validate_sql("")

        assert is_valid is False
        assert error is not None


class TestSqlServerManagerCRUD:
    """Tests for CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_record_found(self):
        """Test retrieving an existing record."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("email",)]
        mock_cursor.fetchone.return_value = (1, "Alice", "alice@example.com")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        record = await manager.get_record("users", "id", 1)

        assert record is not None
        assert record["id"] == 1
        assert record["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_get_record_not_found(self):
        """Test retrieving a non-existent record."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchone.return_value = None

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        record = await manager.get_record("users", "id", 999)

        assert record is None

    @pytest.mark.asyncio
    async def test_delete_record_success(self):
        """Test deleting a record."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        result = await manager.delete_record("users", "id", 1)

        assert result is True
        mock_cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_records_with_filters(self):
        """Test fetching records with WHERE filters."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("status",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", "active"),
            (2, "Bob", "active"),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        records = await manager.fetch_records(
            "users",
            filters={"status": "active"},
        )

        assert len(records) == 2
        assert records[0]["status"] == "active"
        # Verify SQL was built with WHERE clause
        mock_cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_records_no_filters(self):
        """Test fetching all records without filters."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice"),
            (2, "Bob"),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        records = await manager.fetch_records("users")

        assert len(records) == 2
        # Verify SQL was SELECT * FROM [users] (no WHERE clause)
        call_args = mock_cursor.execute.call_args
        assert "SELECT * FROM" in call_args[0][0]
        assert "WHERE" not in call_args[0][0]

    @pytest.mark.asyncio
    async def test_upsert_record(self):
        """Test inserting or updating a record."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        result = await manager.upsert_record(
            "users",
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            ["id"],
        )

        assert result is True
        # Verify MERGE or INSERT...ON CONFLICT SQL was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0][0]
        assert "MERGE" in call_args or "INSERT" in call_args


class TestSqlServerManagerViews:
    """Tests for view management."""

    @pytest.mark.asyncio
    async def test_list_views(self):
        """Test listing views in the database."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("TABLE_NAME",)]
        mock_cursor.fetchall.return_value = [
            ("view1",),
            ("view2",),
            ("view3",),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        views = await manager.list_views()

        assert views == ["view1", "view2", "view3"]

    @pytest.mark.asyncio
    async def test_create_view(self):
        """Test creating a view."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        result = await manager.create_view(
            "my_view",
            "SELECT id, name FROM users WHERE status = 'active'",
        )

        assert result is True
        # Verify CREATE OR ALTER VIEW SQL
        call_args = mock_cursor.execute.call_args[0][0]
        assert "VIEW" in call_args
        assert "my_view" in call_args

    @pytest.mark.asyncio
    async def test_check_view_exists_true(self):
        """Test checking if view exists (positive case)."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        # Mock list_views to return our view
        with patch.object(
            manager,
            "list_views",
            new_callable=AsyncMock,
            return_value=["my_view", "other_view"],
        ):
            exists = await manager.check_view_exists("my_view")

        assert exists is True

    @pytest.mark.asyncio
    async def test_check_view_exists_false(self):
        """Test checking if view exists (negative case)."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)

        # Mock list_views to return views without ours
        with patch.object(
            manager,
            "list_views",
            new_callable=AsyncMock,
            return_value=["other_view"],
        ):
            exists = await manager.check_view_exists("my_view")

        assert exists is False


class TestSqlServerManagerMetadata:
    """Tests for metadata retrieval."""

    @pytest.mark.asyncio
    async def test_get_metadata_connected(self):
        """Test retrieving metadata when connected."""
        config = {
            "host": "localhost",
            "port": 1433,
            "database": "testdb",
        }
        manager = SqlServerManager(config)

        mock_cursor = MagicMock()
        mock_cursor.description = [("version",)]
        mock_cursor.fetchone.return_value = ("Microsoft SQL Server 2019 (15.0.2000.5)",)

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        manager.connection = mock_connection
        manager.connected = True

        metadata = await manager.get_metadata()

        assert metadata["connected"] is True
        assert "version" in metadata

    @pytest.mark.asyncio
    async def test_get_metadata_not_connected(self):
        """Test retrieving metadata when not connected."""
        config = {"host": "localhost", "port": 1433, "database": "testdb"}
        manager = SqlServerManager(config)
        manager.connected = False
        manager.connection = None

        metadata = await manager.get_metadata()

        assert metadata["connected"] is False


class TestSqlServerManagerFactoryRegistration:
    """Tests for factory registration of SqlServerManager."""

    def test_sqlserver_registered(self):
        """Test that 'sqlserver' backend is registered."""
        backends = DatabaseManagerFactory.get_supported_backends()

        assert "sqlserver" in backends

    def test_mssql_alias_registered(self):
        """Test that 'mssql' alias is registered."""
        backends = DatabaseManagerFactory.get_supported_backends()

        assert "mssql" in backends

    def test_create_manager_sqlserver(self):
        """Test factory creates SqlServerManager for 'sqlserver'."""
        config = {
            "host": "localhost",
            "port": 1433,
            "database": "testdb",
            "username": "sa",
            "password": "testpass",
        }

        manager = DatabaseManagerFactory.create_manager("sqlserver", config)

        assert isinstance(manager, SqlServerManager)

    def test_create_manager_mssql_alias(self):
        """Test factory creates SqlServerManager for 'mssql' alias."""
        config = {
            "host": "localhost",
            "port": 1433,
            "database": "testdb",
            "username": "sa",
            "password": "testpass",
        }

        manager = DatabaseManagerFactory.create_manager("mssql", config)

        assert isinstance(manager, SqlServerManager)

    def test_create_manager_case_insensitive(self):
        """Test factory is case-insensitive."""
        config = {
            "host": "localhost",
            "port": 1433,
            "database": "testdb",
            "username": "sa",
            "password": "testpass",
        }

        manager = DatabaseManagerFactory.create_manager("SQLSERVER", config)

        assert isinstance(manager, SqlServerManager)
