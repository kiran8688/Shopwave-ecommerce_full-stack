# app/core/mcp.py
# ─────────────────────────────────────────────────────────────────────────────
# Dynamic MCP Client Provider.
# Reads the MOCK_MCP environment variable:
#   • If MOCK_MCP=true (default): exports MockMCPClient stubs.
#   • If MOCK_MCP=false: imports live HTTP/JSON-RPC clients from utils/mcp_client.py
#     and wraps them in a keyword-argument adapter for router compatibility.
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Any

# Check environment state (defaults to mock/stubs for safety)
MOCK_MCP = os.getenv("MOCK_MCP", "true").lower() in ("true", "1", "yes")

if not MOCK_MCP:
    # Import the real HTTP clients connected to the Docker internal network
    from app.utils.mcp_client import (
        inventory_mcp as real_inventory_mcp,
        payments_mcp as real_payments_mcp,
        search_mcp as real_search_mcp,
        notify_mcp as real_notify_mcp,
        analytics_mcp as real_analytics_mcp,
        content_mcp as real_content_mcp,
    )

    class MCPClientAdapter:
        """
        Adapts the real MCPClient (which takes a single 'arguments' dictionary)
        to match the keyword arguments format (**kwargs) expected by all endpoints.
        """
        def __init__(self, real_client: Any):
            self.real_client = real_client

        async def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
            # Translate keyword arguments (e.g. order_id=x, currency=y) into a params dict
            return await self.real_client.call_tool(tool_name, arguments=kwargs)

    payments_mcp = MCPClientAdapter(real_payments_mcp)
    notify_mcp = MCPClientAdapter(real_notify_mcp)
    search_mcp = MCPClientAdapter(real_search_mcp)
    inventory_mcp = MCPClientAdapter(real_inventory_mcp)
    custom_player_mcp = MCPClientAdapter(real_content_mcp)
    analytics_mcp = MCPClientAdapter(real_analytics_mcp)

else:
    class MockMCPClient:
        """
        Standard stub mock client used for local testing and standalone deployments.
        """
        def __init__(self, name: str):
            self.name = name

        async def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
            return {"status": "mocked", "tool": tool_name, "args": kwargs}

    payments_mcp = MockMCPClient("shopwave-payments")
    notify_mcp = MockMCPClient("shopwave-notifications")
    search_mcp = MockMCPClient("shopwave-search")
    inventory_mcp = MockMCPClient("shopwave-inventory")
    custom_player_mcp = MockMCPClient("shopwave-custom-player")
    analytics_mcp = MockMCPClient("shopwave-analytics")
