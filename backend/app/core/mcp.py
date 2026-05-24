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
        analytics_mcp as real_analytics_mcp,
    )
    from app.utils.mcp_client import (
        content_mcp as real_content_mcp,
    )
    from app.utils.mcp_client import (
        inventory_mcp as real_inventory_mcp,
    )
    from app.utils.mcp_client import (
        notify_mcp as real_notify_mcp,
    )
    from app.utils.mcp_client import (
        payments_mcp as real_payments_mcp,
    )
    from app.utils.mcp_client import (
        search_mcp as real_search_mcp,
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
            # 1. Payments Client mock responses
            if self.name == "shopwave-payments" or tool_name in ("create_payment_intent", "verify_payment", "process_refund"):
                if tool_name == "create_payment_intent":
                    amount_paise = kwargs.get("amount_paise") or kwargs.get("amount") or 50000
                    currency = kwargs.get("currency", "INR")
                    shopwave_order_id = kwargs.get("order_id") or kwargs.get("shopwave_order_id", "ord_12345")
                    razorpay_order_id = f"order_mock_{str(shopwave_order_id).replace('-', '')[:14]}"
                    return {
                        "razorpay_order_id": razorpay_order_id,
                        "amount": amount_paise,
                        "currency": currency,
                        "status": "created",
                        "shopwave_order_id": shopwave_order_id,
                        "key_id": "rzp_test_shopwavekeys"
                    }
                elif tool_name == "verify_payment":
                    return {
                        "verified": True,
                        "status": "success",
                        "message": "Signature verified successfully."
                    }
                elif tool_name == "process_refund":
                    amount = kwargs.get("amount", 1000)
                    currency = kwargs.get("currency", "INR")
                    payment_id = kwargs.get("payment_id") or kwargs.get("razorpay_payment_id", "pay_mock_123")
                    return {
                        "refund_id": f"rfnd_mock_{str(payment_id).replace('pay_', '')}",
                        "status": "processed",
                        "amount": amount,
                        "currency": currency,
                        "razorpay_payment_id": payment_id
                    }

            # 2. Inventory Client mock responses
            if self.name == "shopwave-inventory" or tool_name in ("check_stock_levels", "suggest_reorder"):
                if tool_name == "check_stock_levels":
                    product_ids = kwargs.get("product_ids", [])
                    if isinstance(product_ids, str):
                        product_ids = [product_ids]
                    stock_levels = {}
                    for pid in product_ids:
                        stock_levels[pid] = {
                            "stock_quantity": 42,
                            "status": "in_stock",
                            "reorder_point": 10
                        }
                    return {
                        "stock_levels": stock_levels,
                        "status": "success"
                    }
                elif tool_name == "suggest_reorder":
                    product_id = kwargs.get("product_id", "prod_123")
                    return {
                        "product_id": product_id,
                        "suggested_reorder_quantity": 50,
                        "reason": "Stock level below reorder point and high velocity sales in previous 14 days",
                        "lead_time_days": kwargs.get("lead_time_days", 7),
                        "priority": "medium",
                        "status": "success"
                    }

            # 3. Search Client mock responses
            if self.name == "shopwave-search" or tool_name == "semantic_search":
                category_id = kwargs.get("category_id") or "79815a51-bd11-4775-8167-96ef8c0aefbe"
                results = [
                    {
                        "id": "e36e6d1e-bfba-4b82-9602-4b71239c0993",
                        "name": "ShopWave Premium Wireless Headphones",
                        "slug": "shopwave-premium-wireless-headphones",
                        "description": "Experience pure sound isolation and deep bass with these premium noise-canceling headphones.",
                        "sku": "SW-WHP-001",
                        "price": 8999.00,
                        "compare_at_price": 12999.00,
                        "stock_quantity": 42,
                        "is_active": True,
                        "is_featured": True,
                        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60",
                        "thumbnail_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150&auto=format&fit=crop&q=60",
                        "category_id": category_id,
                        "aiScore": 98.0
                    },
                    {
                        "id": "a988d8b9-50e5-4d22-b430-c3d52d929944",
                        "name": "Minimalist Leather Backpack",
                        "slug": "minimalist-leather-backpack",
                        "description": "Handcrafted full-grain leather backpack designed to carry your daily essentials and a 16-inch laptop.",
                        "sku": "SW-LBP-002",
                        "price": 4500.00,
                        "compare_at_price": 5999.00,
                        "stock_quantity": 18,
                        "is_active": True,
                        "is_featured": False,
                        "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=500&auto=format&fit=crop&q=60",
                        "thumbnail_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=150&auto=format&fit=crop&q=60",
                        "category_id": category_id,
                        "aiScore": 89.5
                    },
                    {
                        "id": "c72c8423-f38b-4b14-8f53-488f7b76e1a2",
                        "name": "Mechanical Gaming Keyboard RGB",
                        "slug": "mechanical-gaming-keyboard-rgb",
                        "description": "Tactile clicky switches and customizable RGB lighting for ultimate gaming performance.",
                        "sku": "SW-MKB-003",
                        "price": 3200.00,
                        "compare_at_price": 4499.00,
                        "stock_quantity": 25,
                        "is_active": True,
                        "is_featured": True,
                        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=60",
                        "thumbnail_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=150&auto=format&fit=crop&q=60",
                        "category_id": category_id,
                        "aiScore": 82.3
                    }
                ]
                return {
                    "results": results,
                    "count": len(results),
                    "query": kwargs.get("query", ""),
                    "status": "success"
                }

            return {"status": "mocked", "tool": tool_name, "args": kwargs}

    payments_mcp = MockMCPClient("shopwave-payments")
    notify_mcp = MockMCPClient("shopwave-notifications")
    search_mcp = MockMCPClient("shopwave-search")
    inventory_mcp = MockMCPClient("shopwave-inventory")
    custom_player_mcp = MockMCPClient("shopwave-custom-player")
    analytics_mcp = MockMCPClient("shopwave-analytics")
