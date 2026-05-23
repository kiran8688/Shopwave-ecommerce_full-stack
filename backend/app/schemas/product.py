# app/schemas/product.py
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None
    sku: str = Field(max_length=100)
    price: Decimal = Field(gt=0, decimal_places=2)
    compare_at_price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True
    is_featured: bool = False
    image_url: str | None = None
    thumbnail_url: str | None = None
    category_id: uuid.UUID | None = None


class ProductCreate(ProductBase):
    slug: str = Field(max_length=220)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    is_featured: bool | None = None
    image_url: str | None = None
    category_id: uuid.UUID | None = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
