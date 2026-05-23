// src/pages/Orders.jsx
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { Package } from 'lucide-react'
import { shortId } from '@/utils/helpers'

const STATUS_COLORS = {
  pending:    'bg-yellow-100 text-yellow-800',
  confirmed:  'bg-blue-100 text-blue-800',
  processing: 'bg-purple-100 text-purple-800',
  shipped:    'bg-indigo-100 text-indigo-800',
  delivered:  'bg-green-100 text-green-800',
  cancelled:  'bg-red-100 text-red-800',
  refunded:   'bg-gray-100 text-gray-700',
}

export default function Orders() {
  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/orders/')
      return data
    },
  })

  if (isLoading) return <div className="space-y-4">{Array.from({length:3}).map((_,i)=><div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"/>)}</div>

  if (!orders?.length) {
    return (
      <div className="text-center py-20 space-y-3">
        <Package className="h-14 w-14 mx-auto text-gray-300" />
        <p className="text-gray-500">You haven't placed any orders yet.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Orders</h1>
      {orders.map(order => (
        <div key={order.id} className="card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-400">Order #{shortId(order.id)}</p>
              <p className="text-sm text-gray-500 mt-1">{new Date(order.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' })}</p>
            </div>
            <div className="text-right">
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_COLORS[order.status] ?? 'bg-gray-100 text-gray-700'}`}>
                {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
              </span>
              <p className="text-lg font-bold text-primary mt-2">₹{parseFloat(order.total_amount).toFixed(2)}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
