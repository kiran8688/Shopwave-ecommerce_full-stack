# app/api/v1/endpoints/analytics.py
# Admin-only dashboard analytics endpoints.

from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_admin_user
from app.core.mcp import analytics_mcp
from app.models.user import User

router = APIRouter(dependencies=[Depends(get_current_admin_user)])


@router.get("/summary")
async def get_sales_summary(
    date_from: str | None = Query(None, description="Start date in YYYY-MM-DD format"),
    date_to: str | None = Query(None, description="End date in YYYY-MM-DD format"),
):
    """
    Admin-only: Retrieve overall sales metrics summary using analytics_mcp.
    """
    summary = await analytics_mcp.call_tool(
        "get_sales_summary",
        date_from=date_from,
        date_to=date_to
    )
    return summary


@router.get("/top-products")
async def get_top_products(
    limit: int = Query(5, ge=1, le=50, description="Number of top products to fetch"),
    metric: str = Query("revenue", description="Metric to rank products by (revenue, sales_count)"),
):
    """
    Admin-only: Retrieve top performing products by revenue or volume.
    """
    top_products = await analytics_mcp.call_tool(
        "get_top_products",
        limit=limit,
        metric=metric
    )
    return top_products


@router.get("/revenue")
async def get_revenue_by_day(
    days: int = Query(7, ge=1, le=90, description="Number of trailing days of revenue historical data"),
):
    """
    Admin-only: Retrieve daily revenue breakdowns over a period.
    """
    revenue = await analytics_mcp.call_tool(
        "get_revenue_by_day",
        days=days
    )
    return revenue


@router.get("/low-stock")
async def get_low_stock_report(
    threshold: int = Query(10, ge=1, le=100, description="Minimum inventory quantity threshold"),
):
    """
    Admin-only: Retrieve low inventory stock report.
    """
    report = await analytics_mcp.call_tool(
        "get_low_stock_report",
        threshold=threshold
    )
    return report
