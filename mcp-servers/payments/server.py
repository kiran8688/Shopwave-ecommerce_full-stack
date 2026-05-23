# mcp-servers/payments/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Payments Server — abstracts Razorpay payment operations.
# Swapping to Stripe requires only changes here, not in FastAPI endpoints.
# ─────────────────────────────────────────────────────────────────────────────

import os
import hmac
import hashlib
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="shopwave-payments", description="Payment gateway abstraction layer")

# Razorpay credentials from environment — never hardcoded
RAZORPAY_KEY_ID     = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")


@mcp.tool()
async def create_payment_intent(
    order_id: str,
    amount_paise: int,
    currency: str = "INR",
) -> dict[str, Any]:
    """
    Create a Razorpay order object — equivalent to Stripe's PaymentIntent.

    Args:
        order_id:      ShopWave internal order UUID (used as receipt for reconciliation).
        amount_paise:  Total in smallest currency unit (paise for INR; ₹1 = 100 paise).
        currency:      ISO 4217 code — default INR.

    Returns:
        razorpay_order_id, amount, currency, status, shopwave_order_id
    """
    import razorpay  # lazy import — installed via pyproject.toml

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    rz_order = client.order.create({
        "amount":   amount_paise,
        "currency": currency,
        "receipt":  order_id,
        "notes":    {"shopwave_order_id": order_id},
    })

    return {
        "razorpay_order_id": rz_order["id"],
        "amount":             rz_order["amount"],
        "currency":           rz_order["currency"],
        "status":             rz_order["status"],
        "shopwave_order_id":  order_id,
    }


@mcp.tool()
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> dict[str, Any]:
    """
    Verify the HMAC-SHA256 signature Razorpay attaches to every payment callback.

    Without this verification step, a malicious client could send a fake
    "payment successful" payload and claim free goods.

    Args:
        razorpay_order_id:   From the Razorpay JS SDK success callback.
        razorpay_payment_id: Payment ID assigned by Razorpay.
        razorpay_signature:  HMAC provided by Razorpay in the callback.

    Returns:
        { verified: bool, payment_id: str | None }
    """
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    # hmac.compare_digest is constant-time — prevents timing side-channel attacks
    verified = hmac.compare_digest(expected, razorpay_signature)

    return {
        "verified":   verified,
        "payment_id": razorpay_payment_id if verified else None,
    }


@mcp.tool()
async def process_refund(
    payment_id: str,
    amount_paise: int | None = None,
    reason: str = "customer_request",
) -> dict[str, Any]:
    """
    Issue a full or partial refund via Razorpay.

    Args:
        payment_id:    Razorpay payment ID to refund.
        amount_paise:  Refund amount in paise. None = full refund.
        reason:        Reason string stored in Razorpay dashboard.

    Returns:
        { refund_id, amount, status }
    """
    import razorpay
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    payload: dict = {"speed": "normal", "notes": {"reason": reason}}
    if amount_paise is not None:
        payload["amount"] = amount_paise

    refund = client.payment.refund(payment_id, payload)

    return {
        "refund_id": refund["id"],
        "amount":    refund["amount"],
        "status":    refund["status"],
    }


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
