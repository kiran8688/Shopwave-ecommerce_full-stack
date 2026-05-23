// src/pages/Products.jsx
import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productService } from '@/services/product.service'
import { useCartStore } from '@/store/cartStore'
import toast from 'react-hot-toast'
import { ShoppingCart, Filter } from 'lucide-react'

export default function Products() {
  const [searchParams] = useSearchParams()
  const searchQuery = searchParams.get('search') ?? ''
  const [categoryId, setCategoryId] = useState(null)

  const { addItem } = useCartStore()

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: productService.getCategories,
  })

  const { data: products, isLoading } = useQuery({
    queryKey: ['products', { search: searchQuery, categoryId }],
    queryFn: () => productService.getProducts({ search: searchQuery, categoryId }),
  })

  function handleAddToCart(product, e) {
    e.preventDefault()   // Prevent navigation when button inside <Link> is clicked
    addItem(product, 1)
    toast.success(`${product.name} added to cart!`)
  }

  return (
    <div className="flex gap-6">
      {/* Sidebar: category filter */}
      <aside className="hidden md:block w-48 shrink-0">
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="h-4 w-4 text-gray-500" />
            <h3 className="font-semibold text-gray-900 text-sm">Categories</h3>
          </div>
          <ul className="space-y-1">
            <li>
              <button
                onClick={() => setCategoryId(null)}
                className={`w-full text-left text-sm px-2 py-1.5 rounded-lg transition-colors ${!categoryId ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'}`}
              >All</button>
            </li>
            {(categories ?? []).map(cat => (
              <li key={cat.id}>
                <button
                  onClick={() => setCategoryId(cat.id)}
                  className={`w-full text-left text-sm px-2 py-1.5 rounded-lg transition-colors ${categoryId === cat.id ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                >{cat.name}</button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* Product grid */}
      <div className="flex-1">
        {searchQuery && (
          <p className="text-gray-500 text-sm mb-4">
            Results for <span className="font-semibold text-gray-900">"{searchQuery}"</span>
          </p>
        )}
        {isLoading ? (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 9 }).map((_, i) => <div key={i} className="bg-gray-100 h-72 rounded-xl animate-pulse" />)}
          </div>
        ) : (products ?? []).length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <ShoppingCart className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No products found</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {(products ?? []).map(product => (
              <Link key={product.id} to={`/products/${product.id}`} className="card hover:shadow-md transition-shadow group relative">
                <div className="aspect-square bg-gray-100 rounded-lg mb-3 overflow-hidden">
                  {product.image_url
                    ? <img src={product.image_url} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                    : <div className="w-full h-full flex items-center justify-center text-5xl">📦</div>
                  }
                </div>
                <h3 className="font-medium text-gray-900 text-sm line-clamp-2">{product.name}</h3>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-primary font-bold">₹{parseFloat(product.price).toFixed(2)}</p>
                  {product.compare_at_price && (
                    <p className="text-xs text-gray-400 line-through">₹{parseFloat(product.compare_at_price).toFixed(2)}</p>
                  )}
                </div>
                <button
                  onClick={(e) => handleAddToCart(product, e)}
                  className="btn-primary w-full mt-3 text-sm py-1.5"
                >
                  <ShoppingCart className="h-4 w-4 mr-1" /> Add to Cart
                </button>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
