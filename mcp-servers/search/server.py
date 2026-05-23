# mcp-servers/search/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Search Server — semantic product search using pgvector + Anthropic embeddings.
# Requires PostgreSQL 18 with the pgvector extension installed.
# ─────────────────────────────────────────────────────────────────────────────

import os
import asyncpg
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="shopwave-search", dependencies=["asyncpg"])

DB_URL          = os.environ.get("DATABASE_URL", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


async def _get_embedding(text: str) -> list[float]:
    """
    Generate a 1024-dimensional embedding for `text` using Voyage-3.

    WHY embeddings?  Unlike ILIKE keyword search, embeddings capture semantic
    meaning — "phone" and "smartphone" produce nearby vectors, improving recall.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/embeddings",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={"model": "voyage-3", "input": text, "input_type": "query"},
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]["embedding"]


@mcp.tool()
async def semantic_search(
    query: str,
    limit: int = 20,
    category_id: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> dict[str, Any]:
    """
    Rank products by semantic similarity to the query string.

    Uses pgvector's <=> cosine distance operator to compare the query
    embedding against pre-computed product embeddings stored in products.embedding.

    Args:
        query:       Free-text search query (e.g. "waterproof running shoes").
        limit:       Max number of results to return (1-100).
        category_id: Optional UUID to restrict results to one category.
        min_price:   Lower price bound (INR).
        max_price:   Upper price bound (INR).
    """
    embedding = await _get_embedding(query)
    vec_str = f"[{','.join(str(x) for x in embedding)}]"

    conditions = ["p.is_active = true", "p.stock_quantity > 0"]
    params: list[Any] = [vec_str, limit]
    idx = 3

    if category_id:
        conditions.append(f"p.category_id = ${idx}::uuid")
        params.append(category_id); idx += 1
    if min_price is not None:
        conditions.append(f"p.price >= ${idx}")
        params.append(min_price); idx += 1
    if max_price is not None:
        conditions.append(f"p.price <= ${idx}")
        params.append(max_price); idx += 1

    where = " AND ".join(conditions)

    conn = await asyncpg.connect(DB_URL)
    try:
        rows = await conn.fetch(
            f"""
            SELECT p.id::text, p.name, p.slug, p.price::text,
                   p.image_url, p.stock_quantity,
                   1 - (p.embedding <=> $1::vector) AS similarity_score
            FROM products p
            WHERE {where}
            ORDER BY p.embedding <=> $1::vector
            LIMIT $2
            """,
            *params,
        )
        return {"query": query, "results": [dict(r) for r in rows], "count": len(rows)}
    finally:
        await conn.close()


@mcp.tool()
async def index_product(product_id: str) -> dict[str, Any]:
    """
    Compute and persist the embedding for a single product.
    Call this after every CREATE or UPDATE to products table.

    Combines name + description into one text blob for a richer vector.
    """
    conn = await asyncpg.connect(DB_URL)
    try:
        row = await conn.fetchrow(
            "SELECT id::text, name, description FROM products WHERE id = $1::uuid",
            product_id,
        )
        if not row:
            return {"indexed": False, "reason": "product_not_found"}

        text = f"{row['name']}. {row['description'] or ''}"
        embedding = await _get_embedding(text)
        vec_str = f"[{','.join(str(x) for x in embedding)}]"

        await conn.execute(
            "UPDATE products SET embedding = $1::vector WHERE id = $2::uuid",
            vec_str, product_id,
        )
        return {"indexed": True, "product_id": product_id}
    finally:
        await conn.close()


@mcp.tool()
async def reindex_catalogue() -> dict[str, Any]:
    """
    Re-embed every active product. Run after bulk imports or embedding model changes.
    May take several minutes depending on catalogue size.
    """
    conn = await asyncpg.connect(DB_URL)
    try:
        rows = await conn.fetch("SELECT id::text, name, description FROM products WHERE is_active = true")
    finally:
        await conn.close()

    success, errors = 0, 0
    for row in rows:
        try:
            await index_product(row["id"])
            success += 1
        except Exception:
            errors += 1

    return {"reindexed": success, "errors": errors, "total": len(rows)}


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8003)))
