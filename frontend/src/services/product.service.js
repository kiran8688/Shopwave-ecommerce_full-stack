// src/services/product.service.js
import api from './api'

export const productService = {
  async getProducts({ skip = 0, limit = 20, categoryId, search } = {}) {
    const params = new URLSearchParams()
    params.append('skip', skip)
    params.append('limit', limit)
    if (categoryId) params.append('category_id', categoryId)
    if (search) params.append('search', search)
    const { data } = await api.get(`/api/v1/products/?${params}`)
    return data
  },

  async getProduct(productId) {
    const { data } = await api.get(`/api/v1/products/${productId}`)
    return data
  },

  async getCategories() {
    const { data } = await api.get('/api/v1/categories/')
    return data
  },

  async createCategory(categoryData) {
    const { data } = await api.post('/api/v1/categories/', categoryData)
    return data
  },

  async deleteCategory(categoryId) {
    await api.delete(`/api/v1/categories/${categoryId}`)
  },

  async createProduct(productData) {
    const { data } = await api.post('/api/v1/products/', productData)
    return data
  },

  async updateProduct(productId, productData) {
    const { data } = await api.patch(`/api/v1/products/${productId}`, productData)
    return data
  },

  async deleteProduct(productId) {
    await api.delete(`/api/v1/products/${productId}`)
  },

  // AI Copywriting Generation
  async generateCopyPreview({ name, category, price, tone }) {
    const { data } = await api.post('/api/v1/products/generate-copy-preview', {
      name,
      category,
      price,
      tone,
    })
    return data
  },

  async generateCopyForProduct(productId, { tone }) {
    const { data } = await api.post(`/api/v1/products/${productId}/generate-copy`, {
      tone,
    })
    return data
  },

  // Admin Analytics
  async getSalesSummary(dateFrom, dateTo) {
    const params = new URLSearchParams()
    if (dateFrom) params.append('date_from', dateFrom)
    if (dateTo) params.append('date_to', dateTo)
    const { data } = await api.get(`/api/v1/analytics/summary?${params}`)
    return data
  },

  async getTopProducts(limit = 5, metric = 'revenue') {
    const params = new URLSearchParams()
    params.append('limit', limit)
    params.append('metric', metric)
    const { data } = await api.get(`/api/v1/analytics/top-products?${params}`)
    return data
  },

  async getRevenueByDay(days = 7) {
    const params = new URLSearchParams()
    params.append('days', days)
    const { data } = await api.get(`/api/v1/analytics/revenue?${params}`)
    return data
  },

  async getLowStockReport(threshold = 10) {
    const params = new URLSearchParams()
    params.append('threshold', threshold)
    const { data } = await api.get(`/api/v1/analytics/low-stock?${params}`)
    return data
  },
}

