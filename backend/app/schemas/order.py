# app/schemas/order.py
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    shipping_name: str = Field(max_length=150)
    shipping_address_line1: str = Field(max_length=255)
    shipping_address_line2: str | None = None
    shipping_city: str = Field(max_length=100)
    shipping_state: str = Field(max_length=100)
    shipping_postal_code: str = Field(max_length=20)
    shipping_country: str = Field(max_length=2, default="IN")
    customer_notes: str | None = None


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_sku: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    payment_status: str
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    total_amount: Decimal
    shipping_name: str
    shipping_city: str
    shipping_country: str
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
