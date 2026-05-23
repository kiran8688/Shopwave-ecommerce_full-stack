# mcp-servers/analytics/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Analytics Server — business intelligence queries over the ShopWave DB.
# All queries exclude cancelled/refunded orders for accurate revenue reporting.
# ─────────────────────────────────────────────────────────────────────────────

import os
import asyncpg
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="shopwave-analytics", dependencies=["asyncpg"])
DB_URL = os.environ.get("DATABASE_URL", "")


async def _conn():
    return await asyncpg.connect(DB_URL)


@mcp.tool()
async def get_sales_summary(date_from: str, date_to: str) -> dict[str, Any]:
    """
    Aggregate revenue and order metrics for a calendar period.

    Args:
        date_from: ISO date "YYYY-MM-DD" (inclusive start).
        date_to:   ISO date "YYYY-MM-DD" (inclusive end).

    Returns:
        total_revenue, order_count, avg_order_value, unique_customers
    """
    conn = await _conn()
    try:
        row = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(total_amount), 0)::float     AS total_revenue,
                COUNT(*)                                   AS order_count,
                COALESCE(AVG(total_amount), 0)::float     AS avg_order_value,
                COUNT(DISTINCT user_id)                    AS unique_customers
            FROM orders
            WHERE created_at::date BETWEEN $1::date AND $2::date
              AND status NOT IN ('cancelled', 'refunded')
            """,
            date_from, date_to,
        )
        return {"period": {"from": date_from, "to": date_to}, **dict(row)}
    finally:
        await conn.close()


@mcp.tool()
async def get_top_products(limit: int = 10, metric: str = "revenue") -> dict[str, Any]:
    """
    Return top-performing products sorted by revenue or quantity sold.

    Args:
        limit:  Number of products (1-50).
        metric: "revenue" | "quantity"
    """
    if metric not in ("revenue", "quantity"):
        return {"error": "metric must be 'revenue' or 'quantity'"}

    order_col = "SUM(oi.line_total)" if metric == "revenue" else "SUM(oi.quantity)"
    conn = await _conn()
    try:
        rows = await conn.fetch(
            f"""
            SELECT p.id::text AS product_id, p.name,
                   SUM(oi.line_total)::float AS total_revenue,
                   SUM(oi.quantity)          AS total_quantity_sold
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o   ON oi.order_id   = o.id
            WHERE o.status NOT IN ('cancelled', 'refunded')
            GROUP BY p.id, p.name
            ORDER BY {order_col} DESC
            LIMIT $1
            """,
            min(limit, 50),
        )
        return {"metric": metric, "top_products": [dict(r) for r in rows]}
    finally:
        await conn.close()


@mcp.tool()
async def get_revenue_by_day(days: int = 30) -> dict[str, Any]:
    """
    Daily revenue time series for the last N days — used for dashboard charts.

    Args:
        days: Lookback window (max 365).
    """
    conn = await _conn()
    try:
        rows = await conn.fetch(
            """
            SELECT
                created_at::date AS day,
                COUNT(*)          AS order_count,
                SUM(total_amount)::float AS revenue
            FROM orders
            WHERE created_at > NOW() - ($1 || ' days')::interval
              AND status NOT IN ('cancelled', 'refunded')
            GROUP BY created_at::date
            ORDER BY day ASC
            """,
            str(min(days, 365)),
        )
        return {"days": days, "series": [dict(r) for r in rows]}
    finally:
        await conn.close()


@mcp.tool()
async def get_low_stock_report(threshold: int = 10) -> dict[str, Any]:
    """
    Return all products with stock at or below the threshold — admin alert feed.
    """
    conn = await _conn()
    try:
        rows = await conn.fetch(
            """
            SELECT id::text, name, sku, stock_quantity,
                   CASE WHEN stock_quantity = 0 THEN 'out_of_stock' ELSE 'low_stock' END AS status
            FROM products
            WHERE is_active = true AND stock_quantity <= $1
            ORDER BY stock_quantity ASC
            """,
            threshold,
        )
        return {"threshold": threshold, "products": [dict(r) for r in rows], "count": len(rows)}
    finally:
        await conn.close()


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8005)))
