"""
Databricks SQL dialect - extracts SchemaContract from Databricks view definitions.

Uses regex + lightweight tokenization (not a full AST parser) to extract:
- Base tables and column schemas
- Foreign key relationships (inferred from JOIN conditions)
- Column mappings (derived → source)
- Semantic roles (FACT, DIMENSION)
"""

import re
import logging
from typing import Any, Dict, List, Optional

from src.database.dialects.base_dialect import (
    QueryDialect,
    SchemaContract,
    TableSchema,
    ColumnSchema,
    ForeignKeySchema,
)


class DatabricksDialect(QueryDialect):
    """Schema contract extractor for Databricks/Spark SQL dialect."""

    async def extract_schema_contract(self, view_name: str, view_sql: str) -> SchemaContract:
        """
        Extract complete schema contract from Databricks view definition.

        Returns SchemaContract with:
        - Base tables and column schemas
        - Foreign key relationships
        - Column lineage
        - Semantic roles

        Handles Databricks-specific SQL syntax (three-level naming, Delta tables, etc.).
        """
        contract = SchemaContract(
            view_name=view_name,
            source_system="databricks",
            native_sql=view_sql,
            parse_confidence=0.75,  # Regex-based, not 100% accurate
        )

        try:
            normalized = " ".join(view_sql.split())

            # Extract base tables (handle catalog.schema.table naming)
            base_tables = self._extract_tables(normalized)
            contract.tables = [
                TableSchema(name=table, table_type="TABLE") for table in base_tables
            ]

            # Add the view itself
            view_table = TableSchema(name=view_name, table_type="VIEW", role="VIEW")
            contract.tables.insert(0, view_table)

            # Extract column references from SELECT list
            columns = self._extract_columns(normalized)
            if contract.tables:
                contract.tables[0].columns = columns

            # Infer foreign keys from JOIN conditions
            fks = self._extract_foreign_keys(normalized, base_tables)
            contract.foreign_keys = fks

            # Extract column mappings
            contract.column_mappings = self._extract_column_mappings(normalized)

            # Infer table role
            if len(base_tables) > 1:
                contract.tables[0].role = "FACT"
            elif len(base_tables) == 1:
                contract.tables[0].role = "DIMENSION"

            return contract
        except Exception as e:
            self.logger.warning(f"Databricks schema extraction error: {e}")
            contract.parse_confidence = 0.1
            contract.notes = str(e)
            return contract

    def _extract_tables(self, normalized_sql: str) -> List[str]:
        """
        Extract table names from FROM and JOIN clauses.

        Handles Databricks three-level naming: catalog.schema.table
        """
        tables = []

        # FROM clause: FROM [catalog.][schema.]table [alias]
        # Pattern: optional schema refs (word.word.word or word.word), optional alias
        from_pattern = r"FROM\s+(?:[\w]+\.)?(?:[\w]+\.)?(?:`)?(\w+)(?:`)?(?:\s+(?:AS\s+)?(\w+))?"
        for match in re.finditer(from_pattern, normalized_sql, re.IGNORECASE):
            table_name = match.group(1)
            if table_name.upper() not in ["VALUES"]:
                tables.append(table_name)

        # JOIN clause: [INNER|LEFT|RIGHT|FULL] JOIN [catalog.][schema.]table [alias]
        join_pattern = r"(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\s+(?:[\w]+\.)?(?:[\w]+\.)?(?:`)?(\w+)(?:`)?"
        for match in re.finditer(join_pattern, normalized_sql, re.IGNORECASE):
            table_name = match.group(1)
            if table_name not in tables:
                tables.append(table_name)

        return tables

    def _extract_columns(self, normalized_sql: str) -> List[ColumnSchema]:
        """Extract column definitions from SELECT list."""
        columns = []

        # SELECT [...] FROM pattern
        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(select_pattern, normalized_sql, re.IGNORECASE | re.DOTALL)
        if not match:
            return columns

        select_list = match.group(1)

        # Parse each column: col_ref [AS alias]
        col_pattern = r"([\w\.]+)\s+(?:AS\s+)?(?:`)?(\w+)(?:`)?"
        for col_match in re.finditer(col_pattern, select_list):
            source = col_match.group(1)
            alias = col_match.group(2) or source.split(".")[-1]

            # Determine data type (simplified heuristic)
            col_type = self._infer_column_type(source)

            col_schema = ColumnSchema(
                name=alias,
                data_type=col_type,
                source_column=source,
            )
            columns.append(col_schema)

        return columns

    def _extract_foreign_keys(
        self, normalized_sql: str, base_tables: List[str]
    ) -> List[ForeignKeySchema]:
        """Extract foreign key relationships from JOIN ON conditions."""
        fks = []

        # ON condition: table1.col1 = table2.col2
        # Handle backticks and optional schema/catalog references
        on_pattern = r"ON\s+(?:[\w]+\.)?(?:`)?(\w+)(?:`)?\.(?:`)?(\w+)(?:`)?\s*=\s*(?:[\w]+\.)?(?:`)?(\w+)(?:`)?\.(?:`)?(\w+)(?:`)?"
        for match in re.finditer(on_pattern, normalized_sql):
            left_table = match.group(1)
            left_col = match.group(2)
            right_table = match.group(3)
            right_col = match.group(4)

            if left_table in base_tables and right_table in base_tables:
                fks.append(
                    ForeignKeySchema(
                        source_table=left_table,
                        source_column=left_col,
                        target_table=right_table,
                        target_column=right_col,
                        is_inferred=True,
                    )
                )

        return fks

    def _extract_column_mappings(self, normalized_sql: str) -> Dict[str, str]:
        """Extract column mappings (derived → source)."""
        mappings = {}

        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(select_pattern, normalized_sql, re.IGNORECASE | re.DOTALL)
        if not match:
            return mappings

        select_list = match.group(1)

        # col_ref [AS] alias
        col_pattern = r"([\w\.]+)\s+(?:AS\s+)?(?:`)?(\w+)(?:`)?"
        for col_match in re.finditer(col_pattern, select_list):
            source = col_match.group(1)
            alias = col_match.group(2)
            if alias != source:
                mappings[alias] = source

        return mappings

    def _infer_column_type(self, col_name: str) -> str:
        """
        Infer column data type from name heuristics.

        Simplified approach — in production, query INFORMATION_SCHEMA.COLUMNS.
        """
        col_lower = col_name.lower()

        # Numeric
        if any(x in col_lower for x in ["amount", "value", "count", "total", "sum"]):
            return "DOUBLE"
        # Date
        if any(x in col_lower for x in ["date", "time", "month", "year"]):
            return "TIMESTAMP"
        # Default: string
        return "STRING"
