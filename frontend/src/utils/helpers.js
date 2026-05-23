// src/utils/helpers.js

/**
 * Format a number as Indian Rupee currency string.
 * e.g. 1234.5 → "₹1,234.50"
 */
export function formatINR(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(parseFloat(amount))
}

/**
 * Truncate a string to maxLen characters, appending "…" if cut.
 */
export function truncate(str, maxLen = 80) {
  if (!str || str.length <= maxLen) return str
  return str.slice(0, maxLen) + '…'
}

/**
 * Convert a UUID to a short 8-char uppercase reference code.
 * e.g. "a1b2c3d4-..." → "A1B2C3D4"
 */
export function shortId(uuid) {
  return uuid?.replace(/-/g, '').slice(0, 8).toUpperCase() ?? ''
}

/**
 * Format an ISO date string for display.
 * e.g. "2025-04-09T..." → "9 Apr 2025"
 */
export function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

/**
 * Clamp a value between min and max (inclusive).
 */
export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}
