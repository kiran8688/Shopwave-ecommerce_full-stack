// src/main.jsx
// ─────────────────────────────────────────────────────────────────────────────
// React 19 application bootstrap — mounts the root component and wraps it
// with all global providers.
// ─────────────────────────────────────────────────────────────────────────────

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

import App from './App'
import './index.css'   // Tailwind directives + global styles

// ── TanStack Query client ─────────────────────────────────────────────────────
// QueryClient manages all server-state: caching, background refetching, retries.
// staleTime: 60s — cached data is considered fresh for 1 minute before refetch
// retry: 1 — retry failed requests once before showing an error
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      retry: 1,
      refetchOnWindowFocus: false,  // Don't refetch every time the tab regains focus
    },
  },
})

// ── Mount ─────────────────────────────────────────────────────────────────────
// createRoot is the React 19 concurrent-mode entry point (replaces ReactDOM.render)
createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* StrictMode runs effects twice in dev to surface side-effect bugs */}
    <QueryClientProvider client={queryClient}>
      {/* BrowserRouter provides HTML5 history-based routing */}
      <BrowserRouter>
        <App />
        {/* Toaster renders toast notifications injected via react-hot-toast */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: { fontSize: '14px' },
            success: { iconTheme: { primary: '#2563eb', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
