# mcp-servers/notifications/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Notifications Server — transactional email via SendGrid.
# Future: swap for AWS SES or upgrade to Claude-generated personalised copy.
# ─────────────────────────────────────────────────────────────────────────────

import os
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="shopwave-notifications", description="Transactional email delivery")

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL       = os.environ.get("FROM_EMAIL", "noreply@shopwave.com")
FROM_NAME        = "ShopWave"


async def _send_email(to_email: str, subject: str, html: str) -> bool:
    """Send a single transactional email via SendGrid v3 API. Returns True on success."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": FROM_EMAIL, "name": FROM_NAME},
                "subject": subject,
                "content": [{"type": "text/html", "value": html}],
            },
        )
        return resp.status_code == 202


@mcp.tool()
async def send_order_confirmation(
    user_email: str,
    user_name: str,
    order_id: str,
    order_total: str,
    items: list[dict],
) -> dict[str, Any]:
    """
    Send order confirmation email after successful order placement.

    Args:
        user_email:  Recipient email address.
        user_name:   First name used for greeting personalisation.
        order_id:    ShopWave UUID (shortened for display).
        order_total: Pre-formatted total string (e.g. "₹1,234.00").
        items:       List of { name, quantity, unit_price } line items.
    """
    rows_html = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #f3f4f6'>{i['name']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #f3f4f6;text-align:center'>×{i['quantity']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #f3f4f6;text-align:right'>₹{i.get('unit_price','')}</td></tr>"
        for i in items
    )
    order_short = order_id[:8].upper()

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:auto;padding:32px;color:#111">
      <div style="text-align:center;margin-bottom:28px">
        <span style="font-size:28px;font-weight:700;color:#2563eb">ShopWave</span>
      </div>
      <h2 style="font-weight:600;margin-bottom:4px">Hey {user_name}, your order is confirmed! 🎉</h2>
      <p style="color:#6b7280;margin-top:0">Order reference: <strong>#{order_short}</strong></p>

      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;margin:24px 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
        <thead>
          <tr style="background:#f9fafb">
            <th style="padding:10px 8px;text-align:left;font-size:12px;color:#6b7280;font-weight:600">ITEM</th>
            <th style="padding:10px 8px;text-align:center;font-size:12px;color:#6b7280;font-weight:600">QTY</th>
            <th style="padding:10px 8px;text-align:right;font-size:12px;color:#6b7280;font-weight:600">PRICE</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
        <tfoot>
          <tr style="background:#f9fafb">
            <td colspan="2" style="padding:12px 8px;font-weight:700">Total</td>
            <td style="padding:12px 8px;text-align:right;font-weight:700;color:#2563eb">{order_total}</td>
          </tr>
        </tfoot>
      </table>

      <p style="font-size:14px;color:#6b7280">
        Track your order at
        <a href="https://shopwave.com/orders" style="color:#2563eb">shopwave.com/orders</a>
      </p>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0"/>
      <p style="font-size:12px;color:#9ca3af;text-align:center">© ShopWave. This is an automated email — please do not reply.</p>
    </div>
    """

    sent = await _send_email(
        to_email=user_email,
        subject=f"Order Confirmed #{order_short} — ShopWave",
        html=html,
    )
    return {"sent": sent, "recipient": user_email, "order_id": order_id}


@mcp.tool()
async def send_shipping_update(
    user_email: str,
    user_name: str,
    order_id: str,
    tracking_number: str,
    carrier: str,
    tracking_url: str | None = None,
) -> dict[str, Any]:
    """Send a shipping dispatch notification with tracking details."""
    order_short = order_id[:8].upper()
    track_link = f'<a href="{tracking_url}" style="color:#2563eb">Track Package</a>' if tracking_url else tracking_number

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:auto;padding:32px;color:#111">
      <span style="font-size:24px;font-weight:700;color:#2563eb">ShopWave</span>
      <h2 style="margin-top:24px">Your order is on its way, {user_name}! 🚚</h2>
      <p>Order <strong>#{order_short}</strong> has been shipped via <strong>{carrier}</strong>.</p>
      <p>Tracking: {track_link}</p>
    </div>
    """
    sent = await _send_email(user_email, f"Your ShopWave Order #{order_short} Has Shipped!", html)
    return {"sent": sent, "recipient": user_email}


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8004)))
