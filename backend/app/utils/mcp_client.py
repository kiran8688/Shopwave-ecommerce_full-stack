# app/utils/mcp_client.py
# ─────────────────────────────────────────────────────────────────────────────
# Async MCP client — calls MCP servers from FastAPI service layer.
# All MCP server addresses resolve via Docker Compose internal DNS.
# ─────────────────────────────────────────────────────────────────────────────

import httpx
from typing import Any
from app.core.config import settings


class MCPToolError(Exception):
    """Raised when an MCP tool call returns a protocol-level error response."""
    def __init__(self, tool: str, code: int | None, message: str):
        self.tool = tool
        self.code = code
        self.message = message
        super().__init__(f"MCP tool '{tool}' failed [{code}]: {message}")


class MCPClient:
    """
    Thin async wrapper around httpx for invoking MCP tool endpoints.

    Usage:
        result = await inventory_mcp.call_tool(
            "check_stock_levels",
            {"product_ids": ["uuid-1", "uuid-2"]},
        )
    """

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Content-Type": "application/json",
            # Shared secret authenticates backend → MCP server calls
            "X-MCP-API-Key": api_key or getattr(settings, "MCP_INTERNAL_API_KEY", "dev-secret"),
        }

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Execute a named tool on the remote MCP server.

        Sends a JSON-RPC 2.0 style payload to /messages and returns the
        parsed result dict. Raises MCPToolError on protocol errors and
        httpx.HTTPStatusError on HTTP 4xx/5xx.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout,
        ) as client:
            response = await client.post("/messages", json=payload)
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise MCPToolError(
                tool=tool_name,
                code=data["error"].get("code"),
                message=data["error"].get("message", "Unknown MCP error"),
            )
        return data.get("result", {})


# ── Singleton clients — import these in service/endpoint files ────────────────
inventory_mcp  = MCPClient(base_url="http://mcp-inventory:8001")
payments_mcp   = MCPClient(base_url="http://mcp-payments:8002")
search_mcp     = MCPClient(base_url="http://mcp-search:8003")
notify_mcp     = MCPClient(base_url="http://mcp-notifications:8004")
analytics_mcp  = MCPClient(base_url="http://mcp-analytics:8005")
content_mcp    = MCPClient(base_url="http://mcp-content:8006")
