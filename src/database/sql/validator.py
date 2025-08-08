"""
SQL Validator - Common SQL validation logic across database backends.

This module provides SQL validation utilities used by all database backends
to ensure security, correctness, and compliance with platform-specific rules.

Part of the Multi-Cloud Platform (MCP) service architecture for database operations.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class SQLValidator:
    """
    SQL validator for security and correctness checks.
    Used by database backends to validate SQL statements.
    """
    
    @staticmethod
    def validate_select_only(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the SQL statement is a SELECT statement only.
        No DDL or DML allowed for security reasons.
        
        Args:
            sql: The SQL statement to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Normalize SQL (remove comments, extra spaces)
        normalized_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        normalized_sql = re.sub(r'/\*[\s\S]*?\*/', '', normalized_sql)
        normalized_sql = normalized_sql.strip()
        
        # Check if the statement is a SELECT statement
        if not normalized_sql.lower().startswith('select '):
            error_msg = f"Invalid SQL statement (not a SELECT): {sql}"
            return False, error_msg
        
        # Check for disallowed operations (DDL, DML)
        disallowed_patterns = [
            r'\bcreate\b', r'\bdrop\b', r'\balter\b', r'\btruncate\b', 
            r'\binsert\b', r'\bupdate\b', r'\bdelete\b', r'\bmerge\b',
            r'\bgrant\b', r'\brevoke\b', r'\bbegin\b', r'\bcommit\b',
            r'\brollback\b', r'\bcall\b', r'\bexec\b', r'\bexecute\b',
            r'\bsystem\b', r'\bload\b', r'\bdelete\b'
        ]
        
        for pattern in disallowed_patterns:
            if re.search(pattern, normalized_sql.lower()):
                error_msg = f"SQL statement contains disallowed operation: {pattern}"
                return False, error_msg
        
        return True, None
        
    @staticmethod
    def check_sql_injection_risks(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Check for potential SQL injection risks in the statement.
        
        Args:
            sql: The SQL statement to check
            
        Returns:
            Tuple of (is_safe, risk_message)
        """
        # Look for common SQL injection patterns
        risk_patterns = [
            r"'.*;.*--",  # Semicolon followed by comment
            r"'.*;\s*(?:select|insert|update|delete|drop|create|alter)",  # Semicolon followed by another command
            r"'\s*(?:or|and)\s+['\"0-9]+=\s*['\"0-9]+",  # Simple OR/AND injection
            r"'\s*;\s*waitfor\s+delay",  # Time-based SQL injection
            r"xp_cmdshell",  # Command execution in SQL Server
            r"exec\s+\w+",  # Execution of stored procedures
            r"UNION\s+(?:ALL\s+)?SELECT"  # UNION-based SQL injection
        ]
        
        for pattern in risk_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                error_msg = f"SQL statement contains potential SQL injection pattern: {pattern}"
                return False, error_msg
        
        return True, None
