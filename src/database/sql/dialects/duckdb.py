"""
DuckDB SQL Dialect - SQL dialect-specific logic for DuckDB.

This module provides dialect-specific SQL handling for DuckDB,
including syntax transformations, optimizations, and validations.

Part of the Multi-Cloud Platform (MCP) service architecture.
"""

import re
from typing import Dict, Any, List, Tuple, Optional

from src.database.sql.validator import SQLValidator


class DuckDBDialect:
    """
    DuckDB-specific SQL dialect handler.
    Provides transformations and validations specific to DuckDB.
    """
    
    @staticmethod
    def validate(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL statement for DuckDB-specific syntax and security.
        
        Args:
            sql: The SQL statement to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # First apply common SQL validation
        is_valid, error_msg = SQLValidator.validate_select_only(sql)
        if not is_valid:
            return False, error_msg
            
        # Check for DuckDB-specific issues
        return DuckDBDialect._check_duckdb_specific(sql)
    
    @staticmethod
    def _check_duckdb_specific(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Check for DuckDB-specific syntax issues or unsupported features.
        
        Args:
            sql: The SQL statement to check
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for unsupported DuckDB functions or syntax
        unsupported_patterns = [
            # Add any DuckDB-specific syntax that should be disallowed
            r'\bUNNEST\b',  # Example of a function that might be restricted
            r'\bSAMPLE\b'   # Example of another restricted function
        ]
        
        for pattern in unsupported_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                error_msg = f"SQL statement contains restricted DuckDB feature: {pattern}"
                return False, error_msg
        
        return True, None
    
    @staticmethod
    def transform_for_compatibility(sql: str) -> str:
        """
        Transform a SQL statement for compatibility with DuckDB.
        This can handle common SQL patterns that need adjustment.
        
        Args:
            sql: The SQL statement to transform
            
        Returns:
            Transformed SQL statement compatible with DuckDB
        """
        # Transform SQL for DuckDB compatibility
        
        # Replace SHOW TABLES FROM with SHOW TABLES for DuckDB
        sql = re.sub(r'SHOW\s+TABLES\s+FROM\s+(\w+)', r'SHOW TABLES', sql, flags=re.IGNORECASE)
        
        # Replace DATE_FORMAT with strftime for DuckDB
        sql = re.sub(r'DATE_FORMAT\s*\(([^,]+),\s*[\'"]([^\'"]*)[\'"]\)', r'strftime(\2, \1)', sql, flags=re.IGNORECASE)
        
        # Replace IF with CASE WHEN in expressions
        # This is a simplified example - actual implementation would be more complex
        sql = re.sub(r'IF\s*\(([^,]+),\s*([^,]+),\s*([^\)]+)\)', r'CASE WHEN \1 THEN \2 ELSE \3 END', sql, flags=re.IGNORECASE)
        
        return sql
