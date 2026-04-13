"""
QueryDialect abstraction - schema contract extraction for multi-warehouse support.

QueryDialect extracts complete schema contracts from customer view definitions.
These contracts flow through Data Product Onboarding → Contract YAML → DPA
query generation → MCP interface (Phase 10D).

Dialects extract:
- Complete table and column schemas
- Foreign key relationships
- Semantic roles (fact, dimension, measures, dimensions)
- Column lineage and mappings
"""

from src.database.dialects.base_dialect import (
    QueryDialect,
    SchemaContract,
    TableSchema,
    ColumnSchema,
    ForeignKeySchema,
)

__all__ = [
    "QueryDialect",
    "SchemaContract",
    "TableSchema",
    "ColumnSchema",
    "ForeignKeySchema",
]
