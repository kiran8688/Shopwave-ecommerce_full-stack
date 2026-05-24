# app/api/v1/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.order import Order

router = APIRouter()


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payments_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Asynchronously processes payments callback webhooks (e.g. Razorpay webhook order.paid, payment.captured, etc.).
    If verified, automatically fetches the order row, marks payment_status = "paid",
    order.status = "confirmed", and saves the transaction changes.
    """
    # Extract razorpay_order_id from payload
    # Check standard Razorpay nested structure
    razorpay_order_id = (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
        .get("order_id")
    )
    # Check flat structures as a fallback
    if not razorpay_order_id:
        razorpay_order_id = payload.get("razorpay_order_id") or payload.get("order_id")

    if not razorpay_order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract razorpay_order_id or order_id from payload",
        )

    # Query for the matching Order using parameterization/prepared statement
    result = await db.execute(
        select(Order).where(Order.payment_intent_id == razorpay_order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matching Order not found",
        )

    # Automatically mark payment_status = "paid" and order.status = "confirmed"
    order.status = "confirmed"
    order.payment_status = "paid"
    await db.commit()

    return {"status": "success"}
