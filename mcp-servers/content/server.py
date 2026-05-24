# mcp-servers/content/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Content Server — uses Claude to generate product copy and SEO metadata.
# ─────────────────────────────────────────────────────────────────────────────

import os
import httpx
import json
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="shopwave-content", dependencies=["asyncpg"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-sonnet-4-20250514"


async def _claude(prompt: str, max_tokens: int = 1000) -> str:
    """Call Claude API and return the text content of the first message block."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


@mcp.tool()
async def generate_product_description(
    product_name: str,
    category: str,
    key_features: list[str],
    price: str,
    tone: str = "professional",
) -> dict[str, Any]:
    """
    Generate an SEO-optimised product description using Claude.

    Args:
        product_name:  Full product name.
        category:      Category path (e.g. "Electronics > Phones").
        key_features:  Bullet points of product attributes.
        price:         Formatted price string for context.
        tone:          "professional" | "casual" | "luxury"

    Returns:
        { short_description, long_description, bullet_points }
    """
    features_text = "\n".join(f"- {f}" for f in key_features)
    prompt = f"""
You are an e-commerce copywriter. Generate product content for ShopWave.

Product: {product_name}
Category: {category}
Price: {price}
Key features:
{features_text}

Tone: {tone}

Respond ONLY with a JSON object (no markdown) with these exact keys:
- "short_description": 1-2 sentence product summary (max 160 chars for SEO meta)
- "long_description": 3-4 paragraph detailed description with natural keyword usage
- "bullet_points": array of 4-6 concise feature bullets
"""
    raw = await _claude(prompt, max_tokens=800)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"long_description": raw, "short_description": "", "bullet_points": []}

    return result


@mcp.tool()
async def generate_meta_tags(
    product_name: str,
    short_description: str,
    category: str,
) -> dict[str, Any]:
    """
    Generate SEO title tag and meta description optimised for search engines.

    Returns title (max 60 chars) and meta_description (max 155 chars).
    """
    prompt = f"""
Generate SEO tags for this e-commerce product.
Product: {product_name}
Category: {category}
Description: {short_description}

Respond ONLY with JSON — no markdown:
{{"title": "...", "meta_description": "..."}}

Rules:
- title: 50-60 characters, include product name + 1 key benefit
- meta_description: 140-155 characters, action-oriented, include price signal
"""
    raw = await _claude(prompt, max_tokens=200)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": product_name, "meta_description": short_description[:155]}


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8006)))
