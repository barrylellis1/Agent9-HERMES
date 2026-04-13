"""
Base QueryDialect class - schema contract abstraction for multi-warehouse support.

QueryDialect extracts complete schema metadata from customer view definitions.
This metadata becomes the schema contract that flows through:
- Data Product Onboarding (extraction)
- Contract YAML (storage)
- DPA query generation (schema-aware SQL)
- MCP interface (Phase 10D)

No SQL translation — purely schema understanding.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging


@dataclass
class ColumnSchema:
    """Schema definition for a single column."""

    name: str
    data_type: str  # Snowflake/Databricks type (STRING, NUMBER, TIMESTAMP, etc.)
    is_nullable: bool = True
    is_primary_key: bool = False
    is_measure: bool = False  # Numeric column suitable for aggregation
    is_dimension: bool = False  # Categorical column suitable for grouping
    is_time: bool = False  # Date/timestamp column
    description: Optional[str] = None
    source_column: Optional[str] = None  # If derived, where it comes from


@dataclass
class TableSchema:
    """Schema definition for a table or view."""

    name: str
    table_type: str  # "TABLE" or "VIEW"
    role: Optional[str] = None  # "FACT", "DIMENSION", "BRIDGE"
    columns: List[ColumnSchema] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    row_count: Optional[int] = None
    description: Optional[str] = None


@dataclass
class ForeignKeySchema:
    """Schema definition for a foreign key relationship."""

    source_table: str
    source_column: str
    target_table: str
    target_column: str
    is_inferred: bool = False  # True if inferred from SQL, False if from INFORMATION_SCHEMA


@dataclass
class SchemaContract:
    """
    Complete schema contract extracted from a customer view.

    This contract is:
    1. Extracted during Data Product Onboarding (via QueryDialect)
    2. Stored in Contract YAML (source of truth)
    3. Used by DPA for schema-aware query generation
    4. Exposed as MCP interface (Phase 10D)
    """

    view_name: str
    source_system: str  # "snowflake", "databricks"
    native_sql: str  # Customer's original view SQL (never translated)

    # Schema metadata
    tables: List[TableSchema] = field(default_factory=list)  # Base tables + view
    foreign_keys: List[ForeignKeySchema] = field(default_factory=list)
    column_mappings: Dict[str, str] = field(default_factory=dict)  # derived -> source

    # Quality metrics
    parse_confidence: float = 0.0  # 0.0-1.0 confidence in extracted schema
    notes: Optional[str] = None

    def get_columns(self) -> List[ColumnSchema]:
        """Get all columns from the view (flattened)."""
        columns = []
        for table in self.tables:
            columns.extend(table.columns)
        return columns

    def get_measures(self) -> List[str]:
        """Get all measure column names."""
        return [col.name for col in self.get_columns() if col.is_measure]

    def get_dimensions(self) -> List[str]:
        """Get all dimension column names."""
        return [col.name for col in self.get_columns() if col.is_dimension]


class QueryDialect(ABC):
    """
    Base class for SQL dialect schema extractors.

    Each dialect (Snowflake, Databricks, etc.) implements platform-specific
    logic to extract complete schema contracts from view definitions.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    @abstractmethod
    async def extract_schema_contract(self, view_name: str, view_sql: str) -> SchemaContract:
        """
        Extract complete schema contract from a view definition.

        Args:
            view_name: Name of the view
            view_sql: View definition SQL

        Returns:
            SchemaContract with complete schema metadata
        """
        pass

    async def extract_and_enhance(
        self, view_name: str, view_sql: str, column_stats: Optional[Dict[str, Any]] = None
    ) -> SchemaContract:
        """
        Extract schema contract and enhance with statistics.

        Args:
            view_name: Name of the view
            view_sql: View definition SQL
            column_stats: Optional column statistics for role inference

        Returns:
            SchemaContract with enhanced metadata
        """
        contract = await self.extract_schema_contract(view_name, view_sql)

        # Enhance with column statistics if provided
        if column_stats:
            try:
                # Infer which columns are measures vs dimensions
                for col in contract.get_columns():
                    if col.data_type in ["NUMBER", "FLOAT", "DOUBLE", "INT", "INTEGER", "BIGINT"]:
                        col.is_measure = True
                    elif col.data_type in ["VARCHAR", "STRING", "TEXT"]:
                        col.is_dimension = True
                    elif col.data_type in ["TIMESTAMP", "DATE"]:
                        col.is_time = True
            except Exception as e:
                self.logger.warning(f"Could not enhance schema: {e}")

        return contract
