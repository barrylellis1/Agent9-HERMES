"""
MCP Connection Factory - Creates MCPManager instances from connection profiles.

Validates MCP configuration and instantiates MCPManager for the appropriate vendor.
"""

import logging
from typing import Any, Dict, Optional

from src.database.backends.mcp_manager import MCPManager


class MCPConnectionFactory:
    """Factory for creating MCPManager instances from connection configuration."""

    @staticmethod
    def create(
        vendor: str,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
    ) -> MCPManager:
        """
        Create an MCPManager instance for a specific vendor.

        Args:
            vendor: Vendor type: "snowflake", "databricks", or "bigquery"
            config: Configuration dict with MCP settings:
                - mcp_endpoint: MCP server endpoint URL (required)
                - mcp_auth_type: Auth type (optional, defaults to "bearer")
                - schema: Default schema/database (optional)
            logger: Optional logger instance

        Returns:
            MCPManager instance ready for connect()

        Raises:
            ValueError: If required configuration is missing
        """
        vendor = vendor.lower()
        logger = logger or logging.getLogger(__name__)

        # Validate required configuration
        if not config.get("mcp_endpoint"):
            raise ValueError("MCP configuration missing: mcp_endpoint is required")

        if vendor not in ("snowflake", "databricks", "bigquery"):
            raise ValueError(f"Unsupported vendor: {vendor}. Must be snowflake, databricks, or bigquery")

        return MCPManager(vendor=vendor, config=config, logger=logger)
