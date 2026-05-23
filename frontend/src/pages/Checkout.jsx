// src/pages/Checkout.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import api from '@/services/api'
import toast from 'react-hot-toast'

export default function Checkout() {
  const navigate = useNavigate()
  const { items, subtotal, clearCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    shipping_name: '', shipping_address_line1: '', shipping_address_line2: '',
    shipping_city: '', shipping_state: '', shipping_postal_code: '', shipping_country: 'IN',
  })

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handlePlaceOrder(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/api/v1/orders/', {
        ...form,
        items: items.map(i => ({ product_id: i.id, quantity: i.quantity })),
      })
      clearCart()
      toast.success('Order placed successfully! 🎉')
      navigate('/orders')
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Failed to place order')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>
      <form onSubmit={handlePlaceOrder} className="space-y-6">
        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-900">Shipping Address</h2>
          {[
            { name: 'shipping_name', label: 'Full Name', placeholder: 'Jane Doe' },
            { name: 'shipping_address_line1', label: 'Address Line 1', placeholder: '123 Main St' },
            { name: 'shipping_address_line2', label: 'Address Line 2 (optional)', placeholder: 'Apt 4B' },
            { name: 'shipping_city', label: 'City', placeholder: 'Hyderabad' },
            { name: 'shipping_state', label: 'State', placeholder: 'Telangana' },
            { name: 'shipping_postal_code', label: 'Postal Code', placeholder: '500001' },
          ].map(({ name, label, placeholder }) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                name={name}
                value={form[name]}
                onChange={handleChange}
                placeholder={placeholder}
                required={!name.includes('line2')}
                className="input"
              />
            </div>
          ))}
        </div>

        {/* Order summary */}
        <div className="card space-y-3">
          <h2 className="font-semibold text-gray-900">Order Summary ({items.length} items)</h2>
          {items.map(i => (
            <div key={i.id} className="flex justify-between text-sm">
              <span className="text-gray-600">{i.name} × {i.quantity}</span>
              <span>₹{(i.price * i.quantity).toFixed(2)}</span>
            </div>
          ))}
          <div className="border-t pt-3 flex justify-between font-bold">
            <span>Total</span>
            <span className="text-primary">₹{(subtotal * 1.18 + (subtotal >= 500 ? 0 : 50)).toFixed(2)}</span>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? 'Placing Order...' : 'Place Order'}
        </button>
      </form>
    </div>
  )
}
