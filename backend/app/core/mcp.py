# app/core/mcp.py
"""
Mock MCP clients for backend integration.
In a real deployment, these would connect to the FastMCP servers via SSE or stdio
and invoke the registered tools using the standard MCP protocol.
"""

from typing import Any

class MockMCPClient:
    def __init__(self, name: str):
        self.name = name

    async def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        # Implementation left to the MCP SDK
        # This is a stub for type-checking and structural correctness in endpoints.
        return {"status": "mocked", "tool": tool_name, "args": kwargs}

payments_mcp = MockMCPClient("shopwave-payments")
notify_mcp = MockMCPClient("shopwave-notifications")
search_mcp = MockMCPClient("shopwave-search")
inventory_mcp = MockMCPClient("shopwave-inventory")
custom_player_mcp = MockMCPClient("shopwave-custom-player")
analytics_mcp = MockMCPClient("shopwave-analytics")
