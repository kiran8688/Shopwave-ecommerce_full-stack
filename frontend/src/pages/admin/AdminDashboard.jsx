// src/pages/admin/AdminDashboard.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Catalogue & Administrative Dashboard.
// Implements Category CRUD, low-stock warnings, and AI stock reorder suggestions.
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productService } from '@/services/product.service'
import { Plus, Pencil, Trash2, Package, Search, Sparkles, FolderKanban, AlertTriangle, X, DollarSign, Users, ShoppingBag, BarChart3, TrendingUp } from 'lucide-react'
import toast from 'react-hot-toast'
import ProductForm from './ProductForm'
import api from '@/services/api'

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('products') // 'products' | 'categories'
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  // Category CRUD states
  const [isCatFormOpen, setIsCatFormOpen] = useState(false)
  const [catForm, setCatForm] = useState({ name: '', slug: '', description: '', image_url: '' })
  const [isCatSubmitting, setIsCatSubmitting] = useState(false)

  // AI Suggestion state
  const [activeSuggestion, setActiveSuggestion] = useState(null)
  const [isFetchingSuggestion, setIsFetchingSuggestion] = useState(false)

  const queryClient = useQueryClient()

  // Queries
  const { data: products, isLoading: isProductsLoading } = useQuery({
    queryKey: ['products', 'admin', searchTerm],
    queryFn: () => productService.getProducts({ search: searchTerm, limit: 100 }),
  })

  const { data: categories, isLoading: isCategoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: productService.getCategories,
  })

  const { data: salesSummary, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['salesSummary'],
    queryFn: () => productService.getSalesSummary(),
    enabled: activeTab === 'analytics'
  })

  const { data: topProducts, isLoading: isTopProductsLoading } = useQuery({
    queryKey: ['topProducts'],
    queryFn: () => productService.getTopProducts(5, 'revenue'),
    enabled: activeTab === 'analytics'
  })

  const { data: revenueByDay, isLoading: isRevenueLoading } = useQuery({
    queryKey: ['revenueByDay'],
    queryFn: () => productService.getRevenueByDay(7),
    enabled: activeTab === 'analytics'
  })

  const { data: lowStockReport, isLoading: isLowStockLoading } = useQuery({
    queryKey: ['lowStockReport'],
    queryFn: () => productService.getLowStockReport(10),
    enabled: activeTab === 'analytics'
  })

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: (id) => productService.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['products'])
      toast.success('Product deleted successfully')
    },
    onError: () => toast.error('Failed to delete product')
  })

  const deleteCatMutation = useMutation({
    mutationFn: (id) => productService.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['categories'])
      toast.success('Category deleted successfully')
    },
    onError: () => toast.error('Failed to delete category. Ensure it has no products associated.')
  })

  // Handlers
  const handleEdit = (product) => {
    setEditingProduct(product)
    setIsFormOpen(true)
  }

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      deleteMutation.mutate(id)
    }
  }

  const openAddForm = () => {
    setEditingProduct(null)
    setIsFormOpen(true)
  }

  async function handleFetchAIReorder(product) {
    setIsFetchingSuggestion(true)
    try {
      const { data } = await api.get(`/api/v1/products/${product.id}/reorder-suggestion`)
      setActiveSuggestion({
        productName: product.name,
        stock: product.stock_quantity,
        sku: product.sku,
        ...data
      })
    } catch (err) {
      toast.error('Could not fetch AI replenishment forecast.')
    } finally {
      setIsFetchingSuggestion(false)
    }
  }

  async function handleAddCategory(e) {
    e.preventDefault()
    if (!catForm.name || !catForm.slug) {
      return toast.error('Please enter name and slug.')
    }
    setIsCatSubmitting(true)
    try {
      await productService.createCategory(catForm)
      queryClient.invalidateQueries(['categories'])
      toast.success('Category created successfully!')
      setCatForm({ name: '', slug: '', description: '', image_url: '' })
      setIsCatFormOpen(false)
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Failed to create category')
    } finally {
      setIsCatSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Catalogue & Analytics</h1>
          <p className="text-gray-500">Manage your products, categories, inventory forecasts and sales analytics.</p>
        </div>
        {activeTab === 'products' ? (
          <button
            onClick={openAddForm}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Add New Product
          </button>
        ) : activeTab === 'categories' ? (
          <button
            onClick={() => setIsCatFormOpen(true)}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Add Category
          </button>
        ) : null}
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('products')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'products' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Products Catalogue
        </button>
        <button
          onClick={() => setActiveTab('categories')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'categories' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Categories Manager
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'analytics' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Sales & Analytics
        </button>
      </div>

      {/* Products Tab view */}
      {activeTab === 'products' && (
        <div className="space-y-6">
          <div className="flex items-center gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search within catalogue..."
                className="input pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Product</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">SKU</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Price</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Stock</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {isProductsLoading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} className="animate-pulse">
                        <td colSpan="5" className="px-6 py-8 h-10 bg-gray-50/50"></td>
                      </tr>
                    ))
                  ) : products?.length > 0 ? (
                    products.map((product) => (
                      <tr key={product.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded bg-gray-100 flex items-center justify-center overflow-hidden">
                              {product.image_url ? (
                                <img src={product.image_url} alt="" className="h-full w-full object-cover" />
                              ) : (
                                <Package className="h-5 w-5 text-gray-400" />
                              )}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{product.name}</div>
                              <div className="text-xs text-gray-500 capitalize">{product.slug}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600 font-mono">{product.sku}</td>
                        <td className="px-6 py-4 text-sm font-semibold text-gray-900">₹{parseFloat(product.price).toFixed(2)}</td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col sm:flex-row sm:items-start gap-2">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide w-fit ${
                              product.stock_quantity > 10 ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                            }`}>
                              {product.stock_quantity} in stock
                            </span>

                            {/* AI Stock warnings suggester trigger */}
                            {product.stock_quantity <= 10 && (
                              <button
                                onClick={() => handleFetchAIReorder(product)}
                                className="inline-flex items-center gap-1 text-[10px] font-bold text-violet-600 bg-violet-50 hover:bg-violet-100 px-2 py-0.5 rounded-full transition-all border border-violet-100"
                              >
                                <Sparkles className="h-3 w-3" />
                                AI Forecast
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleEdit(product)}
                              className="p-1.5 text-gray-400 hover:text-primary hover:bg-blue-50 rounded-lg transition-colors"
                              title="Edit"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(product.id)}
                              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                        No products found. Start by adding one!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Categories Tab View */}
      {activeTab === 'categories' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Category</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Slug</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Description</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {isCategoriesLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <tr key={i} className="animate-pulse">
                        <td colSpan="4" className="px-6 py-8 h-10 bg-gray-50/50"></td>
                      </tr>
                    ))
                  ) : categories?.length > 0 ? (
                    categories.map((cat) => (
                      <tr key={cat.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded bg-gray-100 flex items-center justify-center overflow-hidden">
                              {cat.image_url ? (
                                <img src={cat.image_url} alt="" className="h-full w-full object-cover" />
                              ) : (
                                <FolderKanban className="h-5 w-5 text-gray-400" />
                              )}
                            </div>
                            <span className="font-medium text-gray-900">{cat.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600 font-mono">{cat.slug}</td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{cat.description || 'No description.'}</td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => {
                              if (window.confirm('Are you sure you want to delete this category?')) {
                                deleteCatMutation.mutate(cat.id)
                              }
                            }}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="px-6 py-12 text-center text-gray-500">
                        No categories found. Start by adding one!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Analytics Tab View */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {/* KPI Dashboard summary grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Revenue */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex items-center gap-4 relative overflow-hidden">
              <div className="absolute right-0 bottom-0 translate-x-2 translate-y-2 opacity-5 text-primary">
                <DollarSign className="h-24 w-24" />
              </div>
              <div className="h-12 w-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                <DollarSign className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Total Revenue</span>
                <span className="text-2xl font-bold text-gray-900 mt-1 block">
                  {isSummaryLoading ? '...' : `₹${salesSummary?.total_revenue?.toLocaleString() || '0.00'}`}
                </span>
              </div>
            </div>

            {/* Total Orders */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex items-center gap-4 relative overflow-hidden">
              <div className="absolute right-0 bottom-0 translate-x-2 translate-y-2 opacity-5 text-violet-600">
                <ShoppingBag className="h-24 w-24" />
              </div>
              <div className="h-12 w-12 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
                <ShoppingBag className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Total Orders</span>
                <span className="text-2xl font-bold text-gray-900 mt-1 block">
                  {isSummaryLoading ? '...' : salesSummary?.total_orders || 0}
                </span>
              </div>
            </div>

            {/* Total Customers */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex items-center gap-4 relative overflow-hidden">
              <div className="absolute right-0 bottom-0 translate-x-2 translate-y-2 opacity-5 text-emerald-600">
                <Users className="h-24 w-24" />
              </div>
              <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Customers</span>
                <span className="text-2xl font-bold text-gray-900 mt-1 block">
                  {isSummaryLoading ? '...' : salesSummary?.total_customers || 0}
                </span>
              </div>
            </div>

            {/* Average Order Value */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex items-center gap-4 relative overflow-hidden">
              <div className="absolute right-0 bottom-0 translate-x-2 translate-y-2 opacity-5 text-amber-600">
                <TrendingUp className="h-24 w-24" />
              </div>
              <div className="h-12 w-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <TrendingUp className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Avg Order Value</span>
                <span className="text-2xl font-bold text-gray-900 mt-1 block">
                  {isSummaryLoading ? '...' : `₹${parseFloat(salesSummary?.average_order_value || 0).toFixed(2)}`}
                </span>
              </div>
            </div>
          </div>

          {/* Graphs & Sales Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Daily Sales Bar Chart */}
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-gray-900 flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" /> Daily Revenue Trend
                </h3>
                <span className="text-xs font-semibold bg-primary/10 text-primary px-3 py-1 rounded-full">Last 7 Days</span>
              </div>
              
              <div className="h-64 flex items-end justify-between gap-4 pt-6 relative">
                {isRevenueLoading ? (
                  <div className="w-full h-full flex items-center justify-center text-sm text-gray-500">Loading charts...</div>
                ) : revenueByDay?.data?.length > 0 ? (
                  revenueByDay.data.map((day, idx) => {
                    const maxRevenue = Math.max(...revenueByDay.data.map(d => d.revenue), 1)
                    const heightPercent = Math.min(100, Math.max(8, (day.revenue / maxRevenue) * 100))
                    const dateObj = new Date(day.date)
                    const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' })
                    const dayNum = dateObj.toLocaleDateString('en-US', { day: 'numeric' })
                    
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center group h-full justify-end relative">
                        {/* Hover Details Popover */}
                        <div className="opacity-0 group-hover:opacity-100 absolute bottom-full mb-2 bg-gray-900 text-white text-[10px] rounded py-1 px-2 pointer-events-none transition-all shadow-md z-10 text-center whitespace-nowrap">
                          <p className="font-bold">₹{day.revenue.toFixed(0)}</p>
                          <p className="text-[8px] text-gray-400">{day.orders_count} orders</p>
                        </div>
                        
                        {/* Bar Segment */}
                        <div 
                          className="w-full rounded-t-lg bg-gradient-to-t from-primary/80 to-primary group-hover:from-primary group-hover:to-primary-dark transition-all duration-300 relative cursor-pointer"
                          style={{ height: `${heightPercent}%` }}
                        >
                          {day.revenue === maxRevenue && (
                            <span className="absolute -top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-yellow-400 animate-ping" />
                          )}
                        </div>
                        
                        <span className="text-[10px] font-bold text-gray-700 mt-2">{dayName}</span>
                        <span className="text-[9px] text-gray-400">{dayNum}</span>
                      </div>
                    )
                  })
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-sm text-gray-500">No revenue data available.</div>
                )}
              </div>
            </div>

            {/* Top Products */}
            <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-6">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" /> Best Sellers
              </h3>
              
              <div className="space-y-4">
                {isTopProductsLoading ? (
                  <div className="text-sm text-gray-500 py-4">Loading top products...</div>
                ) : topProducts?.length > 0 ? (
                  topProducts.map((p, i) => {
                    const topRevenue = topProducts[0]?.revenue || 1
                    const progressWidth = Math.min(100, Math.max(10, (p.revenue / topRevenue) * 100))
                    
                    return (
                      <div key={p.id || i} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-gray-900 truncate max-w-[180px]">{p.name}</span>
                          <span className="text-gray-500 font-mono">₹{parseFloat(p.revenue).toFixed(0)}</span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full transition-all duration-500" 
                            style={{ width: `${progressWidth}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-[10px] text-gray-400">
                          <span>{p.sales_count} units sold</span>
                          <span>Stock: {p.current_stock}</span>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="text-sm text-gray-500 py-4">No top product sales yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* Low Stock Alerts and Action */}
          {lowStockReport && lowStockReport.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6 space-y-4">
              <div className="flex items-center gap-2 text-orange-800">
                <AlertTriangle className="h-5 w-5" />
                <h3 className="font-bold text-sm">Critical Inventory Action Required</h3>
              </div>
              <p className="text-xs text-orange-700">
                The following products have dropped below active inventory threshold level (10 units). AI recommends immediate supplier dispatch.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {lowStockReport.map(item => (
                  <div key={item.id} className="bg-white p-4 rounded-xl border border-orange-100 flex justify-between items-center shadow-sm">
                    <div>
                      <h4 className="text-xs font-bold text-gray-900">{item.name}</h4>
                      <p className="text-[10px] text-gray-500 font-mono">SKU: {item.sku}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-red-600 block">{item.stock_quantity} remaining</span>
                      <button 
                        onClick={() => handleFetchAIReorder(item)}
                        className="text-[9px] font-bold text-violet-600 hover:underline mt-1 block"
                      >
                        ⚡ AI Forecast Reorder
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI Suggestion Dialog modal */}
      {activeSuggestion && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl relative animate-slide-up">
            <button
              onClick={() => setActiveSuggestion(null)}
              className="absolute top-4 right-4 p-1 rounded-lg hover:bg-gray-100 text-gray-400"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 mb-4 text-violet-600 bg-violet-50 p-3 rounded-xl">
              <Sparkles className="h-5 w-5" />
              <h3 className="font-bold text-violet-900 text-sm">AI Stock Replenishment Forecast</h3>
            </div>

            <div className="space-y-3 text-sm text-gray-600">
              <p><strong className="text-gray-900">Product:</strong> {activeSuggestion.productName}</p>
              <p><strong className="text-gray-900">SKU:</strong> <span className="font-mono">{activeSuggestion.sku}</span></p>
              <p><strong className="text-gray-900">Current Stock:</strong> {activeSuggestion.stock} units</p>
              <hr className="my-2 border-gray-100" />

              {activeSuggestion.status === 'mocked' ? (
                <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-100 p-3 rounded-xl space-y-2">
                  <p className="text-xs text-violet-700 font-semibold flex items-center gap-1">
                    <Sparkles className="h-3.5 w-3.5" /> AI Lead Time Suggestion (Forecast Model)
                  </p>
                  <p className="text-xs text-violet-600">
                    Stock is critical. Reorder recommended is <strong>{50 - activeSuggestion.stock} units</strong> via lead-time supplier.
                  </p>
                </div>
              ) : (
                <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-100 p-3 rounded-xl space-y-2">
                  <p className="text-xs text-violet-700 font-semibold flex items-center gap-1">
                    <Sparkles className="h-3.5 w-3.5" /> AI Lead-Time Suggestion
                  </p>
                  <p className="text-xs text-violet-600">
                    Calculated Lead Time: <strong>{activeSuggestion.lead_time_days || 7} days</strong>.
                    Suggested Replenishment Units: <strong>{activeSuggestion.suggested_reorder_qty || 50}</strong>.
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={() => setActiveSuggestion(null)}
              className="btn-primary w-full mt-5 py-2"
            >
              Acknowledge
            </button>
          </div>
        </div>
      )}

      {/* Category Creation Form Modal */}
      {isCatFormOpen && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleAddCategory} className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl relative animate-slide-up space-y-4">
            <button
              type="button"
              onClick={() => setIsCatFormOpen(false)}
              className="absolute top-4 right-4 p-1 rounded-lg hover:bg-gray-100 text-gray-400"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="border-b pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Add New Category</h3>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Category Name *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Smart Devices"
                  required
                  value={catForm.name}
                  onChange={e => setCatForm(c => ({ ...c, name: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Slug *</label>
                <input
                  type="text"
                  className="input font-mono"
                  placeholder="e.g. smart-devices"
                  required
                  value={catForm.slug}
                  onChange={e => setCatForm(c => ({ ...c, slug: e.target.value.toLowerCase().replace(/ /g, '-') }))}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Description</label>
                <textarea
                  className="input h-20 resize-none"
                  placeholder="Brief explanation of items in category..."
                  value={catForm.description}
                  onChange={e => setCatForm(c => ({ ...c, description: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Image URL</label>
                <input
                  type="text"
                  className="input"
                  placeholder="https://..."
                  value={catForm.image_url}
                  onChange={e => setCatForm(c => ({ ...c, image_url: e.target.value }))}
                />
              </div>
            </div>

            <div className="flex gap-3 pt-3 border-t">
              <button
                type="button"
                onClick={() => setIsCatFormOpen(false)}
                className="btn-secondary flex-1 text-sm py-2"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isCatSubmitting}
                className="btn-primary flex-1 text-sm py-2"
              >
                {isCatSubmitting ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Product Form component */}
      {isFormOpen && (
        <ProductForm 
          product={editingProduct} 
          onClose={() => setIsFormOpen(false)} 
        />
      )}
    </div>
  )
}
