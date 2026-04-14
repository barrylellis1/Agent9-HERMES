"""
MCP (Model Context Protocol) HTTP Client for Data Platform Integration

Provides a thin HTTP abstraction over vendor-managed MCP servers (Snowflake, Databricks, BigQuery).
Handles authentication, tool invocation, and error handling without importing vendor SDKs.

Architecture:
- MCPClient: HTTP transport abstraction for JSON-RPC tool calls
- MCPManager (in backends/): Implements DatabaseManager ABC, uses MCPClient
- MCPConnectionFactory: Factory for creating MCPManager instances

Auth methods: bearer token (Snowflake, Databricks PAT), GCP OIDC (BigQuery)
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import httpx


class MCPError(Exception):
    """Raised when an MCP server returns an error or is unreachable."""

    pass


@dataclass
class MCPToolResult:
    """Response from an MCP tool invocation."""

    content: List[Dict[str, Any]]  # Tool output content blocks
    is_error: bool = False  # Whether the tool invocation resulted in an error

    def get_text(self) -> str:
        """Extract plain text from the first content block."""
        if not self.content:
            return ""
        first = self.content[0]
        if isinstance(first, dict):
            return first.get("text", "")
        return ""


class MCPClient:
    """
    HTTP client for invoking tools on vendor-managed MCP servers.

    Supports Snowflake, Databricks, and BigQuery managed MCP servers.
    Handles authentication via bearer tokens or GCP OIDC.

    Example:
        client = MCPClient(
            endpoint="https://mcp.snowflake.com",
            auth_token="my-oauth-token",
            auth_type="bearer"
        )
        result = await client.call_tool("sql_execute", {"sql": "SELECT 1"})
        print(result.get_text())
        await client.close()
    """

    def __init__(
        self,
        endpoint: str,
        auth_token: Union[str, Callable[[], str]],
        auth_type: str = "bearer",
        timeout: int = 30,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize MCP client.

        Args:
            endpoint: Base URL of the MCP server (e.g., "https://mcp.example.com")
            auth_token: Bearer token or callable that returns a token (for GCP OIDC)
            auth_type: Authentication type: "bearer", "pat" (alias for bearer), or "gcp_oidc"
            timeout: Request timeout in seconds
            logger: Optional logger for debug output
        """
        self.endpoint = endpoint.rstrip("/")
        self.auth_token = auth_token
        self.auth_type = auth_type.lower()
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

        self._client: Optional[httpx.AsyncClient] = None

    def _auth_headers(self) -> Dict[str, str]:
        """Build authorization headers based on auth_type."""
        if self.auth_type in ("bearer", "pat"):
            # PAT (Personal Access Token) is treated as a bearer token
            token = self.auth_token() if callable(self.auth_token) else self.auth_token
            return {"Authorization": f"Bearer {token}"}
        if self.auth_type == "gcp_oidc":
            # For GCP OIDC, auth_token may be a callable returning a token
            token = self.auth_token() if callable(self.auth_token) else self.auth_token
            return {"Authorization": f"Bearer {token}"}
        # Default to bearer
        token = self.auth_token() if callable(self.auth_token) else self.auth_token
        return {"Authorization": f"Bearer {token}"}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the underlying httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def call_tool(self, tool_name: str, input: Dict[str, Any]) -> MCPToolResult:
        """
        Invoke a tool on the MCP server.

        Args:
            tool_name: Name of the tool to invoke (e.g., "sql_execute")
            input: Tool arguments (tool-specific)

        Returns:
            MCPToolResult containing the tool output

        Raises:
            MCPError: If the request fails, server returns an error, or response is invalid
        """
        client = await self._get_client()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": input,
            },
        }
        url = f"{self.endpoint}/mcp"

        try:
            response = await client.post(
                url,
                json=payload,
                headers={**self._auth_headers(), "Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise MCPError(
                f"HTTP {exc.response.status_code} from MCP server at {url}: {exc.response.text}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise MCPError(f"MCP request to {url} timed out after {self.timeout}s") from exc
        except httpx.RequestError as exc:
            raise MCPError(f"MCP request to {url} failed: {exc}") from exc

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise MCPError(f"Invalid JSON from MCP server at {url}: {exc}") from exc

        if "error" in data:
            error_info = data["error"]
            error_msg = error_info.get("message", "Unknown error") if isinstance(
                error_info, dict
            ) else str(error_info)
            raise MCPError(f"MCP error for tool '{tool_name}': {error_msg}")

        result = data.get("result", {})
        content = result.get("content", [])
        is_error = result.get("isError", False)
        return MCPToolResult(content=content, is_error=is_error)

    async def list_tools(self) -> List[str]:
        """
        List available tools on the MCP server.

        Returns:
            List of tool names

        Raises:
            MCPError: If the request fails or response is invalid
        """
        client = await self._get_client()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        url = f"{self.endpoint}/mcp"

        try:
            response = await client.post(
                url,
                json=payload,
                headers={**self._auth_headers(), "Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise MCPError(
                f"HTTP {exc.response.status_code} listing tools from {url}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise MCPError(f"Tool listing request to {url} failed: {exc}") from exc

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise MCPError(f"Invalid JSON from MCP server at {url}: {exc}") from exc

        tools = data.get("result", {}).get("tools", [])
        return [t.get("name", "") for t in tools if isinstance(t, dict)]

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
