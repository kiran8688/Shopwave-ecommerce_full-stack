// src/pages/Home.jsx
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productService } from '@/services/product.service'
import { ShoppingBag, ArrowRight } from 'lucide-react'

export default function Home() {
  const { data: products, isLoading } = useQuery({
    queryKey: ['products', 'featured'],
    queryFn: () => productService.getProducts({ limit: 8 }),
  })

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="rounded-2xl bg-gradient-to-br from-primary to-secondary p-12 text-white text-center">
        <ShoppingBag className="h-14 w-14 mx-auto mb-4 opacity-90" />
        <h1 className="text-4xl font-bold mb-3">Welcome to ShopWave</h1>
        <p className="text-blue-100 text-lg mb-6">Discover amazing products at great prices</p>
        <Link to="/products" className="inline-flex items-center gap-2 bg-white text-primary font-semibold px-6 py-3 rounded-xl hover:bg-blue-50 transition-colors">
          Shop Now <ArrowRight className="h-4 w-4" />
        </Link>
      </section>

      {/* Featured Products */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Featured Products</h2>
          <Link to="/products" className="text-primary hover:underline text-sm font-medium">View all</Link>
        </div>
        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-gray-100 rounded-xl h-64 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(products ?? []).map(product => (
              <Link key={product.id} to={`/products/${product.id}`} className="card hover:shadow-md transition-shadow group">
                <div className="aspect-square bg-gray-100 rounded-lg mb-3 overflow-hidden">
                  {product.image_url
                    ? <img src={product.image_url} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                    : <div className="w-full h-full flex items-center justify-center text-gray-300 text-4xl">📦</div>
                  }
                </div>
                <h3 className="font-medium text-gray-900 text-sm truncate">{product.name}</h3>
                <p className="text-primary font-bold mt-1">₹{parseFloat(product.price).toFixed(2)}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
