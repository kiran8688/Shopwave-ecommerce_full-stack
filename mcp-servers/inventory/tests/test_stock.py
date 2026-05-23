# mcp-servers/inventory/tests/test_stock.py
# ─────────────────────────────────────────────────────────────────────────────
# Unit tests for inventory MCP tools.
# asyncpg is mocked so tests run without a live database.
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_conn():
    """Return a mock asyncpg connection ready for use in tests."""
    conn = AsyncMock()
    conn.close = AsyncMock()
    return conn


# ── check_stock_levels ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_check_stock_levels_returns_all_statuses(mock_conn):
    """
    Verify the three status labels map correctly to quantity thresholds.
    out_of_stock (0), low_stock (<10), in_stock (>=10).
    """
    mock_conn.fetch.return_value = [
        {"id": "uuid-1", "name": "Widget A", "stock_quantity": 0,   "status": "out_of_stock"},
        {"id": "uuid-2", "name": "Widget B", "stock_quantity": 5,   "status": "low_stock"},
        {"id": "uuid-3", "name": "Widget C", "stock_quantity": 100, "status": "in_stock"},
    ]

    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        # Import inside test so the patch is active during import
        import importlib
        import sys
        if "server" in sys.modules:
            del sys.modules["server"]
        sys.path.insert(0, "/home/claude/ecommerce/mcp-servers/inventory")
        from server import check_stock_levels

        result = await check_stock_levels(["uuid-1", "uuid-2", "uuid-3"])

    assert result["checked_count"] == 3
    by_id = {r["id"]: r["status"] for r in result["stock_levels"]}
    assert by_id["uuid-1"] == "out_of_stock"
    assert by_id["uuid-2"] == "low_stock"
    assert by_id["uuid-3"] == "in_stock"


@pytest.mark.asyncio
async def test_check_stock_levels_empty_list(mock_conn):
    """Empty product_ids list should return an empty stock_levels array."""
    mock_conn.fetch.return_value = []

    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        import sys
        sys.path.insert(0, "/home/claude/ecommerce/mcp-servers/inventory")
        from server import check_stock_levels
        result = await check_stock_levels([])

    assert result["checked_count"] == 0
    assert result["stock_levels"] == []


# ── suggest_reorder ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_suggest_reorder_urgent_when_days_less_than_lead_time(mock_conn):
    """
    Stock = 5 units, daily velocity = 2 → stockout in 2.5 days.
    Lead time = 7 days → urgency should be 'urgent'.
    """
    mock_conn.fetchrow.return_value = {"name": "Fast Mover", "stock_quantity": 5}
    mock_conn.fetchval.return_value = 2.0  # 2 units/day

    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        import sys
        sys.path.insert(0, "/home/claude/ecommerce/mcp-servers/inventory")
        from server import suggest_reorder
        result = await suggest_reorder("some-uuid", lead_time_days=7)

    assert result["urgency"] == "urgent"
    assert result["days_until_stockout"] < 7
    assert result["current_stock"] == 5


@pytest.mark.asyncio
async def test_suggest_reorder_optional_when_plenty_of_stock(mock_conn):
    """
    Stock = 500, velocity = 1/day → stockout in 500 days.
    Lead time = 7 days → urgency should be 'optional'.
    """
    mock_conn.fetchrow.return_value = {"name": "Slow Mover", "stock_quantity": 500}
    mock_conn.fetchval.return_value = 1.0

    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        import sys
        sys.path.insert(0, "/home/claude/ecommerce/mcp-servers/inventory")
        from server import suggest_reorder
        result = await suggest_reorder("some-uuid", lead_time_days=7)

    assert result["urgency"] == "optional"


@pytest.mark.asyncio
async def test_suggest_reorder_product_not_found(mock_conn):
    """Return an error dict (not raise) when the product UUID doesn't exist."""
    mock_conn.fetchrow.return_value = None

    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        import sys
        sys.path.insert(0, "/home/claude/ecommerce/mcp-servers/inventory")
        from server import suggest_reorder
        result = await suggest_reorder("nonexistent-uuid")

    assert "error" in result


# ── bulk_update_stock ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bulk_update_stock_success(mock_conn):
    """All valid updates should appear in the 'updated' list."""
    mock_conn.fetchrow.side_effect = [
        {"id": "uuid-1", "name": "Product A", "stock_quantity": 15},
        {"id": "uuid-2", "name": "Product B", "stock_quantity": 25},
    ]
    # Mock transaction context manager
    mock_conn.transaction.return_value.__aenter__ = AsyncMock(return_value=None)
    mock_conn.transaction.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
        import sys
        sys.path.insert(0, "/home/claude/ecommerce/mcp-servers/inventory")
        from server import bulk_update_stock
        result = await bulk_update_stock([
            {"product_id": "uuid-1", "quantity_delta": 5},
            {"product_id": "uuid-2", "quantity_delta": 10},
        ])

    assert result["failed_count"] == 0
