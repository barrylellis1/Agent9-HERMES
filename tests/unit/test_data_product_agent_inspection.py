"""
Unit tests for Data Product Agent schema inspection workflow.

Tests cover:
- _resolve_inspection_settings: metadata resolution from request/registry/connection profile
- _prepare_inspection_manager: dynamic manager selection (DuckDB vs BigQuery)
- _discover_tables_for_inspection: table/view enumeration per backend
- _profile_table: dispatching to backend-specific profiling
- inspect_source_schema: end-to-end inspection workflow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.models.data_product_onboarding_models import (
    DataProductSchemaInspectionRequest,
    DataProductSchemaInspectionResponse,
    TableProfile,
    TableColumnProfile,
)


@pytest.fixture
def mock_registry_factory():
    """Mock registry factory with data product provider."""
    factory = MagicMock()
    dp_provider = MagicMock()
    
    # Mock data product with BigQuery source_system
    mock_dp = MagicMock()
    mock_dp.source_system = "bigquery"
    mock_dp.metadata = {
        "project": "test-project",
        "dataset": "test_dataset",
    }
    dp_provider.get.return_value = mock_dp
    
    factory.get_provider.return_value = dp_provider
    return factory


@pytest.fixture
def mock_duckdb_manager():
    """Mock DuckDB manager for inspection."""
    manager = AsyncMock()
    manager.is_connected.return_value = True
    manager.execute_query = AsyncMock(return_value={
        "columns": ["table_name"],
        "rows": [{"table_name": "test_table"}],
    })
    return manager


@pytest.fixture
def mock_bigquery_manager():
    """Mock BigQuery manager for inspection."""
    manager = AsyncMock()
    manager.connect = AsyncMock(return_value=True)
    manager.disconnect = AsyncMock()
    manager.execute_query = AsyncMock(return_value={
        "columns": ["table_name"],
        "rows": [{"table_name": "test_view"}],
    })
    return manager


@pytest.fixture
def data_product_agent(mock_registry_factory, mock_duckdb_manager):
    """Create a Data Product Agent with mocked dependencies."""
    config = {
        "agent_id": "test_dpa",
        "database": {"type": "duckdb", "path": ":memory:"},
        "bypass_mcp": True,
        "registry_factory": mock_registry_factory,
    }
    
    agent = A9_Data_Product_Agent(config=config)  # arch-allow-agent-ctor
    agent.db_manager = mock_duckdb_manager
    
    return agent


class TestResolveInspectionSettings:
    """Tests for _resolve_inspection_settings method."""
    
    @pytest.mark.asyncio
    async def test_resolve_settings_from_request(self, data_product_agent):
        """Test settings resolution when request provides all details."""
        request = DataProductSchemaInspectionRequest(
            request_id="test_001",
            principal_id="test_user",
            source_system="duckdb",
            schema="main",
            tables=["table1", "table2"],
            connection_overrides={"path": "/custom/path.db"},
        )
        
        settings = data_product_agent._resolve_inspection_settings(request)
        
        assert settings["source_system"] == "duckdb"
        assert settings["schema"] == "main"
        assert settings["tables"] == ["table1", "table2"]
        assert settings["connection_overrides"]["path"] == "/custom/path.db"
    
    @pytest.mark.asyncio
    async def test_resolve_settings_from_registry(self, data_product_agent):
        """Test settings resolution from registry metadata when request is minimal."""
        request = DataProductSchemaInspectionRequest(
            request_id="test_002",
            principal_id="test_user",
            data_product_id="dp_test_001",
        )
        
        settings = data_product_agent._resolve_inspection_settings(request)
        
        # Should pull source_system from registry
        assert settings["source_system"] == "bigquery"
        assert settings["project"] == "test-project"
        assert settings["schema"] == "test_dataset"
    
    @pytest.mark.asyncio
    async def test_resolve_settings_defaults_to_duckdb(self, data_product_agent):
        """Test settings resolution defaults to DuckDB when no metadata available."""
        # Mock provider to return None
        data_product_agent.data_product_provider.get.return_value = None
        
        request = DataProductSchemaInspectionRequest(
            request_id="test_003",
            principal_id="test_user",
        )
        
        settings = data_product_agent._resolve_inspection_settings(request)
        
        assert settings["source_system"] == "duckdb"


class TestPrepareInspectionManager:
    """Tests for _prepare_inspection_manager method."""
    
    @pytest.mark.asyncio
    async def test_prepare_duckdb_manager_reuses_existing(self, data_product_agent):
        """Test DuckDB manager preparation reuses existing connection."""
        settings = {
            "source_system": "duckdb",
            "connection_config": {"type": "duckdb", "path": ":memory:"},
            "connection_params": {},
        }
        
        manager, cleanup_needed = await data_product_agent._prepare_inspection_manager(settings)
        
        assert manager is data_product_agent.db_manager
        assert cleanup_needed is False
    
    @pytest.mark.asyncio
    async def test_prepare_bigquery_manager_creates_new(self, data_product_agent, mock_bigquery_manager):
        """Test BigQuery manager preparation creates new instance."""
        settings = {
            "source_system": "bigquery",
            "connection_config": {
                "type": "bigquery",
                "project": "test-project",
                "dataset": "test_dataset",
            },
            "connection_params": {
                "service_account_info": {"type": "service_account"},
            },
        }
        
        with patch("src.database.manager_factory.DatabaseManagerFactory.create_manager", return_value=mock_bigquery_manager):
            manager, cleanup_needed = await data_product_agent._prepare_inspection_manager(settings)
            
            assert manager is mock_bigquery_manager
            assert cleanup_needed is True
            mock_bigquery_manager.connect.assert_called_once()


class TestDiscoverTablesForInspection:
    """Tests for _discover_tables_for_inspection method."""
    
    @pytest.mark.asyncio
    async def test_discover_uses_explicit_tables_when_provided(self, data_product_agent, mock_duckdb_manager):
        """Test discovery uses explicit table list when provided."""
        settings = {
            "source_system": "duckdb",
            "tables": ["table1", "table2"],
            "schema": "main",
        }
        
        tables = await data_product_agent._discover_tables_for_inspection(
            mock_duckdb_manager,
            settings,
        )
        
        assert tables == ["table1", "table2"]
        mock_duckdb_manager.execute_query.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_discover_queries_duckdb_information_schema(self, data_product_agent, mock_duckdb_manager):
        """Test discovery queries DuckDB information_schema when no explicit tables."""
        mock_duckdb_manager.execute_query.return_value = {
            "columns": ["table_name"],
            "rows": [
                {"table_name": "customers"},
                {"table_name": "orders"},
            ],
        }
        
        settings = {
            "source_system": "duckdb",
            "schema": "main",
        }
        
        tables = await data_product_agent._discover_tables_for_inspection(
            mock_duckdb_manager,
            settings,
        )
        
        assert "customers" in tables
        assert "orders" in tables
        mock_duckdb_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discover_queries_bigquery_information_schema(self, data_product_agent, mock_bigquery_manager):
        """Test discovery queries BigQuery INFORMATION_SCHEMA when no explicit tables."""
        mock_bigquery_manager.execute_query.return_value = {
            "columns": ["table_name"],
            "rows": [
                {"table_name": "sales_view"},
                {"table_name": "revenue_view"},
            ],
        }
        
        settings = {
            "source_system": "bigquery",
            "project": "test-project",
            "schema": "test_dataset",
        }
        
        tables = await data_product_agent._discover_tables_for_inspection(
            mock_bigquery_manager,
            settings,
        )
        
        assert "sales_view" in tables
        assert "revenue_view" in tables
        mock_bigquery_manager.execute_query.assert_called_once()


class TestProfileTable:
    """Tests for _profile_table dispatcher and backend-specific profiling."""
    
    @pytest.mark.asyncio
    async def test_profile_table_dispatches_to_duckdb(self, data_product_agent, mock_duckdb_manager):
        """Test _profile_table dispatches to DuckDB profiling."""
        mock_duckdb_manager.execute_query.side_effect = [
            # PRAGMA table_info response
            {
                "columns": ["name", "type"],
                "rows": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "amount", "type": "DECIMAL"},
                ],
            },
            # COUNT(*) response
            {"columns": ["count"], "rows": [{"count": 100}]},
        ]
        
        settings = {
            "source_system": "duckdb",
            "include_samples": False,
            "inspection_depth": "standard",
        }
        
        profile = await data_product_agent._profile_table(
            mock_duckdb_manager,
            "test_table",
            settings,
        )
        
        assert profile is not None
        assert profile.name == "test_table"
        assert profile.row_count == 100
        assert len(profile.columns) == 2
    
    @pytest.mark.asyncio
    async def test_profile_table_dispatches_to_bigquery(self, data_product_agent, mock_bigquery_manager):
        """Test _profile_table dispatches to BigQuery profiling."""
        mock_bigquery_manager.execute_query.side_effect = [
            # INFORMATION_SCHEMA.COLUMNS response
            {
                "columns": ["column_name", "data_type"],
                "rows": [
                    {"column_name": "order_id", "data_type": "STRING"},
                    {"column_name": "revenue", "data_type": "FLOAT64"},
                ],
            },
            # COUNT(1) response
            {"columns": ["row_count"], "rows": [{"row_count": 500}]},
        ]
        
        settings = {
            "source_system": "bigquery",
            "project": "test-project",
            "schema": "test_dataset",
            "include_samples": False,
            "inspection_depth": "standard",
        }
        
        profile = await data_product_agent._profile_table(
            mock_bigquery_manager,
            "sales_view",
            settings,
        )
        
        assert profile is not None
        assert profile.name == "sales_view"
        assert profile.row_count == 500
        assert len(profile.columns) == 2


class TestInspectSourceSchemaEndToEnd:
    """End-to-end tests for inspect_source_schema workflow."""
    
    @pytest.mark.asyncio
    async def test_inspect_source_schema_duckdb_success(self, data_product_agent, mock_duckdb_manager):
        """Test successful DuckDB inspection workflow."""
        mock_duckdb_manager.execute_query.side_effect = [
            # Table discovery
            {"columns": ["table_name"], "rows": [{"table_name": "orders"}]},
            # PRAGMA table_info
            {
                "columns": ["name", "type"],
                "rows": [
                    {"name": "order_id", "type": "INTEGER"},
                    {"name": "amount", "type": "DECIMAL"},
                ],
            },
            # COUNT(*)
            {"columns": ["count"], "rows": [{"count": 250}]},
        ]
        
        request = DataProductSchemaInspectionRequest(
            request_id="test_inspect_001",
            principal_id="test_user",
            source_system="duckdb",
            schema="main",
        )
        
        response = await data_product_agent.inspect_source_schema(request)
        
        assert response.status == "success"
        assert len(response.tables) == 1
        assert response.tables[0].name == "orders"
        assert response.tables[0].row_count == 250
        assert response.inspection_metadata["source_system"] == "duckdb"
    
    @pytest.mark.asyncio
    async def test_inspect_source_schema_bigquery_success(self, data_product_agent, mock_bigquery_manager):
        """Test successful BigQuery inspection workflow."""
        mock_bigquery_manager.execute_query.side_effect = [
            # Table discovery
            {"columns": ["table_name"], "rows": [{"table_name": "revenue_view"}]},
            # INFORMATION_SCHEMA.COLUMNS
            {
                "columns": ["column_name", "data_type"],
                "rows": [
                    {"column_name": "product_id", "data_type": "STRING"},
                    {"column_name": "revenue", "data_type": "FLOAT64"},
                ],
            },
            # COUNT(1)
            {"columns": ["row_count"], "rows": [{"row_count": 1000}]},
        ]
        
        settings = {
            "source_system": "bigquery",
            "project": "test-project",
            "schema": "test_dataset",
            "connection_config": {
                "type": "bigquery",
                "project": "test-project",
                "dataset": "test_dataset",
            },
            "connection_params": {},
        }
        
        request = DataProductSchemaInspectionRequest(
            request_id="test_inspect_002",
            principal_id="test_user",
            source_system="bigquery",
            connection_overrides={"project": "test-project", "dataset": "test_dataset"},
        )
        
        with patch("src.database.manager_factory.DatabaseManagerFactory.create_manager", return_value=mock_bigquery_manager):
            response = await data_product_agent.inspect_source_schema(request)
            
            assert response.status == "success"
            assert len(response.tables) == 1
            assert response.tables[0].name == "revenue_view"
            assert response.tables[0].row_count == 1000
            assert response.inspection_metadata["source_system"] == "bigquery"
            mock_bigquery_manager.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_inspect_source_schema_connection_failure(self, data_product_agent, mock_bigquery_manager):
        """Test inspection handles connection failures gracefully."""
        mock_bigquery_manager.connect.side_effect = Exception("Connection failed")
        
        request = DataProductSchemaInspectionRequest(
            request_id="test_inspect_003",
            principal_id="test_user",
            source_system="bigquery",
            connection_overrides={"project": "invalid-project"},
        )
        
        with patch("src.database.manager_factory.DatabaseManagerFactory.create_manager", return_value=mock_bigquery_manager):
            response = await data_product_agent.inspect_source_schema(request)
            
            assert response.status == "error"
            assert len(response.blockers) > 0
            assert "Connection failed" in response.error_message
    
    @pytest.mark.asyncio
    async def test_inspect_source_schema_no_tables_discovered(self, data_product_agent, mock_duckdb_manager):
        """Test inspection handles empty table discovery gracefully."""
        mock_duckdb_manager.execute_query.return_value = {
            "columns": ["table_name"],
            "rows": [],
        }
        
        request = DataProductSchemaInspectionRequest(
            request_id="test_inspect_004",
            principal_id="test_user",
            source_system="duckdb",
            schema="empty_schema",
        )
        
        response = await data_product_agent.inspect_source_schema(request)
        
        assert response.status == "success"
        assert len(response.tables) == 0
        assert len(response.warnings) > 0
        assert any("No tables" in w for w in response.warnings)
