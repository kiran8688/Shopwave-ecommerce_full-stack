// src/components/layout/Layout.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Shell layout wrapping all pages — renders Navbar, page content, and Footer.
// <Outlet /> is the React Router v7 slot where child route components render.
// ─────────────────────────────────────────────────────────────────────────────

import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Footer from './Footer'

export default function Layout() {
  return (
    // min-h-screen + flex-col ensures footer sticks to bottom even on short pages
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />

      {/* flex-1 makes main grow to fill remaining vertical space */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />   {/* Child route component renders here */}
      </main>

      <Footer />
    </div>
  )
}
