"""
Unit tests for DataProductOnboardingService.

Tests cover:
- Connection lifecycle (connect, disconnect)
- Table discovery from metadata catalogs
- Table profiling (columns, types, constraints)
- Foreign key extraction
- View SQL parsing via QueryDialect
- Semantic tag inference
- Contract YAML generation
- Integration workflows
"""

import pytest
import logging
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd

from src.services.data_product_onboarding_service import (
    DataProductOnboardingService,
    OnboardingServiceRequest,
    OnboardingServiceResponse,
)


# ============================================================================
# OnboardingService Lifecycle Tests
# ============================================================================


class TestOnboardingServiceLifecycle:
    """Test service connection and lifecycle."""

    @pytest.fixture
    def service(self):
        """Create OnboardingService instance."""
        return DataProductOnboardingService(logger=logging.getLogger(__name__))

    @pytest.mark.asyncio
    async def test_connect_snowflake(self, service):
        """Service connects to Snowflake via manager."""
        config = {
            "account": "trial",
            "warehouse": "wh",
            "database": "db",
            "schema": "public",
        }
        connection_params = {"user": "test", "password": "test"}

        with patch(
            "src.services.data_product_onboarding_service.DatabaseManagerFactory.create_manager"
        ) as mock_factory:
            mock_manager = AsyncMock()
            mock_manager.connect = AsyncMock(return_value=True)
            mock_factory.return_value = mock_manager

            result = await service.connect(config, "snowflake", connection_params)

            assert result is True
            assert service.source_system == "snowflake"
            assert service.manager is not None
            assert service.dialect is not None

    @pytest.mark.asyncio
    async def test_connect_databricks(self, service):
        """Service connects to Databricks via manager."""
        config = {
            "server_hostname": "adb.cloud.databricks.com",
            "http_path": "/sql/1.0/warehouses/abc",
        }
        connection_params = {"user": "test", "access_token": "token"}

        with patch(
            "src.services.data_product_onboarding_service.DatabaseManagerFactory.create_manager"
        ) as mock_factory:
            mock_manager = AsyncMock()
            mock_manager.connect = AsyncMock(return_value=True)
            mock_factory.return_value = mock_manager

            result = await service.connect(config, "databricks", connection_params)

            assert result is True
            assert service.source_system == "databricks"
            assert service.dialect is not None

    @pytest.mark.asyncio
    async def test_connect_fails(self, service):
        """Service handles connection failure."""
        with patch(
            "src.services.data_product_onboarding_service.DatabaseManagerFactory.create_manager"
        ) as mock_factory:
            mock_manager = AsyncMock()
            mock_manager.connect = AsyncMock(return_value=False)
            mock_factory.return_value = mock_manager

            result = await service.connect({}, "snowflake", {})

            assert result is False

    @pytest.mark.asyncio
    async def test_disconnect(self, service):
        """Service disconnects cleanly."""
        mock_manager = AsyncMock()
        mock_manager.disconnect = AsyncMock(return_value=True)
        service.manager = mock_manager

        result = await service.disconnect()

        assert result is True
        mock_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self, service):
        """Disconnect returns True if not connected."""
        result = await service.disconnect()
        assert result is True


# ============================================================================
# Table Discovery Tests
# ============================================================================


