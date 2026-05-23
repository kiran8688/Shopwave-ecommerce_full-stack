// src/pages/Cart.jsx
import { Link } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import { Trash2, ShoppingBag } from 'lucide-react'

export default function Cart() {
  const { items, updateQuantity, removeItem, clearCart, subtotal } = useCartStore()

  if (items.length === 0) {
    return (
      <div className="text-center py-24 space-y-4">
        <ShoppingBag className="h-16 w-16 mx-auto text-gray-300" />
        <h2 className="text-xl font-semibold text-gray-500">Your cart is empty</h2>
        <Link to="/products" className="btn-primary inline-flex">Continue Shopping</Link>
      </div>
    )
  }

  return (
    <div className="grid md:grid-cols-3 gap-8">
      {/* Items list */}
      <div className="md:col-span-2 space-y-4">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold text-gray-900">Shopping Cart</h1>
          <button onClick={clearCart} className="text-sm text-red-500 hover:underline">Clear all</button>
        </div>
        {items.map(item => (
          <div key={item.id} className="card flex gap-4">
            <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden shrink-0">
              {item.image_url
                ? <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                : <div className="w-full h-full flex items-center justify-center text-2xl">📦</div>
              }
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 truncate">{item.name}</h3>
              <p className="text-primary font-bold mt-1">₹{item.price.toFixed(2)}</p>
              <div className="flex items-center gap-3 mt-2">
                <div className="flex items-center border border-gray-200 rounded-lg text-sm">
                  <button onClick={() => updateQuantity(item.id, item.quantity - 1)} className="px-2 py-1 hover:bg-gray-50">−</button>
                  <span className="px-3">{item.quantity}</span>
                  <button onClick={() => updateQuantity(item.id, item.quantity + 1)} className="px-2 py-1 hover:bg-gray-50">+</button>
                </div>
                <button onClick={() => removeItem(item.id)} className="text-red-400 hover:text-red-600">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="font-bold text-gray-900">₹{(item.price * item.quantity).toFixed(2)}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Order summary */}
      <div className="card h-fit space-y-4">
        <h2 className="text-lg font-bold text-gray-900">Order Summary</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-gray-600">Subtotal</span><span>₹{subtotal.toFixed(2)}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Tax (18% GST)</span><span>₹{(subtotal * 0.18).toFixed(2)}</span></div>
          <div className="flex justify-between"><span className="text-gray-600">Shipping</span><span>{subtotal >= 500 ? 'Free' : '₹50.00'}</span></div>
          <div className="border-t border-gray-100 pt-2 flex justify-between font-bold text-base">
            <span>Total</span>
            <span className="text-primary">₹{(subtotal * 1.18 + (subtotal >= 500 ? 0 : 50)).toFixed(2)}</span>
          </div>
        </div>
        <Link to="/checkout" className="btn-primary w-full text-center">Proceed to Checkout</Link>
        <Link to="/products" className="btn-secondary w-full text-center text-sm">Continue Shopping</Link>
      </div>
    </div>
  )
}
