# ShopWave E-Commerce — MCP Implementation Sequence Guide

> **Version:** 1.0.0 | **Stack:** FastAPI + React + PostgreSQL 18 + Docker  
> **Purpose:** Step-by-step roadmap for integrating Model Context Protocol (MCP) servers into the ShopWave platform.

---

## Table of Contents

1. [What is MCP and Why Does ShopWave Need It?](#1-what-is-mcp)
2. [MCP Server Inventory](#2-mcp-server-inventory)
3. [Architecture Overview](#3-architecture-overview)
4. [Implementation Roadmap](#4-implementation-roadmap)
   - [Phase 1 — Core Infrastructure](#phase-1--core-infrastructure)
   - [Phase 2 — Inventory & Catalogue MCP](#phase-2--inventory--catalogue-mcp)
   - [Phase 3 — Payment Gateway MCP](#phase-3--payment-gateway-mcp)
   - [Phase 4 — Search & Indexing MCP](#phase-4--search--indexing-mcp)
   - [Phase 5 — Notification MCP](#phase-5--notification-mcp)
   - [Phase 6 — Analytics MCP](#phase-6--analytics-mcp)
   - [Phase 7 — React Frontend Integration](#phase-7--react-frontend-integration)
5. [Data Flow Reference](#5-data-flow-reference)
6. [Testing MCP Servers](#6-testing-mcp-servers)
7. [Production Checklist](#7-production-checklist)

---

## 1. What is MCP?

**Model Context Protocol (MCP)** is an open standard (developed by Anthropic) that defines a structured interface between AI language models and external tools, APIs, and data sources.

In the ShopWave context, MCP servers act as **intelligent middleware**: FastAPI calls an MCP server, which can use an AI model to reason about data, call external APIs, and return structured results — all through a unified protocol.

### Why use MCP in an e-commerce platform?

| Without MCP | With MCP |
|---|---|
| Hardcoded business rules for inventory thresholds | AI-driven dynamic reorder suggestions |
| Manual product description writing | Auto-generated SEO descriptions from product data |
| Rule-based fraud detection | LLM-powered transaction anomaly detection |
| Static search ranking | Semantic search with contextual re-ranking |
| Template email notifications | Personalised, contextual customer messages |

---

## 2. MCP Server Inventory

The following MCP servers are required for the full ShopWave platform:

### 2.1 Inventory Management MCP (`mcp-inventory`)

- **Purpose:** Monitors stock levels, predicts reorder points, generates purchase order suggestions
- **Domain:** Supply chain, warehouse management
- **Dependencies:** PostgreSQL products table, supplier API credentials
- **Tools exposed:**
  - `check_stock_levels(product_ids[])` → stock report
  - `suggest_reorder(product_id, lead_time_days)` → reorder recommendation
  - `bulk_update_stock(updates[])` → batch stock adjustments

### 2.2 Payment Gateway MCP (`mcp-payments`)

- **Purpose:** Abstracts payment provider (Razorpay/Stripe) interactions; validates payment intents, handles webhooks
- **Domain:** Financial transactions, PCI compliance
- **Dependencies:** Payment provider API keys, orders table
- **Tools exposed:**
  - `create_payment_intent(order_id, amount, currency)` → payment intent
  - `verify_payment(payment_intent_id, signature)` → verification result
  - `process_refund(order_id, amount, reason)` → refund confirmation

### 2.3 Search & Indexing MCP (`mcp-search`)

- **Purpose:** Maintains search index, performs semantic product search, handles faceted filtering
- **Domain:** Information retrieval, NLP
- **Dependencies:** Elasticsearch / pgvector, products table
- **Tools exposed:**
  - `index_product(product_data)` → index status
  - `semantic_search(query, filters, limit)` → ranked product list
  - `reindex_catalogue()` → full reindex trigger

### 2.4 Notification MCP (`mcp-notifications`)

- **Purpose:** Sends personalised emails, SMS, and push notifications at lifecycle events
- **Domain:** Customer communication
- **Dependencies:** SendGrid / AWS SES, Firebase FCM, users table
- **Tools exposed:**
  - `send_order_confirmation(order_id, user_id)` → delivery status
  - `send_shipping_update(order_id, tracking_info)` → delivery status
  - `send_promotional_email(segment_id, template_id)` → send report

### 2.5 Analytics MCP (`mcp-analytics`)

- **Purpose:** Generates AI-powered business insights from sales and user behaviour data
- **Domain:** Business intelligence, data science
- **Dependencies:** Orders table, products table, BI database
- **Tools exposed:**
  - `get_sales_summary(date_from, date_to)` → revenue metrics
  - `get_top_products(limit, metric)` → product performance
  - `detect_anomalies(metric, window_days)` → anomaly report

### 2.6 Content Generation MCP (`mcp-content`)

- **Purpose:** Generates product descriptions, SEO metadata, and marketing copy
- **Domain:** Content management, SEO
- **Dependencies:** Anthropic Claude API, products table
- **Tools exposed:**
  - `generate_product_description(product_data)` → SEO description
  - `generate_meta_tags(product_data)` → SEO title + description
  - `generate_category_content(category_data)` → landing page copy

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  (Vite + Tailwind + Zustand + TanStack Query)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTTP / REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Port 8000)                   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ /api/v1/     │  │ MCP Client   │  │  SQLAlchemy ORM    │   │
│  │ endpoints    │→ │ (httpx async)│  │  (AsyncSession)    │   │
│  └──────────────┘  └──────┬───────┘  └────────┬───────────┘   │
└─────────────────────────── │ ─────────────────│───────────────┘
                             │                  │
           ┌─────────────────┼──────────────────┘
           │                 │                        PostgreSQL 18
           ▼                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                    MCP Server Layer                           │
  │                                                              │
  │  mcp-inventory  mcp-payments  mcp-search  mcp-notifications  │
  │  mcp-analytics  mcp-content                                  │
  └──────────────────────────────────────────────────────────────┘
```

### Communication Protocol

MCP servers in ShopWave use **HTTP/SSE transport** (Server-Sent Events):
- FastAPI backend acts as **MCP Client** — it calls MCP servers via `httpx`
- Each MCP server exposes a `/sse` endpoint for streaming and a `/messages` endpoint for tool calls
- Authentication: shared API key in `X-MCP-API-Key` header

---

## 4. Implementation Roadmap

---

### Phase 1 — Core Infrastructure

**Goal:** Create the MCP client utility that all FastAPI services will use to call MCP servers.

#### Step 1.1 — Install MCP Python SDK

Add to `backend/pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "mcp>=1.0.0",          # Anthropic MCP Python SDK — client + server utilities
    "httpx-sse>=0.4.0",    # SSE support for httpx — required for MCP streaming transport
]
```

#### Step 1.2 — MCP Client Utility

Create `backend/app/utils/mcp_client.py`:

```python
# app/utils/mcp_client.py
# ─────────────────────────────────────────────────────────────────────────────
# Reusable async MCP client used by all FastAPI service layers.
# Each MCP server gets its own base URL from settings; this client handles
# authentication headers, JSON serialisation, and error mapping.
# ─────────────────────────────────────────────────────────────────────────────

import httpx
from typing import Any
from app.core.config import settings


class MCPClient:
    """
    Thin async wrapper around httpx for calling MCP tool endpoints.

    WHY httpx?  It natively supports async/await and HTTP/2, matching
    our async FastAPI + asyncpg stack without blocking the event loop.
    """

    def __init__(self, base_url: str, api_key: str | None = None):
        # Store the MCP server base URL (e.g. "http://mcp-inventory:8001")
        self.base_url = base_url.rstrip("/")
        # API key is sent in X-MCP-API-Key header for server-to-server auth
        self._headers = {
            "Content-Type": "application/json",
            "X-MCP-API-Key": api_key or settings.MCP_INTERNAL_API_KEY,
        }

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Call a named tool on the MCP server and return its result.

        Args:
            tool_name:  The tool identifier (e.g. "check_stock_levels").
            arguments:  Dict of tool input parameters.
            timeout:    Request timeout in seconds — default 30s.

        Returns:
            The parsed JSON response from the MCP server tool.

        Raises:
            MCPToolError: If the server returns an error result.
            httpx.TimeoutException: If the server doesn't respond in time.
        """
        # MCP tool call request follows the JSON-RPC 2.0 style format
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout,
        ) as client:
            response = await client.post("/messages", json=payload)
            response.raise_for_status()   # Raises httpx.HTTPStatusError on 4xx/5xx
            data = response.json()

        # MCP protocol: check for error in response (RPC-level error, not HTTP error)
        if "error" in data:
            raise MCPToolError(
                tool=tool_name,
                code=data["error"].get("code"),
                message=data["error"].get("message", "Unknown MCP error"),
            )

        # Result is nested under data.result.content[0].text for text tool results
        return data.get("result", {})


class MCPToolError(Exception):
    """Raised when an MCP tool call returns an error response."""
    def __init__(self, tool: str, code: int | None, message: str):
        self.tool = tool
        self.code = code
        self.message = message
        super().__init__(f"MCP tool '{tool}' failed [{code}]: {message}")


# ── Pre-configured clients for each MCP server ────────────────────────────────
# These singletons are imported directly in service layers.
# URLs resolve via Docker Compose internal DNS.

inventory_mcp  = MCPClient(base_url="http://mcp-inventory:8001")
payments_mcp   = MCPClient(base_url="http://mcp-payments:8002")
search_mcp     = MCPClient(base_url="http://mcp-search:8003")
notify_mcp     = MCPClient(base_url="http://mcp-notifications:8004")
analytics_mcp  = MCPClient(base_url="http://mcp-analytics:8005")
content_mcp    = MCPClient(base_url="http://mcp-content:8006")
```

#### Step 1.3 — Add MCP Settings

Extend `backend/app/core/config.py`:

```python
# Add these fields to the Settings class

# MCP
MCP_INTERNAL_API_KEY: str = "mcp-internal-secret"  # Shared secret between backend and MCP servers

# MCP Server URLs (override in docker-compose for each service)
MCP_INVENTORY_URL:     str = "http://mcp-inventory:8001"
MCP_PAYMENTS_URL:      str = "http://mcp-payments:8002"
MCP_SEARCH_URL:        str = "http://mcp-search:8003"
MCP_NOTIFICATIONS_URL: str = "http://mcp-notifications:8004"
MCP_ANALYTICS_URL:     str = "http://mcp-analytics:8005"
MCP_CONTENT_URL:       str = "http://mcp-content:8006"
```

---

### Phase 2 — Inventory & Catalogue MCP

**Goal:** Build `mcp-inventory` — a standalone FastAPI+MCP server that manages stock intelligence.

#### Step 2.1 — Directory Structure

```
mcp-servers/
└── inventory/
    ├── server.py          ← MCP server entry point
    ├── tools/
    │   ├── stock.py       ← check_stock_levels, suggest_reorder tools
    │   └── bulk.py        ← bulk_update_stock tool
    ├── pyproject.toml
    └── Dockerfile
```

#### Step 2.2 — MCP Inventory Server

Create `mcp-servers/inventory/server.py`:

```python
# mcp-servers/inventory/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP server for inventory management.
# Uses FastMCP (the high-level MCP server framework) to define tools.
# Each @mcp.tool() decorated function becomes a callable MCP tool.
# ─────────────────────────────────────────────────────────────────────────────

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import Any
import asyncpg   # Direct asyncpg for this lightweight server (no SQLAlchemy needed)
import os

# FastMCP creates an MCP-compliant server with SSE transport automatically
mcp = FastMCP(
    name="shopwave-inventory",
    description="Stock level monitoring and reorder intelligence for ShopWave",
)

# Database connection string — injected via Docker Compose environment
DB_URL = os.environ["DATABASE_URL"]


async def get_db_conn():
    """
    Create a direct asyncpg connection.
    MCP servers use raw asyncpg for simplicity — no ORM overhead needed.
    """
    return await asyncpg.connect(DB_URL)


# ── Tool: check_stock_levels ──────────────────────────────────────────────────

class StockCheckInput(BaseModel):
    product_ids: list[str]   # List of UUID strings


@mcp.tool()
async def check_stock_levels(product_ids: list[str]) -> dict[str, Any]:
    """
    Check current stock quantities for a list of products.

    WHY this is an MCP tool and not a plain API:
    Future versions can use Claude to REASON about the stock data —
    e.g., flag products trending toward stockout based on recent order velocity.

    Args:
        product_ids: List of product UUIDs to check.

    Returns:
        Dict mapping product_id → { stock_quantity, status, product_name }
    """
    conn = await get_db_conn()
    try:
        # Parameterised query prevents SQL injection ($1 = ANY(...) pattern)
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
            """,
            product_ids,
        )
        return {
            "stock_levels": [dict(r) for r in rows],
            "checked_count": len(rows),
        }
    finally:
        await conn.close()


# ── Tool: suggest_reorder ─────────────────────────────────────────────────────

@mcp.tool()
async def suggest_reorder(product_id: str, lead_time_days: int = 7) -> dict[str, Any]:
    """
    AI-powered reorder suggestion for a product.

    Uses recent order velocity (units sold / day over last 30 days) to project
    stock depletion date and recommend reorder quantity.

    Args:
        product_id:     UUID of the product to analyse.
        lead_time_days: Supplier lead time — how many days until stock arrives.

    Returns:
        Reorder recommendation with suggested quantity and urgency level.
    """
    conn = await get_db_conn()
    try:
        # Fetch current stock
        product = await conn.fetchrow(
            "SELECT name, stock_quantity FROM products WHERE id = $1::uuid",
            product_id,
        )
        if not product:
            return {"error": "Product not found", "product_id": product_id}

        # Calculate average daily sales velocity over last 30 days
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

        # Project days until stockout at current sales rate
        days_until_stockout = (stock / daily_velocity) if daily_velocity > 0 else 999

        # If stockout will happen before new stock arrives, flag as urgent
        urgency = "urgent" if days_until_stockout < lead_time_days else (
            "recommended" if days_until_stockout < lead_time_days * 2 else "optional"
        )

        # Suggest 30-day supply as reorder quantity
        suggested_qty = max(int(daily_velocity * 30), 10)

        return {
            "product_id": product_id,
            "product_name": product["name"],
            "current_stock": stock,
            "daily_velocity": round(daily_velocity, 2),
            "days_until_stockout": round(days_until_stockout, 1),
            "urgency": urgency,
            "suggested_reorder_quantity": suggested_qty,
            "lead_time_days": lead_time_days,
        }
    finally:
        await conn.close()


# ── Tool: bulk_update_stock ───────────────────────────────────────────────────

@mcp.tool()
async def bulk_update_stock(updates: list[dict]) -> dict[str, Any]:
    """
    Batch update stock quantities for multiple products.

    Args:
        updates: List of { product_id: str, quantity_delta: int } dicts.
                 Positive delta = stock received. Negative delta = manual adjustment.

    Returns:
        Summary of updated products and any failures.
    """
    conn = await get_db_conn()
    updated, failed = [], []
    try:
        async with conn.transaction():   # All updates succeed or all roll back
            for update in updates:
                pid = update["product_id"]
                delta = update["quantity_delta"]
                try:
                    result = await conn.fetchrow(
                        """
                        UPDATE products
                        SET stock_quantity = GREATEST(0, stock_quantity + $1),
                            updated_at = NOW()
                        WHERE id = $2::uuid
                        RETURNING id::text, name, stock_quantity
                        """,
                        delta, pid,
                    )
                    if result:
                        updated.append(dict(result))
                    else:
                        failed.append({"product_id": pid, "reason": "not_found"})
                except Exception as e:
                    failed.append({"product_id": pid, "reason": str(e)})
    finally:
        await conn.close()

    return {
        "updated": updated,
        "failed": failed,
        "updated_count": len(updated),
        "failed_count": len(failed),
    }


# ── Run the MCP server ────────────────────────────────────────────────────────
if __name__ == "__main__":
    # mcp.run() starts the SSE transport server on the configured host/port
    # PORT is set via Docker Compose environment variable
    import os
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
```

#### Step 2.3 — Integrate Inventory MCP into FastAPI

In `backend/app/api/v1/endpoints/products.py`, add a reorder check endpoint:

```python
# backend/app/api/v1/endpoints/products.py (addition)

from app.utils.mcp_client import inventory_mcp, MCPToolError
from app.core.dependencies import get_current_admin_user

@router.get("/{product_id}/reorder-suggestion")
async def get_reorder_suggestion(
    product_id: UUID,
    lead_time_days: int = 7,
    _admin=Depends(get_current_admin_user),   # Admin-only endpoint
):
    """
    Ask the inventory MCP server for an AI-powered reorder recommendation.

    WHY call MCP here instead of computing in-process?
    The MCP server can be upgraded to use Claude for more sophisticated
    reasoning (seasonal trends, supplier history) without changing this endpoint.
    """
    try:
        result = await inventory_mcp.call_tool(
            tool_name="suggest_reorder",
            arguments={
                "product_id": str(product_id),
                "lead_time_days": lead_time_days,
            },
        )
        return result
    except MCPToolError as e:
        raise HTTPException(status_code=502, detail=f"Inventory service error: {e.message}")
```

---

### Phase 3 — Payment Gateway MCP

**Goal:** Isolate payment logic behind `mcp-payments` so swapping providers (Razorpay ↔ Stripe) requires zero changes to FastAPI endpoints.

#### Step 3.1 — MCP Payments Server

Create `mcp-servers/payments/server.py`:

```python
# mcp-servers/payments/server.py

from mcp.server.fastmcp import FastMCP
import razorpay   # pip install razorpay
import os
import hmac, hashlib

mcp = FastMCP(name="shopwave-payments")

# Razorpay client — credentials injected via environment
rz_client = razorpay.Client(
    auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"])
)


@mcp.tool()
async def create_payment_intent(
    order_id: str,
    amount_paise: int,    # Razorpay works in the smallest currency unit (paise for INR)
    currency: str = "INR",
    receipt: str | None = None,
) -> dict:
    """
    Create a Razorpay order (equivalent to Stripe's PaymentIntent).

    Args:
        order_id:      ShopWave internal order UUID (stored as receipt for reconciliation).
        amount_paise:  Amount in paise (₹1 = 100 paise).
        currency:      ISO 4217 currency code.
        receipt:       Human-readable receipt ID for Razorpay dashboard.

    Returns:
        Razorpay order object including the order_id needed by the frontend SDK.
    """
    rz_order = rz_client.order.create({
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt or order_id,
        "notes": {"shopwave_order_id": order_id},
    })
    return {
        "razorpay_order_id": rz_order["id"],
        "amount": rz_order["amount"],
        "currency": rz_order["currency"],
        "status": rz_order["status"],
        "shopwave_order_id": order_id,
    }


@mcp.tool()
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> dict:
    """
    Verify a payment's HMAC signature to confirm it came from Razorpay.

    WHY signature verification?
    The frontend receives the payment result and sends it to our backend.
    Without verification, a malicious client could fake a successful payment.

    Args:
        razorpay_order_id:   From the Razorpay SDK callback.
        razorpay_payment_id: Payment ID from Razorpay.
        razorpay_signature:  HMAC-SHA256 signature from Razorpay.

    Returns:
        { verified: bool, payment_id: str }
    """
    # Construct the message Razorpay signed: "order_id|payment_id"
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    secret = os.environ["RAZORPAY_KEY_SECRET"].encode()

    expected_signature = hmac.new(
        secret, message.encode(), hashlib.sha256
    ).hexdigest()

    # Constant-time comparison prevents timing attacks
    verified = hmac.compare_digest(expected_signature, razorpay_signature)

    return {
        "verified": verified,
        "payment_id": razorpay_payment_id if verified else None,
    }


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
```

#### Step 3.2 — Integrate Payments MCP into Orders Endpoint

```python
# backend/app/api/v1/endpoints/orders.py (addition)

from app.utils.mcp_client import payments_mcp

@router.post("/{order_id}/payment-intent")
async def create_payment_intent(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a payment intent for an existing order.
    The frontend uses the returned razorpay_order_id to open the Razorpay payment modal.
    """
    result = await db.execute(select(Order).where(
        Order.id == order_id, Order.user_id == current_user.id
    ))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Convert decimal total to paise (₹ × 100)
    amount_paise = int(order.total_amount * 100)

    try:
        intent = await payments_mcp.call_tool(
            "create_payment_intent",
            {
                "order_id": str(order_id),
                "amount_paise": amount_paise,
                "currency": "INR",
            },
        )
        return intent
    except MCPToolError as e:
        raise HTTPException(status_code=502, detail=f"Payment service error: {e.message}")


@router.post("/{order_id}/verify-payment")
async def verify_payment(
    order_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Verify a Razorpay payment signature after the user completes payment in the modal.
    On success, update order.payment_status = 'paid'.
    """
    result = await payments_mcp.call_tool(
        "verify_payment",
        {
            "razorpay_order_id":  body["razorpay_order_id"],
            "razorpay_payment_id": body["razorpay_payment_id"],
            "razorpay_signature":  body["razorpay_signature"],
        },
    )

    if not result.get("verified"):
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Update order payment status in our database
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.payment_status = "paid"
        order.payment_intent_id = result["payment_id"]
        order.status = "confirmed"
        await db.commit()

    return {"message": "Payment verified", "order_status": "confirmed"}
```

---

### Phase 4 — Search & Indexing MCP

**Goal:** Replace basic SQL ILIKE search with semantic vector search via `mcp-search`.

#### Step 4.1 — MCP Search Server

Create `mcp-servers/search/server.py`:

```python
# mcp-servers/search/server.py
# Uses PostgreSQL 18's built-in pgvector for semantic search.
# pgvector stores 1536-dimensional OpenAI / Anthropic embeddings.

from mcp.server.fastmcp import FastMCP
import asyncpg
import httpx
import os
import json

mcp = FastMCP(name="shopwave-search")
DB_URL = os.environ["DATABASE_URL"]


async def get_embedding(text: str) -> list[float]:
    """
    Call Anthropic's embedding endpoint to get a vector representation of text.

    WHY embeddings?  Unlike keyword search, embeddings capture semantic meaning.
    "smartphone" and "mobile phone" return similar vectors, improving search recall.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/embeddings",
            headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "voyage-3",      # Anthropic's embedding model
                "input": text,
                "input_type": "query",
            },
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]["embedding"]


@mcp.tool()
async def semantic_search(
    query: str,
    limit: int = 20,
    category_id: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict:
    """
    Perform semantic product search using pgvector cosine similarity.

    The product name + description are embedded at indexing time and stored
    in the products.embedding column (vector(1536)).
    At search time, the query is embedded and compared against stored vectors.

    Args:
        query:       Natural language search query.
        limit:       Maximum number of results.
        category_id: Optional category UUID filter.
        min_price:   Optional minimum price filter.
        max_price:   Optional maximum price filter.

    Returns:
        List of products ranked by semantic similarity.
    """
    # Get the embedding vector for the search query
    query_embedding = await get_embedding(query)
    embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

    conn = await asyncpg.connect(DB_URL)
    try:
        # Build dynamic WHERE clause for optional filters
        conditions = ["p.is_active = true"]
        params: list = [embedding_str, limit]
        param_idx = 3

        if category_id:
            conditions.append(f"p.category_id = ${param_idx}::uuid")
            params.append(category_id)
            param_idx += 1
        if min_price is not None:
            conditions.append(f"p.price >= ${param_idx}")
            params.append(min_price)
            param_idx += 1
        if max_price is not None:
            conditions.append(f"p.price <= ${param_idx}")
            params.append(max_price)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        # <=> is the pgvector cosine distance operator
        # ORDER BY distance ASC = most similar first
        rows = await conn.fetch(
            f"""
            SELECT p.id::text, p.name, p.slug, p.price::text, p.image_url,
                   p.stock_quantity,
                   1 - (p.embedding <=> $1::vector) AS similarity_score
            FROM products p
            WHERE {where_clause}
            ORDER BY p.embedding <=> $1::vector
            LIMIT $2
            """,
            *params[:2], *params[2:],
        )
        return {
            "query": query,
            "results": [dict(r) for r in rows],
            "count": len(rows),
        }
    finally:
        await conn.close()


@mcp.tool()
async def index_product(product_id: str) -> dict:
    """
    Generate and store an embedding for a product.
    Called automatically when a product is created or updated.

    Args:
        product_id: UUID of the product to index.

    Returns:
        { indexed: bool, product_id: str }
    """
    conn = await asyncpg.connect(DB_URL)
    try:
        product = await conn.fetchrow(
            "SELECT id::text, name, description FROM products WHERE id = $1::uuid",
            product_id,
        )
        if not product:
            return {"indexed": False, "reason": "product_not_found"}

        # Combine name + description for a richer embedding
        text_to_embed = f"{product['name']}. {product['description'] or ''}"
        embedding = await get_embedding(text_to_embed)
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"

        await conn.execute(
            "UPDATE products SET embedding = $1::vector WHERE id = $2::uuid",
            embedding_str, product_id,
        )
        return {"indexed": True, "product_id": product_id}
    finally:
        await conn.close()


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8003)))
```

---

### Phase 5 — Notification MCP

**Goal:** Send AI-personalised transactional emails at order lifecycle events.

#### Step 5.1 — MCP Notifications Server

Create `mcp-servers/notifications/server.py`:

```python
# mcp-servers/notifications/server.py

from mcp.server.fastmcp import FastMCP
import httpx
import os

mcp = FastMCP(name="shopwave-notifications")

SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
FROM_EMAIL = "noreply@shopwave.com"


async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email via SendGrid's transactional API.
    Returns True on success, False on failure.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": FROM_EMAIL, "name": "ShopWave"},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_body}],
            },
        )
        return response.status_code == 202


@mcp.tool()
async def send_order_confirmation(
    user_email: str,
    user_name: str,
    order_id: str,
    order_total: str,
    items: list[dict],
) -> dict:
    """
    Send an order confirmation email.

    WHY MCP for emails?
    Future versions can use Claude to personalise the email body based on the
    user's purchase history and browsing patterns — without changing this interface.

    Args:
        user_email:  Customer's email address.
        user_name:   Customer's name for personalisation.
        order_id:    ShopWave order UUID (shortened for display).
        order_total: Formatted total amount string (e.g. "₹1,234.00").
        items:       List of { name, quantity, price } dicts.

    Returns:
        { sent: bool, recipient: str }
    """
    # Build items HTML table
    items_html = "".join(
        f"<tr><td>{i['name']}</td><td>×{i['quantity']}</td><td>₹{i['price']}</td></tr>"
        for i in items
    )

    html_body = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto;padding:24px">
      <h1 style="color:#2563eb">Thank you, {user_name}!</h1>
      <p>Your order <strong>#{order_id[:8].upper()}</strong> has been confirmed.</p>
      <table width="100%" cellpadding="8" style="border-collapse:collapse;margin:16px 0">
        <thead><tr style="background:#f3f4f6">
          <th align="left">Product</th><th align="left">Qty</th><th align="left">Price</th>
        </tr></thead>
        <tbody>{items_html}</tbody>
      </table>
      <p><strong>Total: {order_total}</strong></p>
      <p style="color:#6b7280;font-size:14px">
        Track your order at <a href="https://shopwave.com/orders">shopwave.com/orders</a>
      </p>
    </div>
    """

    sent = await send_email(
        to_email=user_email,
        subject=f"Order Confirmed — #{order_id[:8].upper()} | ShopWave",
        html_body=html_body,
    )
    return {"sent": sent, "recipient": user_email}


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8004)))
```

---

### Phase 6 — Analytics MCP

**Goal:** Expose AI-readable business metrics for admin dashboards and automated reporting.

#### Step 6.1 — MCP Analytics Server

Create `mcp-servers/analytics/server.py`:

```python
# mcp-servers/analytics/server.py

from mcp.server.fastmcp import FastMCP
import asyncpg
import os
from datetime import date

mcp = FastMCP(name="shopwave-analytics")
DB_URL = os.environ["DATABASE_URL"]


@mcp.tool()
async def get_sales_summary(date_from: str, date_to: str) -> dict:
    """
    Return aggregated revenue and order metrics for a date range.

    Args:
        date_from: ISO date string "YYYY-MM-DD" (inclusive)
        date_to:   ISO date string "YYYY-MM-DD" (inclusive)

    Returns:
        { total_revenue, order_count, avg_order_value, unique_customers }
    """
    conn = await asyncpg.connect(DB_URL)
    try:
        row = await conn.fetchrow(
            """
            SELECT
                COALESCE(SUM(total_amount), 0)::float        AS total_revenue,
                COUNT(*)                                      AS order_count,
                COALESCE(AVG(total_amount), 0)::float        AS avg_order_value,
                COUNT(DISTINCT user_id)                       AS unique_customers
            FROM orders
            WHERE created_at::date BETWEEN $1 AND $2
              AND status NOT IN ('cancelled', 'refunded')
            """,
            date_from, date_to,
        )
        return dict(row)
    finally:
        await conn.close()


@mcp.tool()
async def get_top_products(limit: int = 10, metric: str = "revenue") -> dict:
    """
    Return top-performing products by revenue or quantity sold.

    Args:
        limit:  Number of products to return.
        metric: "revenue" | "quantity" — ranking metric.

    Returns:
        List of { product_id, name, total_revenue, total_quantity_sold }
    """
    order_col = "SUM(oi.line_total)" if metric == "revenue" else "SUM(oi.quantity)"
    conn = await asyncpg.connect(DB_URL)
    try:
        rows = await conn.fetch(
            f"""
            SELECT
                p.id::text AS product_id,
                p.name,
                SUM(oi.line_total)::float   AS total_revenue,
                SUM(oi.quantity)            AS total_quantity_sold
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status NOT IN ('cancelled', 'refunded')
            GROUP BY p.id, p.name
            ORDER BY {order_col} DESC
            LIMIT $1
            """,
            limit,
        )
        return {"top_products": [dict(r) for r in rows], "metric": metric}
    finally:
        await conn.close()


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8005)))
```

---

### Phase 7 — React Frontend Integration

**Goal:** Wire MCP-backed API endpoints into the React frontend.

#### Step 7.1 — Semantic Search Hook

Create `frontend/src/hooks/useSemanticSearch.js`:

```javascript
// src/hooks/useSemanticSearch.js
// ─────────────────────────────────────────────────────────────────────────────
// Custom hook that calls our FastAPI endpoint which in turn calls mcp-search.
// The MCP layer is transparent to the frontend — it just sees a REST endpoint.
// ─────────────────────────────────────────────────────────────────────────────

import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'

export function useSemanticSearch({ query, categoryId, minPrice, maxPrice, enabled = true }) {
  return useQuery({
    // Query key includes all filter params — refetches automatically when any change
    queryKey: ['semantic-search', query, categoryId, minPrice, maxPrice],

    queryFn: async () => {
      if (!query?.trim()) return { results: [], count: 0 }

      const params = new URLSearchParams({ query, limit: 20 })
      if (categoryId) params.append('category_id', categoryId)
      if (minPrice != null) params.append('min_price', minPrice)
      if (maxPrice != null) params.append('max_price', maxPrice)

      // This FastAPI endpoint delegates to mcp-search via MCPClient.call_tool()
      const { data } = await api.get(`/api/v1/products/search?${params}`)
      return data
    },

    enabled: enabled && Boolean(query?.trim()),
    staleTime: 1000 * 30,   // Cache search results for 30 seconds
  })
}
```

#### Step 7.2 — Payment Flow Component

Create `frontend/src/components/features/PaymentModal.jsx`:

```jsx
// src/components/features/PaymentModal.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Razorpay payment modal triggered after order creation.
// Flow:
//   1. POST /orders/:id/payment-intent → gets razorpay_order_id (via mcp-payments)
//   2. Open Razorpay JS SDK modal with the order_id
//   3. On success, POST /orders/:id/verify-payment (mcp-payments verifies signature)
//   4. Show success / redirect to /orders
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

export default function PaymentModal({ orderId, totalAmount, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handlePayment() {
    setLoading(true)
    try {
      // Step 1: Create payment intent via mcp-payments (through FastAPI)
      const { data: intent } = await api.post(`/api/v1/orders/${orderId}/payment-intent`)

      // Step 2: Load Razorpay SDK (loaded via CDN in index.html) and open modal
      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID,
        amount: intent.amount,
        currency: intent.currency,
        order_id: intent.razorpay_order_id,
        name: 'ShopWave',
        description: `Order #${orderId.slice(0, 8).toUpperCase()}`,
        handler: async (response) => {
          // Step 3: Verify payment signature via mcp-payments
          try {
            await api.post(`/api/v1/orders/${orderId}/verify-payment`, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            })
            toast.success('Payment successful! 🎉')
            onSuccess?.()
            navigate('/orders')
          } catch {
            toast.error('Payment verification failed. Contact support.')
          }
        },
        prefill: {},   // Pre-fill from user store in production
        theme: { color: '#2563eb' },
      }

      // window.Razorpay is available because we load the Razorpay JS SDK in index.html
      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Could not initiate payment')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handlePayment}
      disabled={loading}
      className="btn-primary w-full"
    >
      {loading ? 'Preparing payment...' : `Pay ₹${parseFloat(totalAmount).toFixed(2)}`}
    </button>
  )
}
```

---

## 5. Data Flow Reference

### Order Placement with MCP Integration

```
User clicks "Place Order"
        │
        ▼
Frontend POST /api/v1/orders/
        │
        ▼
FastAPI orders.create_order()
  ├── Validate cart items (SQLAlchemy SELECT products)
  ├── Decrement stock (SQLAlchemy UPDATE products)
  ├── INSERT order + order_items (SQLAlchemy)
  ├── inventory_mcp.call_tool("bulk_update_stock")   ← sync MCP call
  └── notify_mcp.call_tool("send_order_confirmation") ← async fire-and-forget
        │
        ▼
Return Order to Frontend
        │
        ▼
Frontend renders PaymentModal
        │
        ▼
payments_mcp.call_tool("create_payment_intent")
        │
        ▼
Razorpay Modal opens
        │
        ▼
payments_mcp.call_tool("verify_payment")
        │
        ▼
Order status → "confirmed"
```

---

## 6. Testing MCP Servers

### Unit test for inventory MCP tool

Create `mcp-servers/inventory/tests/test_stock.py`:

```python
# mcp-servers/inventory/tests/test_stock.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_check_stock_levels_returns_correct_statuses():
    """
    Verify that check_stock_levels correctly maps quantity thresholds to status strings.

    WHY mock asyncpg?  Unit tests should not hit a real database.
    We mock the DB call to control what 'check_stock_levels' receives.
    """
    mock_rows = [
        {"id": "uuid-1", "name": "Widget A", "stock_quantity": 0,  "status": "out_of_stock"},
        {"id": "uuid-2", "name": "Widget B", "stock_quantity": 5,  "status": "low_stock"},
        {"id": "uuid-3", "name": "Widget C", "stock_quantity": 100, "status": "in_stock"},
    ]

    with patch("asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        mock_connect.return_value = mock_conn

        from server import check_stock_levels
        result = await check_stock_levels(["uuid-1", "uuid-2", "uuid-3"])

    assert result["checked_count"] == 3
    statuses = {r["id"]: r["status"] for r in result["stock_levels"]}
    assert statuses["uuid-1"] == "out_of_stock"
    assert statuses["uuid-2"] == "low_stock"
    assert statuses["uuid-3"] == "in_stock"


@pytest.mark.asyncio
async def test_suggest_reorder_flags_urgent_when_velocity_high():
    """
    Verify that urgency=urgent is set when stock will run out before lead time.
    """
    with patch("asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        mock_conn = AsyncMock()
        # Product has 5 units; daily velocity = 2 units/day → 2.5 days until stockout
        # Lead time = 7 days → should be URGENT
        mock_conn.fetchrow.return_value = {"name": "Fast Mover", "stock_quantity": 5}
        mock_conn.fetchval.return_value = 2.0   # 2 units/day average
        mock_connect.return_value = mock_conn

        from server import suggest_reorder
        result = await suggest_reorder("some-uuid", lead_time_days=7)

    assert result["urgency"] == "urgent"
    assert result["days_until_stockout"] < 7
```

---

## 7. Production Checklist

Before deploying MCP servers to production, verify each item:

### Security
- [ ] `MCP_INTERNAL_API_KEY` is a cryptographically random 32-byte hex string
- [ ] MCP servers are NOT exposed on public ports (internal Docker network only)
- [ ] Payment keys (`RAZORPAY_KEY_SECRET`) are stored in Docker secrets, not env vars
- [ ] `ANTHROPIC_API_KEY` has usage limits set in the Anthropic console

### Reliability
- [ ] Each MCP server has a `HEALTHCHECK` in its Dockerfile
- [ ] FastAPI endpoints catch `MCPToolError` and return `HTTP 502` with a user-friendly message
- [ ] MCP clients have `timeout=30.0` set (prevents hanging requests)
- [ ] Retry logic added to `MCPClient.call_tool()` for transient network errors

### Performance
- [ ] `mcp-search` has a connection pool (not a new connection per request)
- [ ] Product embeddings are pre-generated at write time, not at search time
- [ ] `mcp-analytics` queries have appropriate indexes (`created_at`, `status`)

### Observability
- [ ] Structured logging added to each MCP server (JSON format for log aggregation)
- [ ] OpenTelemetry traces span both FastAPI → MCPClient → MCP server calls
- [ ] Alerts configured for MCP server health check failures

### docker-compose MCP extensions
```yaml
# Add to docker-compose.yml services section:

  mcp-inventory:
    build: ./mcp-servers/inventory
    container_name: shopwave_mcp_inventory
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://shopwave:shopwave_pass@db:5432/shopwave_db
      PORT: 8001
    depends_on:
      db:
        condition: service_healthy
    networks:
      - shopwave_net
    # No ports: exposed — internal only, not accessible from host

  mcp-payments:
    build: ./mcp-servers/payments
    container_name: shopwave_mcp_payments
    restart: unless-stopped
    environment:
      RAZORPAY_KEY_ID: ${RAZORPAY_KEY_ID}
      RAZORPAY_KEY_SECRET: ${RAZORPAY_KEY_SECRET}
      PORT: 8002
    networks:
      - shopwave_net

  mcp-search:
    build: ./mcp-servers/search
    container_name: shopwave_mcp_search
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://shopwave:shopwave_pass@db:5432/shopwave_db
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      PORT: 8003
    depends_on:
      db:
        condition: service_healthy
    networks:
      - shopwave_net

  mcp-notifications:
    build: ./mcp-servers/notifications
    container_name: shopwave_mcp_notifications
    restart: unless-stopped
    environment:
      SENDGRID_API_KEY: ${SENDGRID_API_KEY}
      PORT: 8004
    networks:
      - shopwave_net

  mcp-analytics:
    build: ./mcp-servers/analytics
    container_name: shopwave_mcp_analytics
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://shopwave:shopwave_pass@db:5432/shopwave_db
      PORT: 8005
    depends_on:
      db:
        condition: service_healthy
    networks:
      - shopwave_net
```

---

*End of ShopWave MCP Implementation Sequence Guide.*
*For questions, open an issue at github.com/your-org/shopwave.*