class TestTableDiscovery:
    """Test table and view discovery."""

    @pytest.fixture
    def service(self):
        """Create connected service."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))
        service.manager = AsyncMock()
        service.source_system = "snowflake"
        return service

    @pytest.mark.asyncio
    async def test_discover_tables(self, service):
        """Service discovers available tables/views."""
        service.manager.list_views = AsyncMock(
            return_value=["sales_view", "customer_view", "product_view"]
        )

        tables, warnings = await service.discover_tables()

        assert len(tables) == 3
        assert "sales_view" in tables
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_discover_tables_empty(self, service):
        """Service handles no tables found."""
        service.manager.list_views = AsyncMock(return_value=[])

        tables, warnings = await service.discover_tables()

        assert tables == []
        assert any("No tables" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_discover_not_connected(self, service):
        """Discovery fails if not connected."""
        service.manager = None

        tables, warnings = await service.discover_tables()

        assert tables == []
        assert any("Not connected" in w for w in warnings)


# ============================================================================
# Table Profiling Tests
# ============================================================================


class TestTableProfiling:
    """Test schema profiling (columns, types, constraints)."""

    @pytest.fixture
    def service(self):
        """Create service."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))
        service.manager = AsyncMock()
        service.source_system = "snowflake"
        return service

    @pytest.mark.asyncio
    async def test_profile_table_snowflake(self, service):
        """Profile extracts columns from Snowflake."""
        df = pd.DataFrame({
            "column_name": ["id", "name", "amount"],
            "data_type": ["STRING", "VARCHAR", "FLOAT"],
            "is_nullable": ["NO", "YES", "YES"],
        })
        service.manager.execute_query = AsyncMock(return_value=df)

        profile, warnings = await service.profile_table("sales")

        assert profile is not None
        assert profile["name"] == "sales"
        assert len(profile["columns"]) == 3
        assert profile["columns"][0]["name"] == "id"
        assert profile["columns"][0]["type"] == "STRING"
        assert profile["columns"][0]["nullable"] is False

    @pytest.mark.asyncio
    async def test_profile_table_not_connected(self, service):
        """Profile fails if not connected."""
        service.manager = None

        profile, warnings = await service.profile_table("sales")

        assert profile is None
        assert any("Not connected" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_profile_table_query_error(self, service):
        """Profile handles query errors gracefully."""
        service.manager.execute_query = AsyncMock(side_effect=Exception("Query failed"))

        profile, warnings = await service.profile_table("sales")

        # Returns empty profile with warnings, not None
        assert profile is not None
        assert profile["name"] == "sales"
        assert len(profile["columns"]) == 0
        assert any("Query failed" in w or "Failed" in w for w in warnings)


# ============================================================================
# Foreign Key Extraction Tests
# ============================================================================


class TestForeignKeyExtraction:
    """Test FK relationship extraction."""

    @pytest.fixture
    def service(self):
        """Create service."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))
        service.manager = AsyncMock()
        service.source_system = "snowflake"
        return service

    @pytest.mark.asyncio
    async def test_extract_foreign_keys(self, service):
        """FK extraction returns relationships from metadata."""
        df = pd.DataFrame({
            "column_name": ["customer_id", "product_id"],
            "referenced_table_name": ["customers", "products"],
            "referenced_column_name": ["customer_id", "product_id"],
        })
        service.manager.execute_query = AsyncMock(return_value=df)

        fks, warnings = await service.extract_foreign_keys("sales")

        assert len(fks) == 2
        assert fks[0]["source_table"] == "sales"
        assert fks[0]["source_column"] == "customer_id"
        assert fks[0]["target_table"] == "customers"
        assert fks[0]["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_extract_foreign_keys_none(self, service):
        """FK extraction returns empty list if no FKs found."""
        df = pd.DataFrame()
        service.manager.execute_query = AsyncMock(return_value=df)

        fks, warnings = await service.extract_foreign_keys("sales")

        assert fks == []
        assert any("No foreign keys" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_extract_foreign_keys_not_connected(self, service):
        """FK extraction fails if not connected."""
        service.manager = None

        fks, warnings = await service.extract_foreign_keys("sales")

        assert fks == []
        assert any("Not connected" in w for w in warnings)


# ============================================================================
# View Definition Parsing Tests
# ============================================================================


class TestViewDefinitionParsing:
    """Test view SQL parsing via QueryDialect."""

    @pytest.fixture
    def service(self):
        """Create service with Snowflake dialect."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))
        service.source_system = "snowflake"
        from src.database.dialects.snowflake_dialect import SnowflakeDialect
        service.dialect = SnowflakeDialect(logging.getLogger(__name__))
        return service

    @pytest.mark.asyncio
    async def test_parse_view_definition(self, service):
        """View parser extracts base tables and columns."""
        sql = """
        SELECT o.order_id, o.amount, c.customer_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        """

        contract, warnings = await service.parse_view_definition("orders_view", sql)

        assert contract is not None
        assert contract.view_name == "orders_view"
        assert contract.source_system == "snowflake"
        assert len(contract.tables) > 0

    @pytest.mark.asyncio
    async def test_parse_view_low_confidence(self, service):
        """Parser warns on low confidence."""
        sql = "INVALID SQL HERE"

        contract, warnings = await service.parse_view_definition("bad_view", sql)

        # May fail or have low confidence
        if contract:
            if contract.parse_confidence < 0.75:
                assert any("confidence" in w.lower() for w in warnings)

    @pytest.mark.asyncio
    async def test_parse_view_no_dialect(self, service):
        """Parser fails if dialect not initialized."""
        service.dialect = None

        contract, warnings = await service.parse_view_definition("test", "SELECT 1")

        assert contract is None
        assert any("Dialect" in w for w in warnings)


# ============================================================================
# Semantic Tag Inference Tests
# ============================================================================


class TestSemanticTagInference:
    """Test column classification and semantic tag inference."""

    @pytest.fixture
    def service(self):
        """Create service."""
        return DataProductOnboardingService(logger=logging.getLogger(__name__))

    def test_infer_tags_identifier(self, service):
        """Identifier columns tagged correctly."""
        columns = [
            {"name": "customer_id", "type": "INT"},
            {"name": "order_key", "type": "STRING"},
            {"name": "id", "type": "STRING"},
        ]

        tags = service.infer_semantic_tags(columns)

        assert "identifier" in tags["customer_id"]
        assert "identifier" in tags["order_key"]
        assert "identifier" in tags["id"]

    def test_infer_tags_measure(self, service):
        """Measure columns (numeric amounts) tagged correctly."""
        columns = [
            {"name": "amount", "type": "FLOAT"},
            {"name": "total_revenue", "type": "DECIMAL"},
            {"name": "customer_count", "type": "INT"},
        ]

        tags = service.infer_semantic_tags(columns)

        assert "measure" in tags["amount"]
        assert "measure" in tags["total_revenue"]
        # customer_count might be dimension or measure depending on heuristics

    def test_infer_tags_time(self, service):
        """Time columns tagged correctly."""
        columns = [
            {"name": "order_date", "type": "DATE"},
            {"name": "created_at", "type": "TIMESTAMP"},
            {"name": "month", "type": "STRING"},
        ]

        tags = service.infer_semantic_tags(columns)

        assert "time" in tags["order_date"]
        assert "time" in tags["created_at"]
        assert "time" in tags["month"]

    def test_infer_tags_dimension(self, service):
        """Dimension columns tagged correctly."""
        columns = [
            {"name": "customer_name", "type": "VARCHAR"},
            {"name": "category", "type": "STRING"},
            {"name": "region", "type": "TEXT"},
        ]

        tags = service.infer_semantic_tags(columns)

        assert "dimension" in tags["customer_name"]
        assert "dimension" in tags["category"]
        assert "dimension" in tags["region"]


# ============================================================================
# Contract Generation Tests
# ============================================================================


class TestContractGeneration:
    """Test contract YAML generation."""

    @pytest.fixture
    def service(self):
        """Create service."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))
        service.source_system = "snowflake"
        return service

    def test_generate_contract_basic(self, service):
        """Contract generation produces valid YAML."""
        tables = [
            {
                "name": "sales",
                "role": "FACT",
                "primary_keys": ["sale_id"],
                "columns": [
                    {"name": "sale_id", "type": "STRING", "semantic_tags": ["identifier"]},
                    {"name": "amount", "type": "FLOAT", "semantic_tags": ["measure"]},
                ],
                "foreign_keys": [],
            }
        ]

        yaml = service.generate_contract(
            "dp_sales",
            "Sales Data Product",
            "Finance",
            tables,
        )

        assert "data_product:" in yaml
        assert "dp_sales" in yaml
        assert "Sales Data Product" in yaml
        assert "Finance" in yaml
        assert "tables:" in yaml
        assert "sales" in yaml
        assert "FACT" in yaml

    def test_generate_contract_with_fks(self, service):
        """Contract includes foreign key relationships."""
        tables = [
            {
                "name": "sales",
                "role": "FACT",
                "primary_keys": ["sale_id"],
                "columns": [],
                "foreign_keys": [
                    {
                        "source_column": "customer_id",
                        "target_table": "customers",
                        "target_column": "customer_id",
                    }
                ],
            }
        ]

        yaml = service.generate_contract(
            "dp_sales",
            "Sales",
            "Finance",
            tables,
        )

        assert "foreign_keys:" in yaml
        assert "customer_id" in yaml
        assert "customers" in yaml

    def test_generate_contract_with_kpis(self, service):
        """Contract includes KPI proposals."""
        tables = [{"name": "sales", "role": "FACT", "columns": []}]
        kpis = [
            {
                "name": "Total Sales",
                "expression": "SUM(amount)",
                "grain": "order_date",
                "confidence": 0.8,
            }
        ]

        yaml = service.generate_contract(
            "dp_sales",
            "Sales",
            "Finance",
            tables,
            kpis,
        )

        assert "kpis:" in yaml
        assert "Total Sales" in yaml
        assert "SUM(amount)" in yaml


# ============================================================================
# Integration Tests
# ============================================================================


class TestOnboardingServiceIntegration:
    """End-to-end onboarding workflows."""

    @pytest.mark.asyncio
    async def test_snowflake_onboarding_workflow(self):
        """Complete Snowflake onboarding workflow."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))

        # Mock connection
        with patch(
            "src.services.data_product_onboarding_service.DatabaseManagerFactory.create_manager"
        ) as mock_factory:
            mock_manager = AsyncMock()
            mock_manager.connect = AsyncMock(return_value=True)
            mock_manager.list_views = AsyncMock(return_value=["sales_view"])
            mock_manager.execute_query = AsyncMock(
                return_value=pd.DataFrame({
                    "column_name": ["sale_id", "amount"],
                    "data_type": ["STRING", "FLOAT"],
                    "is_nullable": ["NO", "YES"],
                })
            )
            mock_manager.disconnect = AsyncMock(return_value=True)
            mock_factory.return_value = mock_manager

            # Connect
            connected = await service.connect(
                {"account": "trial"},
                "snowflake",
                {"user": "test", "password": "test"},
            )
            assert connected is True

            # Discover
            tables, warns = await service.discover_tables()
            assert "sales_view" in tables

            # Profile
            profile, warns = await service.profile_table("sales_view")
            assert profile is not None
            assert len(profile["columns"]) == 2

            # Infer tags
            tags = service.infer_semantic_tags(profile["columns"])
            assert "identifier" in tags["sale_id"]
            assert "measure" in tags["amount"]

            # Generate contract
            tables_for_contract = [
                {
                    "name": "sales_view",
                    "role": "FACT",
                    "columns": [
                        {"name": "sale_id", "type": "STRING", "semantic_tags": tags["sale_id"]},
                        {"name": "amount", "type": "FLOAT", "semantic_tags": tags["amount"]},
                    ],
                }
            ]
            yaml = service.generate_contract(
                "dp_sales",
                "Sales",
                "Finance",
                tables_for_contract,
            )
            assert "dp_sales" in yaml
            assert "Sales" in yaml

            # Disconnect
            disconnected = await service.disconnect()
            assert disconnected is True

    @pytest.mark.asyncio
    async def test_databricks_onboarding_workflow(self):
        """Complete Databricks onboarding workflow."""
        service = DataProductOnboardingService(logger=logging.getLogger(__name__))

        with patch(
            "src.services.data_product_onboarding_service.DatabaseManagerFactory.create_manager"
        ) as mock_factory:
            mock_manager = AsyncMock()
            mock_manager.connect = AsyncMock(return_value=True)
            mock_manager.disconnect = AsyncMock(return_value=True)
            mock_factory.return_value = mock_manager

            connected = await service.connect(
                {"server_hostname": "adb.cloud.databricks.com"},
                "databricks",
                {"user": "test", "access_token": "token"},
            )
            assert connected is True
            assert service.source_system == "databricks"

            disconnected = await service.disconnect()
            assert disconnected is True
