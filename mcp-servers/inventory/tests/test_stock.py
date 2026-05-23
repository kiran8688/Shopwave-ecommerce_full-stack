import pytest
import asyncio
from unittest.mock import AsyncMock, patch

class AsyncContextManagerMock:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False

@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    # transaction() is called, not awaited. So we need a Mock that returns an async context manager
    from unittest.mock import MagicMock
    mock_tx = MagicMock()
    mock_tx.return_value = AsyncContextManagerMock()
    conn.transaction = mock_tx
    return conn

@pytest.mark.asyncio
async def test_check_stock_levels_returns_all_statuses(mock_conn):
    mock_conn.fetch.return_value = [
        {"id": "uuid-1", "name": "Widget A", "stock_quantity": 0,   "status": "out_of_stock"},
        {"id": "uuid-2", "name": "Widget B", "stock_quantity": 5,   "status": "low_stock"},
        {"id": "uuid-3", "name": "Widget C", "stock_quantity": 100, "status": "in_stock"},
    ]
    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        import sys
        sys.path.insert(0, "/app/mcp-servers/inventory")
        from server import check_stock_levels
        result = await check_stock_levels(["uuid-1", "uuid-2", "uuid-3"])
        assert result["checked_count"] == 3
        statuses = {r["id"]: r["status"] for r in result["stock_levels"]}
        assert statuses["uuid-1"] == "out_of_stock"
        assert statuses["uuid-2"] == "low_stock"
        assert statuses["uuid-3"] == "in_stock"

@pytest.mark.asyncio
async def test_check_stock_levels_empty_list(mock_conn):
    mock_conn.fetch.return_value = []
    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        from server import check_stock_levels
        result = await check_stock_levels([])
        assert result["checked_count"] == 0
        assert result["stock_levels"] == []

@pytest.mark.asyncio
async def test_suggest_reorder_urgent_when_days_less_than_lead_time(mock_conn):
    mock_conn.fetchrow.return_value = {"name": "Fast Mover", "stock_quantity": 5}
    mock_conn.fetchval.return_value = 2.0  # 2 units/day
    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        from server import suggest_reorder
        result = await suggest_reorder("some-uuid", lead_time_days=7)
        assert result["urgency"] == "urgent"
        assert result["days_until_stockout"] == 2.5

@pytest.mark.asyncio
async def test_suggest_reorder_optional_when_plenty_of_stock(mock_conn):
    mock_conn.fetchrow.return_value = {"name": "Slow Mover", "stock_quantity": 500}
    mock_conn.fetchval.return_value = 1.0
    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        from server import suggest_reorder
        result = await suggest_reorder("some-uuid", lead_time_days=7)
        assert result["urgency"] == "optional"
        assert result["days_until_stockout"] == 500.0

@pytest.mark.asyncio
async def test_suggest_reorder_product_not_found(mock_conn):
    mock_conn.fetchrow.return_value = None
    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        from server import suggest_reorder
        result = await suggest_reorder("some-uuid")
        assert "error" in result

@pytest.mark.asyncio
async def test_bulk_update_stock_success(mock_conn):
    mock_conn.fetchrow.side_effect = [
        {"id": "uuid-1", "name": "Product A", "stock_quantity": 15},
        {"id": "uuid-2", "name": "Product B", "stock_quantity": 25},
    ]
    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        from server import bulk_update_stock
        result = await bulk_update_stock([
            {"product_id": "uuid-1", "quantity_delta": 5},
            {"product_id": "uuid-2", "quantity_delta": 10},
        ])
        assert result["updated_count"] == 2
        assert result["failed_count"] == 0
        assert result["updated"][0]["id"] == "uuid-1"
