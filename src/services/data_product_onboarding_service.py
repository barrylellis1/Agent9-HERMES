"""
Data Product Onboarding Service - Standalone service for schema discovery and contract generation.

This service handles platform-adaptive schema discovery for Snowflake, Databricks, BigQuery, and
PostgreSQL. It extracts metadata from enterprise data platforms, infers relationships, and generates
contract YAML for data product registration.

Design:
- Separate from DPA Agent (which focuses on query execution)
- Platform-adaptive: uses INFORMATION_SCHEMA for metadata extraction where available
- QueryDialect-based: parses view SQL to infer base tables and relationships
- Registry-agnostic: generates contract data that can be published to any registry
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.database.manager_factory import DatabaseManagerFactory
from src.database.manager_interface import DatabaseManager
from src.database.dialects.snowflake_dialect import SnowflakeDialect
from src.database.dialects.databricks_dialect import DatabricksDialect
from src.database.dialects.base_dialect import SchemaContract, TableSchema, ColumnSchema


logger = logging.getLogger(__name__)


class OnboardingServiceRequest:
    """Metadata for onboarding request."""

    def __init__(
        self,
        connection_profile: str,
        source_system: str,
        tables: List[str],
        data_product_id: str,
        data_product_name: str,
        domain: str,
        description: str = "",
    ):
        self.connection_profile = connection_profile
        self.source_system = source_system
        self.tables = tables
        self.data_product_id = data_product_id
        self.data_product_name = data_product_name
        self.domain = domain
        self.description = description


class OnboardingServiceResponse:
    """Response from onboarding service."""

    def __init__(
        self,
        success: bool,
        data_product_id: str,
        source_system: str,
        tables: List[Dict[str, Any]],
        foreign_keys: List[Dict[str, Any]],
        kpi_proposals: List[Dict[str, Any]],
        contract_yaml: Optional[str] = None,
        errors: List[str] = None,
        warnings: List[str] = None,
    ):
        self.success = success
        self.data_product_id = data_product_id
        self.source_system = source_system
        self.tables = tables
        self.foreign_keys = foreign_keys
        self.kpi_proposals = kpi_proposals
        self.contract_yaml = contract_yaml
        self.errors = errors or []
        self.warnings = warnings or []


class DataProductOnboardingService:
    """
    Service for discovering, analyzing, and onboarding data products from enterprise platforms.

    Platform Support:
    - Snowflake: Uses INFORMATION_SCHEMA + SHOW commands for FK extraction
    - Databricks: Uses INFORMATION_SCHEMA + catalog metadata
    - BigQuery: Uses INFORMATION_SCHEMA.KEY_COLUMN_USAGE (future)
    - PostgreSQL: Uses information_schema (future)

    Lifecycle:
    1. discover_tables() → List available tables/views
    2. profile_table() → Extract columns, types, constraints
    3. extract_foreign_keys() → FK relationships from metadata or view SQL
    4. infer_semantic_tags() → Classify columns (measure/dimension/time/identifier)
    5. generate_contract() → Contract YAML for registration
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.manager: Optional[DatabaseManager] = None
        self.source_system: Optional[str] = None
        self.dialect: Optional[Any] = None  # QueryDialect instance
        self.connection_config: Dict[str, Any] = {}

    async def connect(
        self,
        connection_config: Dict[str, Any],
        source_system: str,
        connection_params: Dict[str, Any],
    ) -> bool:
        """
        Connect to a data platform using configuration and credentials.

        Args:
            connection_config: Connection profile configuration
            source_system: 'snowflake', 'databricks', 'bigquery', 'postgres'
            connection_params: Runtime credentials (user, password, token, etc.)

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection_config = connection_config
            self.source_system = source_system.lower()

            # Create appropriate manager via factory
            self.manager = DatabaseManagerFactory.create_manager(
                self.source_system, connection_config, self.logger
            )

            # Connect with credentials
            if not await self.manager.connect(connection_params):
                self.logger.error(f"Failed to connect to {source_system}")
                return False

            # Initialize dialect for SQL parsing
            if self.source_system == "snowflake":
                self.dialect = SnowflakeDialect(self.logger)
            elif self.source_system == "databricks":
                self.dialect = DatabricksDialect(self.logger)
            # Other platforms use platform-specific metadata queries (dialect not needed)

            self.logger.info(f"Connected to {source_system} for onboarding")
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close database connection."""
        if self.manager:
            return await self.manager.disconnect()
        return True

    async def discover_tables(
        self, schema: Optional[str] = None, view_only: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        Discover available tables/views in the connected database.

        Args:
            schema: Optional schema to filter (None = all accessible)
            view_only: If True, return only views (curated); if False, return all

        Returns:
            Tuple of (table_list, warnings)
        """
        if not self.manager:
            return [], ["Not connected"]

        try:
            tables = await self.manager.list_views()
            warnings = []

            if not tables:
                warnings.append("No tables/views discovered in schema")

            self.logger.info(f"Discovered {len(tables)} tables/views")
            return tables, warnings
        except Exception as e:
            self.logger.error(f"Discovery error: {e}")
            return [], [str(e)]

    async def profile_table(
        self, table_name: str
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Extract metadata (columns, types, constraints) from a table/view.

        Returns:
            Tuple of (profile_dict, warnings)

        Profile structure:
        {
            'name': str,
            'row_count': int,
            'type': 'TABLE' | 'VIEW',
            'columns': [
                {'name': str, 'type': str, 'nullable': bool, 'semantic_tags': []}
            ],
            'primary_keys': [str],
            'view_definition': str (if VIEW)
        }
        """
        if not self.manager:
            return None, ["Not connected"]

        try:
            warnings = []
            profile = {
                "name": table_name,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
            }

            # Query INFORMATION_SCHEMA.COLUMNS for column metadata
            col_query = self._build_column_query(table_name)
            if col_query:
                try:
                    df = await self.manager.execute_query(col_query)
                    for _, row in df.iterrows():
                        col = {
                            "name": row.get("column_name", row.get("COLUMN_NAME")),
                            "type": row.get("data_type", row.get("DATA_TYPE")),
                            "nullable": row.get("is_nullable", row.get("IS_NULLABLE")) != "NO",
                            "semantic_tags": [],
                        }
                        profile["columns"].append(col)
                except Exception as e:
                    warnings.append(f"Failed to profile columns: {e}")

            self.logger.info(f"Profiled {table_name}: {len(profile['columns'])} columns")
            return profile, warnings
        except Exception as e:
            self.logger.error(f"Profile error for {table_name}: {e}")
            return None, [str(e)]

    async def extract_foreign_keys(
        self, table_name: str
    ) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Extract foreign key relationships for a table from metadata catalogs.

        For Snowflake/Databricks, queries INFORMATION_SCHEMA.KEY_COLUMN_USAGE.
        For DuckDB, infers via naming conventions (future).

        Returns:
            Tuple of (fk_list, warnings)

        FK structure:
        [
            {
                'source_table': str,
                'source_column': str,
                'target_table': str,
                'target_column': str,
                'confidence': float (1.0 = catalog, <1.0 = inferred)
            }
        ]
        """
        if not self.manager:
            return [], ["Not connected"]

        try:
            fks = []
            warnings = []

            if self.source_system in ("snowflake", "databricks"):
                # Query INFORMATION_SCHEMA for FK relationships
                fk_query = self._build_fk_query(table_name)
                if fk_query:
                    try:
                        df = await self.manager.execute_query(fk_query)
                        for _, row in df.iterrows():
                            # Handle both lowercase and uppercase column names
                            src_col = row.get("column_name") or row.get("COLUMN_NAME")
                            tgt_tbl = row.get("referenced_table_name") or row.get("REFERENCED_TABLE_NAME")
                            tgt_col = row.get("referenced_column_name") or row.get("REFERENCED_COLUMN_NAME")

                            fk = {
                                "source_table": table_name,
                                "source_column": src_col,
                                "target_table": tgt_tbl,
                                "target_column": tgt_col,
                                "confidence": 1.0,
                            }
                            fks.append(fk)
                    except Exception as e:
                        warnings.append(f"Failed to extract FKs from metadata: {e}")

            if not fks:
                warnings.append(f"No foreign keys found for {table_name}")

            return fks, warnings
        except Exception as e:
            self.logger.error(f"FK extraction error: {e}")
            return [], [str(e)]

    async def parse_view_definition(
        self, view_name: str, view_sql: str
    ) -> Tuple[Optional[SchemaContract], List[str]]:
        """
        Parse view SQL definition to extract schema contract.

        Uses QueryDialect to extract base tables, column mappings, FK inference.

        Returns:
            Tuple of (SchemaContract, warnings)
        """
        if not self.dialect:
            return None, ["Dialect not initialized"]

        try:
            contract = await self.dialect.extract_schema_contract(view_name, view_sql)
            warnings = []

            if contract.parse_confidence < 0.75:
                warnings.append(
                    f"Low confidence ({contract.parse_confidence}) parsing view SQL. "
                    "Manual review recommended."
                )

            if contract.notes:
                warnings.append(f"Parsing notes: {contract.notes}")

            return contract, warnings
        except Exception as e:
            self.logger.error(f"View parsing error: {e}")
            return None, [str(e)]

    def infer_semantic_tags(self, columns: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Infer semantic tags for columns based on naming conventions and types.

        Tags:
        - 'measure': Numeric columns (sum, count, total, amount, value, etc.)
        - 'dimension': Categorical columns (names, codes, categories)
        - 'time': Date/timestamp columns (date, time, month, year)
        - 'identifier': ID columns (ends with _id, _key, or named 'id')

        Returns:
            Dict mapping column name → List[tags]
        """
        tags = {}

        for col in columns:
            col_name = col.get("name", "").lower()
            col_type = col.get("type", "").upper()
            col_tags = []

            # Identifier check
            if col_name.endswith(("_id", "_key")) or col_name == "id":
                col_tags.append("identifier")

            # Type-based inference
            if any(x in col_type for x in ("INT", "FLOAT", "DECIMAL", "DOUBLE", "NUMBER")):
                # Numeric column - check naming
                if any(x in col_name for x in ("amount", "value", "count", "total", "sum", "revenue")):
                    col_tags.append("measure")
                else:
                    col_tags.append("dimension")
            elif any(x in col_type for x in ("DATE", "TIME", "TIMESTAMP")):
                col_tags.append("time")
            elif any(x in col_type for x in ("STRING", "VARCHAR", "TEXT", "CHAR")):
                # Text column - check naming
                if any(x in col_name for x in ("date", "time", "month", "year")):
                    col_tags.append("time")
                else:
                    col_tags.append("dimension")
            else:
                col_tags.append("dimension")  # Default

            tags[col.get("name", "")] = col_tags

        return tags

    def _build_column_query(self, table_name: str) -> Optional[str]:
        """Build platform-specific INFORMATION_SCHEMA query for columns."""
        if self.source_system == "snowflake":
            return f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name.upper()}'
            ORDER BY ordinal_position
            """
        elif self.source_system == "databricks":
            return f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """
        return None

    def _build_fk_query(self, table_name: str) -> Optional[str]:
        """Build platform-specific INFORMATION_SCHEMA query for foreign keys."""
        if self.source_system == "snowflake":
            return f"""
            SELECT
                kcu.column_name,
                kcu.referenced_table_name,
                kcu.referenced_column_name
            FROM information_schema.key_column_usage kcu
            WHERE table_name = '{table_name.upper()}'
              AND referenced_table_name IS NOT NULL
            """
        elif self.source_system == "databricks":
            return f"""
            SELECT
                column_name,
                referenced_table_name,
                referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name = '{table_name}'
              AND referenced_table_name IS NOT NULL
            """
        return None

    def generate_contract(
        self,
        data_product_id: str,
        data_product_name: str,
        domain: str,
        tables: List[Dict[str, Any]],
        kpi_proposals: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate contract YAML for a data product.

        Contract structure:
        ```yaml
        data_product:
          id: dp_...
          name: ...
          domain: ...
          source_system: snowflake | databricks | ...

        tables:
          - name: ...
            role: FACT | DIMENSION
            primary_keys: [...]
            foreign_keys: [...]
            columns: [...]

        kpis:
          - name: ...
            expression: ...
            grain: ...
        ```
        """
        contract_lines = [
            "data_product:",
            f"  id: {data_product_id}",
            f"  name: {data_product_name}",
            f"  domain: {domain}",
            f"  source_system: {self.source_system}",
            f"  created_at: {datetime.utcnow().isoformat()}",
            "",
            "tables:",
        ]

        for table in tables:
            contract_lines.append(f"  - name: {table.get('name', 'unknown')}")
            contract_lines.append(f"    role: {table.get('role', 'TABLE')}")

            # Primary keys
            pks = table.get("primary_keys", [])
            if pks:
                contract_lines.append(f"    primary_keys: {pks}")

            # Columns
            if table.get("columns"):
                contract_lines.append("    columns:")
                for col in table["columns"]:
                    contract_lines.append(f"      - name: {col.get('name', 'unknown')}")
                    contract_lines.append(f"        data_type: {col.get('type', 'STRING')}")
                    tags = col.get("semantic_tags", [])
                    if tags:
                        contract_lines.append(f"        semantic_tags: {tags}")

            # Foreign keys
            fks = table.get("foreign_keys", [])
            if fks:
                contract_lines.append("    foreign_keys:")
                for fk in fks:
                    contract_lines.append(f"      - source_column: {fk.get('source_column')}")
                    contract_lines.append(f"        target_table: {fk.get('target_table')}")
                    contract_lines.append(f"        target_column: {fk.get('target_column')}")

            contract_lines.append("")

        # KPI proposals
        if kpi_proposals:
            contract_lines.append("kpis:")
            for kpi in kpi_proposals:
                contract_lines.append(f"  - name: {kpi.get('name', 'unknown')}")
                contract_lines.append(f"    expression: {kpi.get('expression', '')}")
                if kpi.get("grain"):
                    contract_lines.append(f"    grain: {kpi['grain']}")
                if kpi.get("confidence"):
                    contract_lines.append(f"    confidence: {kpi['confidence']}")
            contract_lines.append("")

        return "\n".join(contract_lines)
