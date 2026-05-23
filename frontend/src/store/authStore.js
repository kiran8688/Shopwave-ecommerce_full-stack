// src/store/authStore.js
// ─────────────────────────────────────────────────────────────────────────────
// Global auth state managed by Zustand.
// 'persist' middleware serialises state to localStorage so the user stays
// logged in across page refreshes.
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authService } from '@/services/auth.service'
import toast from 'react-hot-toast'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // ── State ────────────────────────────────────────────────────────────
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,

      // ── Actions ──────────────────────────────────────────────────────────
      login: async ({ email, password }) => {
        set({ isLoading: true })
        try {
          const { access_token } = await authService.login({ email, password })

          // Store token in localStorage (interceptor reads from here)
          localStorage.setItem('access_token', access_token)

          // Fetch user profile with the new token
          const user = await authService.getMe()

          set({ accessToken: access_token, user, isAuthenticated: true })
          toast.success(`Welcome back, ${user.username}!`)
          return true
        } catch (err) {
          const msg = err.response?.data?.detail ?? 'Login failed'
          toast.error(msg)
          return false
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (payload) => {
        set({ isLoading: true })
        try {
          const { access_token } = await authService.register(payload)
          localStorage.setItem('access_token', access_token)
          const user = await authService.getMe()
          set({ accessToken: access_token, user, isAuthenticated: true })
          toast.success('Account created! Welcome to ShopWave.')
          return true
        } catch (err) {
          const msg = err.response?.data?.detail ?? 'Registration failed'
          toast.error(msg)
          return false
        } finally {
          set({ isLoading: false })
        }
      },

      logout: async () => {
        try {
          await authService.logout()   // Clears HttpOnly cookie on server
        } catch {
          // Ignore logout API errors — clear local state regardless
        }
        localStorage.removeItem('access_token')
        set({ user: null, accessToken: null, isAuthenticated: false })
        toast.success('Signed out successfully')
      },
    }),
    {
      name: 'shopwave-auth',     // localStorage key
      // Only persist these fields — don't persist isLoading
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
