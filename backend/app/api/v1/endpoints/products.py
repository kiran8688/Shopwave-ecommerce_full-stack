# app/api/v1/endpoints/products.py
# Full CRUD for products — admin-only writes, public reads.

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user
from app.core.mcp import inventory_mcp, search_mcp
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: UUID | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — returns paginated product list.
    Supports filtering by category and text search on name.
    """
    query = select(Product).where(Product.is_active == True)   # noqa: E712

    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        # ILIKE = case-insensitive LIKE; PG 18 supports this natively
        query = query.where(Product.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search/semantic")
async def semantic_search(
    query: str = Query(..., description="Free-text semantic search query"),
    limit: int = Query(20, ge=1, le=100),
    category_id: UUID | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
):
    """
    Public endpoint — uses search_mcp to perform semantic search via pgvector embeddings.
    """
    results = await search_mcp.call_tool(
        "semantic_search",
        query=query,
        limit=limit,
        category_id=str(category_id) if category_id else None,
        min_price=min_price,
        max_price=max_price
    )
    return results


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single product by UUID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),   # Guard: only admins can create
):
    """Admin-only: create a new product."""
    product = Product(**body.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Admin-only: update an existing product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
            
    await db.commit()
    await db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Admin-only: delete a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()
    return None

@router.get("/{product_id}/reorder-suggestion", dependencies=[Depends(get_current_admin_user)])
async def get_reorder_suggestion(product_id: UUID):
    """
    Admin-only endpoint — uses inventory_mcp to get AI-ready reorder recommendations.
    """
    suggestion = await inventory_mcp.call_tool(
        "suggest_reorder",
        product_id=str(product_id),
        lead_time_days=7
    )
    return suggestion
