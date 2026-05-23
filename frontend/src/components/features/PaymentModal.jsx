// src/components/features/PaymentModal.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Razorpay payment modal component.
//
// Flow:
//  1. User clicks "Pay Now"
//  2. POST /orders/:id/payment-intent → FastAPI → mcp-payments → Razorpay API
//  3. Razorpay JS SDK modal opens with the returned order_id
//  4. User completes payment; Razorpay SDK fires the handler callback
//  5. POST /orders/:id/verify-payment → mcp-payments verifies HMAC signature
//  6. On success → navigate to /orders
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '@/services/api'
import { formatINR } from '@/utils/helpers'

export default function PaymentModal({ orderId, totalAmount, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handlePay() {
    setLoading(true)

    try {
      // ── Step 1: Create payment intent via mcp-payments ──────────────────
      const { data: intent } = await api.post(
        `/api/v1/orders/${orderId}/payment-intent`,
      )

      // ── Step 2: Configure and open Razorpay modal ───────────────────────
      // window.Razorpay is loaded via <script> tag in index.html:
      // <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
      const options = {
        key:         import.meta.env.VITE_RAZORPAY_KEY_ID || intent.key_id || 'rzp_test_shopwavekeys',
        amount:      intent.amount,          // In paise (already set by mcp-payments)
        currency:    intent.currency,
        order_id:    intent.razorpay_order_id,
        name:        'ShopWave',
        description: `Order #${orderId.slice(0, 8).toUpperCase()}`,
        theme:       { color: '#2563eb' },

        // ── Step 4: Handle payment success callback ─────────────────────
        handler: async (response) => {
          try {
            // ── Step 5: Verify signature via mcp-payments ───────────────
            await api.post(`/api/v1/orders/${orderId}/verify-payment`, {
              razorpay_order_id:  response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature:  response.razorpay_signature,
            })

            // ── Step 6: Success ─────────────────────────────────────────
            toast.success('Payment successful! 🎉')
            onSuccess?.()
            navigate('/orders')
          } catch (verifyErr) {
            toast.error(
              verifyErr.response?.data?.detail ??
              'Payment verification failed. Contact support.',
            )
          }
        },

        modal: {
          // If user closes the modal without paying, restore the button
          ondismiss: () => setLoading(false),
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.on('payment.failed', (resp) => {
        toast.error(`Payment failed: ${resp.error.description}`)
        setLoading(false)
      })
      rzp.open()

    } catch (err) {
      toast.error(
        err.response?.data?.detail ?? 'Could not initialise payment. Try again.',
      )
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handlePay}
      disabled={loading}
      className="btn-primary w-full text-base py-3"
    >
      {loading
        ? 'Preparing payment…'
        : `Pay ${formatINR(totalAmount)}`
      }
    </button>
  )
}
