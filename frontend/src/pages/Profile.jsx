// src/pages/Profile.jsx
import { useAuthStore } from '@/store/authStore'
import { User, Mail, Shield } from 'lucide-react'

export default function Profile() {
  const { user, logout } = useAuthStore()
  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
      <div className="card space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-14 w-14 rounded-full bg-primary flex items-center justify-center text-white text-2xl font-bold">
            {user?.username?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">{user?.full_name ?? user?.username}</h2>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          <div className="py-3 flex items-center gap-3 text-sm">
            <User className="h-4 w-4 text-gray-400" />
            <span className="text-gray-600">Username:</span>
            <span className="font-medium">{user?.username}</span>
          </div>
          <div className="py-3 flex items-center gap-3 text-sm">
            <Mail className="h-4 w-4 text-gray-400" />
            <span className="text-gray-600">Email:</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <div className="py-3 flex items-center gap-3 text-sm">
            <Shield className="h-4 w-4 text-gray-400" />
            <span className="text-gray-600">Role:</span>
            <span className="font-medium capitalize">{user?.role}</span>
          </div>
        </div>
        <button onClick={logout} className="btn-outline w-full mt-2">Sign Out</button>
      </div>
    </div>
  )
}
