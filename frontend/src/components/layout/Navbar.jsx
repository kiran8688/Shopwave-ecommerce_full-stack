// src/components/layout/Navbar.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Responsive navigation bar with:
//   • Logo / brand link
//   • Product search (links to /products?search=query)
//   • Cart icon with item count badge
//   • Auth links (Login | My Account)
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShoppingCart, Search, User, Menu, X, Package } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useCartStore } from '@/store/cartStore'
import { Settings } from 'lucide-react'

export default function Navbar() {
  const [searchQuery, setSearchQuery] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const navigate = useNavigate()

  // Zustand stores — subscribes to auth + cart state
  const { isAuthenticated, user, logout } = useAuthStore()
  const { itemCount } = useCartStore()

  function handleSearch(e) {
    e.preventDefault()
    if (searchQuery.trim()) {
      // Navigate to products page with search query param
      navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
    }
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">

          {/* ── Brand ──────────────────────────────────────────────────────── */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <Package className="h-7 w-7 text-primary" />
            <span className="text-xl font-bold text-gray-900">ShopWave</span>
          </Link>

          {/* ── Search bar (hidden on mobile) ─────────────────────────────── */}
          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-lg">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="search"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search products..."
                className="input pl-10 pr-4"
              />
            </div>
          </form>

          {/* ── Right nav actions ─────────────────────────────────────────── */}
          <nav className="flex items-center gap-2">

            {/* Cart icon with badge */}
            <Link
              to="/cart"
              className="relative p-2 text-gray-600 hover:text-primary rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Shopping cart"
            >
              <ShoppingCart className="h-6 w-6" />
              {itemCount > 0 && (
                // Badge — shows number of distinct items in cart
                <span className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center
                                 bg-primary text-white text-xs font-bold rounded-full">
                  {itemCount > 99 ? '99+' : itemCount}
                </span>
              )}
            </Link>

            {/* Auth links */}
            {isAuthenticated ? (
              <div className="flex items-center gap-1">
                {user?.role === 'admin' && (
                  <Link
                    to="/admin"
                    className="flex items-center gap-1 px-3 py-2 text-sm font-medium
                               text-primary hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    <Settings className="h-4 w-4" />
                    <span className="hidden lg:inline">Admin</span>
                  </Link>
                )}
                <Link
                  to="/profile"
                  className="flex items-center gap-1 px-3 py-2 text-sm font-medium
                             text-gray-700 hover:text-primary rounded-lg hover:bg-gray-100"
                >
                  <User className="h-4 w-4" />
                  <span className="hidden sm:inline">{user?.username ?? 'Account'}</span>
                </Link>
                <button
                  onClick={logout}
                  className="btn-secondary text-sm px-3 py-1.5"
                >
                  Logout
                </button>
              </div>
            ) : (
              <Link to="/auth" className="btn-primary text-sm">
                Sign In
              </Link>
            )}

            {/* Mobile menu toggle */}
            <button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setMobileMenuOpen(o => !o)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </nav>
        </div>

        {/* ── Mobile search (shown when menu open) ─────────────────────── */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4">
            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="search"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search products..."
                className="input flex-1"
              />
              <button type="submit" className="btn-primary px-4">Go</button>
            </form>
          </div>
        )}
      </div>
    </header>
  )
}
