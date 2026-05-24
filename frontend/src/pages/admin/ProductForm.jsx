// src/pages/admin/ProductForm.jsx
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productService } from '@/services/product.service'
import { X, Save, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ProductForm({ product, onClose }) {
  const isEdit = !!product
  const queryClient = useQueryClient()
  
  const [formData, setFormData] = useState({
    name: product?.name || '',
    slug: product?.slug || '',
    sku: product?.sku || '',
    price: product?.price || '',
    stock_quantity: product?.stock_quantity || 0,
    description: product?.description || '',
    image_url: product?.image_url || '',
    category_id: product?.category_id || '',
    is_active: product?.is_active ?? true,
    is_featured: product?.is_featured ?? false,
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: productService.getCategories
  })

  const [generatingCopy, setGeneratingCopy] = useState(false)

  const handleAIGenerateCopy = async () => {
    if (!formData.name) {
      toast.error('Please enter a product name first')
      return
    }
    setGeneratingCopy(true)
    try {
      const selectedCat = categories?.find(c => c.id === formData.category_id)
      const categoryName = selectedCat ? selectedCat.name : ''
      const res = await productService.generateCopyPreview({
        name: formData.name,
        category: categoryName,
        price: formData.price ? parseFloat(formData.price) : undefined,
        tone: 'persuasive'
      })
      if (res && res.description) {
        let fullText = res.description
        if (res.bullet_points && res.bullet_points.length > 0) {
          fullText += '\n\nKey Features:\n' + res.bullet_points.join('\n')
        }
        setFormData(prev => ({
          ...prev,
          description: fullText
        }))
        toast.success('AI description generated!')
      } else {
        toast.error('Could not generate description')
      }
    } catch (err) {
      console.error(err)
      toast.error('AI generation failed')
    } finally {
      setGeneratingCopy(false)
    }
  }

  const mutation = useMutation({
    mutationFn: (data) => isEdit 
      ? productService.updateProduct(product.id, data) 
      : productService.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['products'])
      toast.success(isEdit ? 'Product updated' : 'Product created')
      onClose()
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || 'Something went wrong'
      toast.error(msg)
    }
  })

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // Validation
    if (!formData.name || !formData.sku || !formData.price) {
      toast.error('Please fill required fields')
      return
    }
    
    // Auto-slugify if empty
    const payload = { ...formData }
    if (!payload.slug) {
      payload.slug = payload.name.toLowerCase().replace(/ /g, '-').replace(/[^\w-]+/g, '')
    }
    
    mutation.mutate(payload)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-900">
            {isEdit ? 'Edit Product' : 'Add New Product'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700">Product Name *</label>
              <input 
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="input"
                placeholder="e.g. iPhone 15 Pro"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700">SKU *</label>
              <input 
                name="sku"
                value={formData.sku}
                onChange={handleChange}
                className="input font-mono"
                placeholder="PH-001"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700">Price (INR) *</label>
              <input 
                name="price"
                type="number"
                step="0.01"
                value={formData.price}
                onChange={handleChange}
                className="input"
                placeholder="0.00"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700">Stock Quantity</label>
              <input 
                name="stock_quantity"
                type="number"
                value={formData.stock_quantity}
                onChange={handleChange}
                className="input"
                placeholder="0"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700">Category</label>
            <select 
              name="category_id"
              value={formData.category_id}
              onChange={handleChange}
              className="input"
            >
              <option value="">Select Category</option>
              {categories?.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700">Image URL</label>
            <input 
              name="image_url"
              value={formData.image_url}
              onChange={handleChange}
              className="input"
              placeholder="https://images.unsplash.com/..."
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-semibold text-gray-700">Description</label>
              <button
                type="button"
                onClick={handleAIGenerateCopy}
                disabled={generatingCopy}
                className="text-xs text-primary font-semibold inline-flex items-center gap-1 hover:text-primary-dark disabled:opacity-50 transition-all cursor-pointer"
              >
                {generatingCopy ? '✨ Writing...' : '🔮 AI Write'}
              </button>
            </div>
            <textarea 
              name="description"
              rows="5"
              value={formData.description}
              onChange={handleChange}
              className="input resize-none"
              placeholder="Write something about the product..."
            />
          </div>

          <div className="flex items-center gap-8">
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="text-sm font-medium text-gray-700">Active</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox"
                name="is_featured"
                checked={formData.is_featured}
                onChange={handleChange}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="text-sm font-medium text-gray-700">Featured</span>
            </label>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
          <p className="text-xs text-gray-500 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" /> * required fields
          </p>
          <div className="flex gap-3">
            <button 
              onClick={onClose}
              className="btn-secondary px-6"
            >
              Cancel
            </button>
            <button 
              onClick={handleSubmit}
              disabled={mutation.isPending}
              className="btn-primary inline-flex items-center gap-2 px-8"
            >
              <Save className="h-4 w-4" /> 
              {mutation.isPending ? 'Saving...' : 'Save Product'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
