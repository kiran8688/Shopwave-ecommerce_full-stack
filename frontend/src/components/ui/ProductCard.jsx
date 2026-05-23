// src/components/ui/ProductCard.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Reusable product card used in product grids and search results.
// ─────────────────────────────────────────────────────────────────────────────

import { Link } from 'react-router-dom'
import { ShoppingCart, Star } from 'lucide-react'
import { useCart } from '@/hooks/useCart'
import { formatINR, truncate } from '@/utils/helpers'

export default function ProductCard({ product }) {
  const { addToCart } = useCart()

  const isOutOfStock = product.stock_quantity === 0
  const hasDiscount  = product.compare_at_price &&
    parseFloat(product.compare_at_price) > parseFloat(product.price)

  const discountPct = hasDiscount
    ? Math.round(
        (1 - parseFloat(product.price) / parseFloat(product.compare_at_price)) * 100,
      )
    : null

  return (
    <article className="card p-0 overflow-hidden hover:shadow-md transition-shadow duration-200 group flex flex-col">

      {/* ── Product image ──────────────────────────────────────────────────── */}
      <Link to={`/products/${product.id}`} className="block relative">
        <div className="aspect-square bg-gray-100 overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              loading="lazy"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-5xl text-gray-300">
              📦
            </div>
          )}
        </div>

        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          {product.is_featured && (
            <span className="bg-accent text-white text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
              <Star className="h-3 w-3 fill-current" /> Featured
            </span>
          )}
          {discountPct && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              -{discountPct}%
            </span>
          )}
          {isOutOfStock && (
            <span className="bg-gray-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              Out of Stock
            </span>
          )}
        </div>
      </Link>

      {/* ── Product details ───────────────────────────────────────────────── */}
      <div className="p-4 flex flex-col flex-1">
        <Link to={`/products/${product.id}`} className="hover:text-primary">
          <h3 className="font-medium text-gray-900 text-sm leading-snug line-clamp-2 mb-1">
            {product.name}
          </h3>
        </Link>

        {product.description && (
          <p className="text-xs text-gray-500 mb-2 line-clamp-2">
            {truncate(product.description, 90)}
          </p>
        )}

        {/* Price row */}
        <div className="flex items-baseline gap-2 mt-auto mb-3">
          <span className="text-base font-bold text-primary">
            {formatINR(product.price)}
          </span>
          {hasDiscount && (
            <span className="text-xs text-gray-400 line-through">
              {formatINR(product.compare_at_price)}
            </span>
          )}
        </div>

        {/* Add to cart */}
        <button
          onClick={() => addToCart(product, 1)}
          disabled={isOutOfStock}
          className="btn-primary w-full text-sm py-2 disabled:opacity-40"
        >
          <ShoppingCart className="h-4 w-4 mr-1.5 inline" />
          {isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
        </button>
      </div>
    </article>
  )
}
