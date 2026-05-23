# app/schemas/category.py
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=120)
    description: str | None = None
    image_url: str | None = None
    parent_id: uuid.UUID | None = None


class CategoryResponse(CategoryCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}
