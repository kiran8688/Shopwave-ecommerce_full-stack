// src/pages/ProductDetail.jsx
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productService } from '@/services/product.service'
import { useCartStore } from '@/store/cartStore'
import toast from 'react-hot-toast'
import { ShoppingCart, Package } from 'lucide-react'
import { useState } from 'react'

export default function ProductDetail() {
  const { slug: id } = useParams()   // We route by id for simplicity
  const [qty, setQty] = useState(1)
  const { addItem } = useCartStore()

  const { data: product, isLoading } = useQuery({
    queryKey: ['product', id],
    queryFn: () => productService.getProduct(id),
  })

  if (isLoading) return <div className="h-96 bg-gray-100 rounded-xl animate-pulse" />
  if (!product) return <p className="text-center text-gray-500 py-20">Product not found</p>

  return (
    <div className="grid md:grid-cols-2 gap-10">
      {/* Image */}
      <div className="aspect-square bg-gray-100 rounded-2xl overflow-hidden">
        {product.image_url
          ? <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
          : <div className="w-full h-full flex items-center justify-center text-8xl"><Package /></div>
        }
      </div>

      {/* Details */}
      <div className="space-y-5">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
          <p className="text-sm text-gray-400 mt-1">SKU: {product.sku}</p>
        </div>
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-bold text-primary">₹{parseFloat(product.price).toFixed(2)}</span>
          {product.compare_at_price && (
            <span className="text-lg text-gray-400 line-through">₹{parseFloat(product.compare_at_price).toFixed(2)}</span>
          )}
        </div>
        {product.description && <p className="text-gray-600 leading-relaxed">{product.description}</p>}

        <div className="flex items-center gap-3">
          <div className="flex items-center border border-gray-200 rounded-lg">
            <button onClick={() => setQty(q => Math.max(1, q - 1))} className="px-3 py-2 text-gray-600 hover:bg-gray-50">−</button>
            <span className="px-4 font-medium">{qty}</span>
            <button onClick={() => setQty(q => q + 1)} className="px-3 py-2 text-gray-600 hover:bg-gray-50">+</button>
          </div>
          <button
            className="btn-primary flex-1"
            onClick={() => { addItem(product, qty); toast.success('Added to cart!') }}
          >
            <ShoppingCart className="h-4 w-4 mr-2" /> Add to Cart
          </button>
        </div>

        <p className="text-sm text-gray-500">
          {product.stock_quantity > 0
            ? <span className="text-green-600 font-medium">✓ In Stock ({product.stock_quantity} available)</span>
            : <span className="text-red-500 font-medium">✗ Out of Stock</span>
          }
        </p>
      </div>
    </div>
  )
}
