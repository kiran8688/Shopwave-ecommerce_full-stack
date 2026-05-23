// src/pages/Checkout.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import api from '@/services/api'
import toast from 'react-hot-toast'
import PaymentModal from '@/components/features/PaymentModal'

export default function Checkout() {
  const navigate = useNavigate()
  const { items, subtotal, clearCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [createdOrder, setCreatedOrder] = useState(null)
  const [form, setForm] = useState({
    shipping_name: '', shipping_address_line1: '', shipping_address_line2: '',
    shipping_city: '', shipping_state: '', shipping_postal_code: '', shipping_country: 'IN',
  })
  const [billingSameAsShipping, setBillingSameAsShipping] = useState(true)
  const [billingForm, setBillingForm] = useState({
    billing_name: '', billing_address_line1: '', billing_address_line2: '',
    billing_city: '', billing_state: '', billing_postal_code: '', billing_country: 'IN',
  })

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function handleBillingChange(e) {
    setBillingForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleCreateOrder(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data: order } = await api.post('/api/v1/orders/', {
        ...form,
        items: items.map(i => ({ product_id: i.id, quantity: i.quantity })),
      })
      setCreatedOrder(order)
      toast.success('Order details saved! Proceed to payment.')
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Failed to place order')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>

      {!createdOrder ? (
        <form onSubmit={handleCreateOrder} className="space-y-6">
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
            
            <label className="flex items-center gap-2 mt-4 cursor-pointer">
              <input
                type="checkbox"
                checked={billingSameAsShipping}
                onChange={e => setBillingSameAsShipping(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="text-sm text-gray-700 font-medium">Billing address matches shipping</span>
            </label>
          </div>

          {!billingSameAsShipping && (
            <div className="card space-y-4 border-t-2 border-primary animate-slide-down">
              <h2 className="font-semibold text-gray-900">Billing Address</h2>
              {[
                { name: 'billing_name', label: 'Full Name', placeholder: 'Jane Doe' },
                { name: 'billing_address_line1', label: 'Address Line 1', placeholder: '123 Main St' },
                { name: 'billing_address_line2', label: 'Address Line 2 (optional)', placeholder: 'Apt 4B' },
                { name: 'billing_city', label: 'City', placeholder: 'Hyderabad' },
                { name: 'billing_state', label: 'State', placeholder: 'Telangana' },
                { name: 'billing_postal_code', label: 'Postal Code', placeholder: '500001' },
              ].map(({ name, label, placeholder }) => (
                <div key={name}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                  <input
                    name={name}
                    value={billingForm[name]}
                    onChange={handleBillingChange}
                    placeholder={placeholder}
                    required={!name.includes('line2')}
                    className="input"
                  />
                </div>
              ))}
            </div>
          )}

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
            {loading ? 'Saving Details...' : 'Continue to Payment'}
          </button>
        </form>
      ) : (
        <div className="space-y-6">
          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 text-lg">Shipping Summary</h2>
            <div className="text-sm text-gray-600 space-y-1">
              <p><strong className="text-gray-900">Name:</strong> {createdOrder.shipping_name}</p>
              <p><strong className="text-gray-900">Address:</strong> {createdOrder.shipping_address_line1}{createdOrder.shipping_address_line2 ? `, ${createdOrder.shipping_address_line2}` : ''}</p>
              <p><strong className="text-gray-900">City & State:</strong> {createdOrder.shipping_city}, {createdOrder.shipping_state} - {createdOrder.shipping_postal_code}</p>
            </div>
          </div>

          <div className="card space-y-4">
            <h2 className="font-semibold text-gray-900 text-lg">Payment Details</h2>
            <div className="flex justify-between font-bold text-lg pt-2 border-t mb-4">
              <span>Grand Total</span>
              <span className="text-primary">₹{parseFloat(createdOrder.total_amount).toFixed(2)}</span>
            </div>
            <PaymentModal
              orderId={createdOrder.id}
              totalAmount={parseFloat(createdOrder.total_amount)}
              onSuccess={clearCart}
            />
            <button
              onClick={() => setCreatedOrder(null)}
              className="btn-outline w-full text-sm mt-3"
            >
              Back to Shipping Info
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
