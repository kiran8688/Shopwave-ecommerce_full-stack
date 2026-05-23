// src/services/api.js
// ─────────────────────────────────────────────────────────────────────────────
// Centralised Axios instance with:
//   • Base URL from Vite env var (inlined at build time)
//   • Request interceptor — attaches Bearer token from authStore
//   • Response interceptor — handles 401 (token expired) globally
// ─────────────────────────────────────────────────────────────────────────────

import axios from 'axios'

// VITE_API_BASE_URL is set via docker-compose build arg or .env.local in dev
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,   // Send cookies (HttpOnly refresh token) with every request
  timeout: 15_000,         // 15 second timeout — avoids hanging requests
})

// ── Request interceptor ───────────────────────────────────────────────────────
// Runs before every request — attaches the JWT access token from localStorage
// (Zustand persists it there via the persist middleware).
api.interceptors.request.use(
  (config) => {
    // Read token from localStorage directly — avoids circular import with authStore
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor ──────────────────────────────────────────────────────
// Runs after every response — handles expired tokens globally so individual
// service calls don't need try/catch for auth errors.
api.interceptors.response.use(
  (response) => response,        // Pass successful responses straight through
  async (error) => {
    const status = error.response?.status

    if (status === 401) {
      // Token expired — clear local auth state and redirect to login
      // Import dynamically to avoid circular dependency with authStore
      localStorage.removeItem('access_token')
      window.location.href = '/auth'
    }

    return Promise.reject(error)
  },
)

export default api
