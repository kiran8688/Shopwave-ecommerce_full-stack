// src/pages/Auth.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Package } from 'lucide-react'

export default function Auth() {
  const [mode, setMode] = useState('login')  // 'login' | 'register'
  const [form, setForm] = useState({ email: '', username: '', full_name: '', password: '' })
  const { login, register, isLoading } = useAuthStore()
  const navigate = useNavigate()

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const success = mode === 'login'
      ? await login({ email: form.email, password: form.password })
      : await register(form)
    if (success) navigate('/')
  }

  return (
    <div className="max-w-md mx-auto mt-10">
      <div className="card">
        {/* Header */}
        <div className="text-center mb-8">
          <Package className="h-10 w-10 text-primary mx-auto mb-2" />
          <h1 className="text-2xl font-bold text-gray-900">
            {mode === 'login' ? 'Sign in to ShopWave' : 'Create your account'}
          </h1>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
          {['login', 'register'].map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${mode === m ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input name="full_name" value={form.full_name} onChange={handleChange}
                  className="input" placeholder="Jane Doe" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input name="username" value={form.username} onChange={handleChange}
                  className="input" placeholder="janedoe" required minLength={3} />
              </div>
            </>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange}
              className="input" placeholder="jane@example.com" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input name="password" type="password" value={form.password} onChange={handleChange}
              className="input" placeholder="••••••••" required minLength={8} />
          </div>

          <button type="submit" disabled={isLoading} className="btn-primary w-full mt-2">
            {isLoading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
