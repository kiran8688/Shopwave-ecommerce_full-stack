// src/store/cartStore.js
// ─────────────────────────────────────────────────────────────────────────────
// Client-side cart state — no server sync until checkout.
// Persisted to localStorage so cart survives browser refreshes.
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const calculateTotals = (items) => {
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0)
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0)
  return { itemCount, subtotal }
}

export const useCartStore = create(
  persist(
    (set, get) => ({
      // items: [{ id, name, price, quantity, image_url, slug }]
      items: [],
      itemCount: 0,
      subtotal: 0,

      // ── Actions ──────────────────────────────────────────────────────────
      addItem: (product, quantity = 1) => {
        set((state) => {
          const existing = state.items.find(i => i.id === product.id)
          let nextItems
          if (existing) {
            // Increment quantity if item already in cart
            nextItems = state.items.map(i =>
              i.id === product.id
                ? { ...i, quantity: i.quantity + quantity }
                : i
            )
          } else {
            // Add new item
            nextItems = [...state.items, {
              id: product.id,
              name: product.name,
              price: parseFloat(product.price),
              quantity,
              image_url: product.image_url,
              slug: product.slug,
              sku: product.sku,
            }]
          }
          return {
            items: nextItems,
            ...calculateTotals(nextItems)
          }
        })
      },

      updateQuantity: (productId, quantity) => {
        if (quantity <= 0) {
          get().removeItem(productId)
          return
        }
        set((state) => {
          const nextItems = state.items.map(i =>
            i.id === productId ? { ...i, quantity } : i
          )
          return {
            items: nextItems,
            ...calculateTotals(nextItems)
          }
        })
      },

      removeItem: (productId) => {
        set((state) => {
          const nextItems = state.items.filter(i => i.id !== productId)
          return {
            items: nextItems,
            ...calculateTotals(nextItems)
          }
        })
      },

      clearCart: () => set({ items: [], itemCount: 0, subtotal: 0 }),
    }),
    {
      name: 'shopwave-cart',
      partialize: (state) => ({
        items: state.items,
        itemCount: state.itemCount,
        subtotal: state.subtotal,
      }),
    },
  ),
)
window.useCartStore = useCartStore
