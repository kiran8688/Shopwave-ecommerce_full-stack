// src/components/layout/Footer.jsx
import { Link } from 'react-router-dom'
import { Package } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">

          {/* Brand */}
          <div>
            <Link to="/" className="flex items-center gap-2 mb-3">
              <Package className="h-6 w-6 text-primary" />
              <span className="font-bold text-gray-900">ShopWave</span>
            </Link>
            <p className="text-sm text-gray-500">
              Modern e-commerce built with FastAPI, React, and PostgreSQL 18.
            </p>
          </div>

          {/* Shop links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Shop</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><Link to="/products" className="hover:text-primary">All Products</Link></li>
              <li><Link to="/cart" className="hover:text-primary">Cart</Link></li>
              <li><Link to="/orders" className="hover:text-primary">My Orders</Link></li>
            </ul>
          </div>

          {/* Account links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Account</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><Link to="/auth" className="hover:text-primary">Sign In / Register</Link></li>
              <li><Link to="/profile" className="hover:text-primary">My Profile</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-100 mt-8 pt-6 text-center text-xs text-gray-400">
          © {new Date().getFullYear()} ShopWave. Built with FastAPI + React + PostgreSQL 18.
        </div>
      </div>
    </footer>
  )
}
