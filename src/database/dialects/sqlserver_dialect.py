"""
SQL Server / Azure SQL dialect - extracts SchemaContract from T-SQL view definitions.

Uses regex + lightweight tokenization (not a full AST parser) to extract:
- Base tables and column schemas
- Foreign key relationships
- Column mappings (derived → source)
- Semantic roles (FACT, DIMENSION)

T-SQL uses bracket-quoting [identifier] instead of double-quote quoting.
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


class SqlServerDialect(QueryDialect):
    """Schema contract extractor for SQL Server / Azure SQL T-SQL dialect."""

    async def extract_schema_contract(self, view_name: str, view_sql: str) -> SchemaContract:
        """
        Extract complete schema contract from a T-SQL view definition.

        Returns SchemaContract with:
        - Base tables and column schemas
        - Foreign key relationships
        - Column lineage
        - Semantic roles
        """
        contract = SchemaContract(
            view_name=view_name,
            source_system="sqlserver",
            native_sql=view_sql,
            parse_confidence=0.75,  # Regex-based, not 100% accurate
        )

        try:
            normalized = " ".join(view_sql.split())

            # Extract base tables from FROM and JOIN clauses
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

            # Infer foreign keys from JOIN ON conditions
            fks = self._extract_foreign_keys(normalized, base_tables)
            contract.foreign_keys = fks

            # Extract column mappings
            contract.column_mappings = self._extract_column_mappings(normalized)

            # Infer table role from number of base tables
            if len(base_tables) > 1:
                contract.tables[0].role = "FACT"
            elif len(base_tables) == 1:
                contract.tables[0].role = "DIMENSION"

            return contract
        except Exception as e:
            self.logger.warning(f"SQL Server schema extraction error: {e}")
            contract.parse_confidence = 0.1
            contract.notes = str(e)
            return contract

    def _extract_tables(self, normalized_sql: str) -> List[str]:
        """Extract table names from FROM and JOIN clauses (handles bracket-quoting)."""
        tables = []

        # FROM clause: FROM [schema.]table [alias]  or  FROM [schema.][table] [alias]
        # Bracket-quoted: [TableName]  or  [schema].[TableName]  or  plain TableName
        from_pattern = (
            r"FROM\s+"
            r"(?:\[[\w\s]+\]\.)?(?:\[?([\w]+)\]?)"  # optional schema, then table name
            r"(?:\s+(?:AS\s+)?(\w+))?"              # optional alias
        )
        for match in re.finditer(from_pattern, normalized_sql, re.IGNORECASE):
            table_name = match.group(1)
            if table_name and table_name.upper() not in ("VALUES", "SELECT"):
                tables.append(table_name)

        # JOIN clause: [INNER|LEFT|RIGHT|FULL] JOIN [schema.]table [alias]
        join_pattern = (
            r"(?:INNER\s+|LEFT\s+OUTER\s+|RIGHT\s+OUTER\s+|FULL\s+OUTER\s+|"
            r"LEFT\s+|RIGHT\s+|FULL\s+|CROSS\s+)?JOIN\s+"
            r"(?:\[[\w\s]+\]\.)?(?:\[?([\w]+)\]?)"
        )
        for match in re.finditer(join_pattern, normalized_sql, re.IGNORECASE):
            table_name = match.group(1)
            if table_name and table_name not in tables:
                tables.append(table_name)

        return tables

    def _extract_columns(self, normalized_sql: str) -> List[ColumnSchema]:
        """Extract column definitions from SELECT list (handles bracket-quoting)."""
        columns = []

        # SELECT [...] FROM pattern
        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(select_pattern, normalized_sql, re.IGNORECASE | re.DOTALL)
        if not match:
            return columns

        select_list = match.group(1)

        # Parse each column: [alias.]col_ref [AS [alias]]  or  alias.col_ref AS alias
        # Handles: ft.transaction_id, gl.account_name AS account_name, etc.
        col_pattern = r"([\w\.\[\]]+)\s+(?:AS\s+)?(?:\[?(\w+)\]?)(?:\s*,|$)"
        for col_match in re.finditer(col_pattern, select_list):
            source = col_match.group(1).strip("[]")
            alias = col_match.group(2) or source.split(".")[-1].strip("[]")

            col_type = self._infer_column_type(alias)

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
        """Extract FK relationships from JOIN ON conditions (handles bracket-quoting)."""
        fks = []

        # ON condition: [table1].[col1] = [table2].[col2]  or  table1.col1 = table2.col2
        on_pattern = (
            r"ON\s+"
            r"(?:\[?(\w+)\]?)\.(?:\[?(\w+)\]?)"   # left_table.left_col
            r"\s*=\s*"
            r"(?:\[?(\w+)\]?)\.(?:\[?(\w+)\]?)"   # right_table.right_col
        )
        for match in re.finditer(on_pattern, normalized_sql, re.IGNORECASE):
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
        """Extract column mappings (derived → source) from SELECT list."""
        mappings = {}

        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(select_pattern, normalized_sql, re.IGNORECASE | re.DOTALL)
        if not match:
            return mappings

        select_list = match.group(1)

        # col_ref [AS] alias — strip brackets
        col_pattern = r"([\w\.\[\]]+)\s+(?:AS\s+)?(?:\[?(\w+)\]?)"
        for col_match in re.finditer(col_pattern, select_list):
            source = col_match.group(1).strip("[]")
            alias = col_match.group(2)
            if alias and alias != source:
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
            return "DECIMAL"
        # Integer identifiers and year/period
        if any(x in col_lower for x in ["_id", "fiscal_year", "fiscal_period_num"]):
            return "INT"
        # Date
        if any(x in col_lower for x in ["date", "time", "month", "year"]):
            return "DATE"
        # Default: string
        return "NVARCHAR"
