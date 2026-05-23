# app/api/v1/endpoints/orders.py
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.schemas.order import OrderCreate

from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.core.mcp import payments_mcp, notify_mcp

router = APIRouter()


@router.get("/")
async def list_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return all orders for the authenticated user."""
    result = await db.execute(
        select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return a specific order — users can only see their own; admins see all."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Non-admins can only view their own orders
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Place a new order.
    """
    items_data = body.items
    subtotal = Decimal("0")
    order_items = []

    for item in items_data:
        result = await db.execute(
            select(Product)
            .where(Product.id == item.product_id)
            .with_for_update()
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

        line_total = product.price * item.quantity
        subtotal += line_total

        order_items.append(OrderItem(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price=product.price,
            quantity=item.quantity,
            line_total=line_total,
        ))

        # Decrement stock
        product.stock_quantity -= item.quantity

    # Build order — tax/shipping computed here (extend with real tax service via MCP)
    tax = subtotal * Decimal("0.18")       # 18% GST placeholder
    shipping = Decimal("50.00") if subtotal < Decimal("500") else Decimal("0")
    total = subtotal + tax + shipping

    order = Order(
        user_id=current_user.id,
        subtotal=subtotal,
        tax_amount=tax,
        shipping_amount=shipping,
        total_amount=total,
        shipping_name=body.shipping_name,
        shipping_address_line1=body.shipping_address_line1,
        shipping_address_line2=body.shipping_address_line2,
        shipping_city=body.shipping_city,
        shipping_state=body.shipping_state,
        shipping_postal_code=body.shipping_postal_code,
        shipping_country=body.shipping_country,
        customer_notes=body.customer_notes,
    )
    db.add(order)
    await db.flush()   # Get order.id without committing — needed to set order_id on items

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    await db.commit()
    await db.refresh(order)

    # MCP Integration: Send Order Confirmation
    items_list = [
        {"name": oi.product_name, "quantity": oi.quantity, "unit_price": str(oi.unit_price)}
        for oi in order_items
    ]
    await notify_mcp.call_tool(
        "send_order_confirmation",
        user_email=current_user.email,
        user_name=current_user.full_name,
        order_id=str(order.id),
        order_total=str(order.total_amount),
        items=items_list
    )

    return order


@router.patch("/{order_id}/status", dependencies=[Depends(get_current_admin_user)])
async def update_order_status(
    order_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: advance the order status machine."""
    valid_statuses = {"pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"}
    new_status = body.get("status")
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.user))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = new_status
    await db.commit()
    await db.refresh(order)

    # MCP Integration: Send Shipping Update
    if new_status == "shipped":
        await notify_mcp.call_tool(
            "send_shipping_update",
            user_email=order.user.email if hasattr(order, "user") and order.user else "user@example.com",
            user_name=order.user.full_name if hasattr(order, "user") and order.user else "Customer",
            order_id=str(order.id),
            tracking_number="SW-" + str(order.id)[:8].upper(),
            carrier="FedEx"
        )

    return order

@router.post("/{order_id}/payment-intent")
async def create_payment_intent(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Integrates payments_mcp to create a payment intent."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    
    amount_paise = int(order.total_amount * 100)
    intent = await payments_mcp.call_tool(
        "create_payment_intent",
        order_id=str(order.id),
        amount_paise=amount_paise,
        currency="INR"
    )
    return intent

@router.post("/{order_id}/verify-payment")
async def verify_payment(
    order_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Integrates payments_mcp to verify a payment signature."""
    # BOLA/IDOR check: verify order exists and belongs to current user
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    verified = await payments_mcp.call_tool(
        "verify_payment",
        razorpay_order_id=body.get("razorpay_order_id"),
        razorpay_payment_id=body.get("razorpay_payment_id"),
        razorpay_signature=body.get("razorpay_signature")
    )
    if not verified.get("verified"):
        raise HTTPException(status_code=400, detail="Payment verification failed")
    
    order.status = "confirmed"
    order.payment_status = "paid"
    await db.commit()
    
    return {"status": "success", "message": "Payment verified and order confirmed."}
