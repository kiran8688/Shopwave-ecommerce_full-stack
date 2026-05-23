// src/hooks/useAuth.js
// ─────────────────────────────────────────────────────────────────────────────
// Thin hook wrapper around useAuthStore — gives components a stable import
// path so we can swap the underlying state manager without touching every file.
// ─────────────────────────────────────────────────────────────────────────────

import { useAuthStore } from '@/store/authStore'

export function useAuth() {
  const { user, isAuthenticated, isLoading, login, register, logout } = useAuthStore()
  return { user, isAuthenticated, isLoading, login, register, logout }
}
