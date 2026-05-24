# mcp-servers/inventory/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Inventory Server — stock intelligence for ShopWave.
# Exposes three tools: check_stock_levels, suggest_reorder, bulk_update_stock.
# ─────────────────────────────────────────────────────────────────────────────

import os
import asyncpg
from mcp.server.fastmcp import FastMCP
from typing import Any

mcp = FastMCP(
    name="shopwave-inventory",
    dependencies=["asyncpg"],
)

DB_URL = os.environ.get("DATABASE_URL", "postgresql://shopwave:shopwave_pass@db:5432/shopwave_db")


async def _conn():
    """Open a fresh asyncpg connection. Always close in a try/finally block."""
    return await asyncpg.connect(DB_URL)


# ── Tool 1: check_stock_levels ────────────────────────────────────────────────

@mcp.tool()
async def check_stock_levels(product_ids: list[str]) -> dict[str, Any]:
    """
    Return current stock quantities and status labels for a list of product UUIDs.

    Status labels:
      out_of_stock  → qty = 0
      low_stock     → qty < 10
      in_stock      → qty >= 10
    """
    conn = await _conn()
    try:
        rows = await conn.fetch(
            """
            SELECT id::text, name, stock_quantity,
                   CASE
                     WHEN stock_quantity = 0   THEN 'out_of_stock'
                     WHEN stock_quantity < 10  THEN 'low_stock'
                     ELSE 'in_stock'
                   END AS status
            FROM products
            WHERE id = ANY($1::uuid[])
              AND is_active = true
            ORDER BY stock_quantity ASC
            """,
            product_ids,
        )
        return {"stock_levels": [dict(r) for r in rows], "checked_count": len(rows)}
    finally:
        await conn.close()


# ── Tool 2: suggest_reorder ───────────────────────────────────────────────────

@mcp.tool()
async def suggest_reorder(product_id: str, lead_time_days: int = 7) -> dict[str, Any]:
    """
    AI-ready reorder recommendation based on 30-day sales velocity.

    Calculates days until stockout at current sell rate; flags urgency if
    stockout will occur before new stock can arrive (lead_time_days).
    """
    conn = await _conn()
    try:
        product = await conn.fetchrow(
            "SELECT name, stock_quantity FROM products WHERE id = $1::uuid AND is_active = true",
            product_id,
        )
        if not product:
            return {"error": "Product not found", "product_id": product_id}

        # Average daily units sold over the last 30 days (excludes cancelled/refunded)
        velocity = await conn.fetchval(
            """
            SELECT COALESCE(SUM(oi.quantity), 0) / 30.0
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id = $1::uuid
              AND o.created_at > NOW() - INTERVAL '30 days'
              AND o.status NOT IN ('cancelled', 'refunded')
            """,
            product_id,
        )

        stock = product["stock_quantity"]
        daily_velocity = float(velocity or 0)
        days_until_stockout = (stock / daily_velocity) if daily_velocity > 0 else 9999.0

        urgency = "urgent" if days_until_stockout < lead_time_days else (
            "recommended" if days_until_stockout < lead_time_days * 2 else "optional"
        )

        return {
            "product_id": product_id,
            "product_name": product["name"],
            "current_stock": stock,
            "daily_velocity": round(daily_velocity, 2),
            "days_until_stockout": round(days_until_stockout, 1),
            "urgency": urgency,
            "suggested_reorder_quantity": max(int(daily_velocity * 30), 10),
            "lead_time_days": lead_time_days,
        }
    finally:
        await conn.close()


# ── Tool 3: bulk_update_stock ─────────────────────────────────────────────────

@mcp.tool()
async def bulk_update_stock(updates: list[dict]) -> dict[str, Any]:
    """
    Batch update stock quantities.

    Each update: { product_id: str, quantity_delta: int }
    Positive delta = received stock. Negative = manual reduction.
    All updates run in a single transaction — all succeed or all roll back.
    """
    conn = await _conn()
    updated, failed = [], []
    try:
        async with conn.transaction():
            for upd in updates:
                pid, delta = upd["product_id"], upd["quantity_delta"]
                try:
                    row = await conn.fetchrow(
                        """
                        UPDATE products
                        SET stock_quantity = GREATEST(0, stock_quantity + $1),
                            updated_at = NOW()
                        WHERE id = $2::uuid
                        RETURNING id::text, name, stock_quantity
                        """,
                        delta, pid,
                    )
                    if row:
                        updated.append(dict(row))
                    else:
                        failed.append({"product_id": pid, "reason": "not_found"})
                except Exception as exc:
                    failed.append({"product_id": pid, "reason": str(exc)})
    finally:
        await conn.close()

    return {
        "updated": updated, "failed": failed,
        "updated_count": len(updated), "failed_count": len(failed),
    }


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
