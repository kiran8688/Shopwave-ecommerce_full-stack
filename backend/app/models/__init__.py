# app/models/__init__.py
# Re-export all models so `from app.models import User` works cleanly.
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem

__all__ = ["User", "Category", "Product", "Order", "OrderItem"]
