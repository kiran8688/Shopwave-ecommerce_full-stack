// src/hooks/useCart.js
import { useCartStore } from '@/store/cartStore'
import toast from 'react-hot-toast'

export function useCart() {
  const store = useCartStore()

  /**
   * addToCart with built-in toast notification.
   * Components call this instead of store.addItem directly.
   */
  function addToCart(product, quantity = 1) {
    if (product.stock_quantity < quantity) {
      toast.error('Not enough stock available')
      return false
    }
    store.addItem(product, quantity)
    toast.success(`${product.name} added to cart!`, { duration: 2500 })
    return true
  }

  return {
    items: store.items,
    itemCount: store.itemCount,
    subtotal: store.subtotal,
    addToCart,
    updateQuantity: store.updateQuantity,
    removeItem: store.removeItem,
    clearCart: store.clearCart,
  }
}
