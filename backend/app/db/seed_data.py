# app/db/seed_data.py
import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product

async def seed_data(db: AsyncSession) -> None:
    """Populate the database with dummy data for categories and products."""
    
    # 1. Check if categories already exist
    category_count_result = await db.execute(select(Category))
    if category_count_result.scalars().first():
        return # Already seeded
    
    # 2. Add categories
    categories = [
        Category(
            id=uuid.uuid4(),
            name="Electronics",
            slug="electronics",
            description="The latest gadgets and high-performance hardware.",
            image_url="https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&q=80"
        ),
        Category(
            id=uuid.uuid4(),
            name="Fashion",
            slug="fashion",
            description="Modern styles and premium apparel for everyone.",
            image_url="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&q=80"
        ),
        Category(
            id=uuid.uuid4(),
            name="Home & Living",
            slug="home-living",
            description="Beautiful furniture and decor for your sanctuary.",
            image_url="https://images.unsplash.com/photo-1484101403633-562f65bd242a?w=800&q=80"
        )
    ]
    
    try:
        db.add_all(categories)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return # Already seeded by another worker
    
    # 3. Add products
    products = [
        # Electronics
        Product(
            name="ShopWave Ultra Phone 15",
            slug="shopwave-ultra-phone-15",
            description="A premium smartphone with a crystal-clear 120Hz display and high-performance AI chip.",
            sku="SW-PH-15",
            price=Decimal("999.99"),
            compare_at_price=Decimal("1199.99"),
            stock_quantity=50,
            image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80",
            category_id=categories[0].id,
            is_featured=True
        ),
        Product(
            name="AcousticPro Noise-Canceling Headphones",
            slug="acousticpro-headphones",
            description="Experience pure sound with active noise cancellation and 40-hour battery life.",
            sku="AP-HD-40",
            price=Decimal("299.50"),
            stock_quantity=120,
            image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
            category_id=categories[0].id
        ),
        # Fashion
        Product(
            name="Classic Minimalist White Tee",
            slug="classic-white-tee",
            description="100% organic cotton, breathable, and designed for daily comfort.",
            sku="FAS-TEE-W",
            price=Decimal("24.99"),
            stock_quantity=500,
            image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
            category_id=categories[1].id
        ),
        Product(
            name="Urban Nomad Sneakers",
            slug="urban-nomad-sneakers",
            description="Ergonomic design for city dwellers who never stop moving.",
            sku="FAS-SNK-UN",
            price=Decimal("110.00"),
            compare_at_price=Decimal("150.00"),
            stock_quantity=85,
            image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80",
            category_id=categories[1].id,
            is_featured=True
        ),
        # Home & Living
        Product(
            name="Mid-Century Oak Coffee Table",
            slug="oak-coffee-table",
            description="Handcrafted from solid white oak with a natural finish.",
            sku="HOM-TBL-OAK",
            price=Decimal("450.00"),
            stock_quantity=15,
            image_url="https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=800&q=80",
            category_id=categories[2].id
        )
    ]
    
    try:
        db.add_all(products)
        await db.commit()
    except IntegrityError:
        await db.rollback()
    
    print("✅ Seed data populated!")
