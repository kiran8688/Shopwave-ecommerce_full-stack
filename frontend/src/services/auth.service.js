// src/services/auth.service.js
// ─────────────────────────────────────────────────────────────────────────────
// Auth API calls — thin wrappers around the Axios instance.
// All business logic (token storage, state update) lives in authStore.
// ─────────────────────────────────────────────────────────────────────────────

import api from './api'

export const authService = {
  /**
   * Register a new account.
   * Returns { access_token, token_type }
   */
  async register({ email, username, full_name, password }) {
    const { data } = await api.post('/api/v1/auth/register', {
      email,
      username,
      full_name,
      password,
    })
    return data
  },

  /**
   * Login with email + password (OAuth2 form-data format required by FastAPI).
   * Returns { access_token, token_type }
   */
  async login({ email, password }) {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const formData = new URLSearchParams()
    formData.append('username', email)   // FastAPI's OAuth2 uses 'username' field for email
    formData.append('password', password)

    const { data } = await api.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  /**
   * Fetch the currently authenticated user's profile.
   */
  async getMe() {
    const { data } = await api.get('/api/v1/users/me')
    return data
  },

  /**
   * Clear the server-side refresh token cookie.
   */
  async logout() {
    await api.post('/api/v1/auth/logout')
  },
}
