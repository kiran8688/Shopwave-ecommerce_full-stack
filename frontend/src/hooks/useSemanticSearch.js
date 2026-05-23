// src/hooks/useSemanticSearch.js
// ─────────────────────────────────────────────────────────────────────────────
// TanStack Query wrapper around the /products/search endpoint,
// which internally delegates to mcp-search via MCPClient.
// ─────────────────────────────────────────────────────────────────────────────

import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'

/**
 * Perform a semantic search against the ShopWave catalogue.
 *
 * @param {object} opts
 * @param {string}  opts.query       - Search query string
 * @param {string}  opts.categoryId  - Optional category UUID filter
 * @param {number}  opts.minPrice    - Optional lower price bound
 * @param {number}  opts.maxPrice    - Optional upper price bound
 * @param {boolean} opts.enabled     - Set false to disable (e.g. while typing)
 */
export function useSemanticSearch({
  query = '',
  categoryId,
  minPrice,
  maxPrice,
  enabled = true,
} = {}) {
  return useQuery({
    queryKey: ['semantic-search', query, categoryId, minPrice, maxPrice],

    queryFn: async () => {
      if (!query.trim()) return { results: [], count: 0, query }

      const params = new URLSearchParams({ query: query.trim(), limit: 24 })
      if (categoryId) params.append('category_id', categoryId)
      if (minPrice != null) params.append('min_price', String(minPrice))
      if (maxPrice != null) params.append('max_price', String(maxPrice))

      const { data } = await api.get(`/api/v1/products/search?${params}`)
      return data
    },

    enabled: enabled && query.trim().length > 0,
    staleTime: 1000 * 30,        // Cache results 30 s — searches are expensive
    placeholderData: (prev) => prev,  // Keep previous results while new ones load
  })
}
