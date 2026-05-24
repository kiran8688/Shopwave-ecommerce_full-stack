// src/App.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Root component — defines the application route tree.
// Layout component wraps all pages that need Navbar + Footer.
// ─────────────────────────────────────────────────────────────────────────────

import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import Home from '@/pages/Home'
import Products from '@/pages/Products'
import ProductDetail from '@/pages/ProductDetail'
import Cart from '@/pages/Cart'
import Checkout from '@/pages/Checkout'
import Auth from '@/pages/Auth'
import Profile from '@/pages/Profile'
import Orders from '@/pages/Orders'
import AdminDashboard from '@/pages/admin/AdminDashboard'
import { useAuthStore } from '@/store/authStore'

// ── Protected Route guard ─────────────────────────────────────────────────────
// Wraps routes that require authentication — redirects to /auth if not logged in
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/auth" replace />
}

// ── Admin Route guard ────────────────────────────────────────────────────────
function AdminRoute({ children }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/auth" replace />
  if (user?.role !== 'admin') return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      {/* All routes inside Layout get the shared Navbar + Footer */}
      <Route element={<Layout />}>

        {/* ── Public routes ─────────────────────────────────────────────── */}
        <Route index element={<Home />} />
        <Route path="products" element={<Products />} />
        <Route path="products/:id" element={<ProductDetail />} />
        <Route path="cart" element={<Cart />} />
        <Route path="auth" element={<Auth />} />

        {/* ── Protected routes ──────────────────────────────────────────── */}
        <Route
          path="checkout"
          element={<ProtectedRoute><Checkout /></ProtectedRoute>}
        />
        <Route
          path="profile"
          element={<ProtectedRoute><Profile /></ProtectedRoute>}
        />
        <Route
          path="orders"
          element={<ProtectedRoute><Orders /></ProtectedRoute>}
        />

        {/* ── Admin routes ──────────────────────────────────────────────── */}
        <Route
          path="admin"
          element={<AdminRoute><AdminDashboard /></AdminRoute>}
        />

        {/* ── Catch-all 404 redirect ────────────────────────────────────── */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
