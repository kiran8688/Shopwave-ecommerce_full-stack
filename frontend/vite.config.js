// vite.config.js
// ─────────────────────────────────────────────────────────────────────────────
// Vite 6 build configuration for the React frontend.
// ─────────────────────────────────────────────────────────────────────────────

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),  // Enables JSX transform, Fast Refresh (HMR for React state)
  ],

  resolve: {
    alias: {
      // '@' maps to ./src — import '@/components/Foo' instead of '../../components/Foo'
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    // Dev proxy — avoids CORS issues by forwarding /api requests to the backend
    // during local development (without Docker). In Docker, Nginx handles proxying.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,   // Rewrites the Host header to match the target
        secure: false,        // Accept self-signed certs in dev
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,         // Disable source maps in production builds
    rollupOptions: {
      output: {
        // Split vendor libraries into a separate chunk — cached separately by browsers
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query:  ['@tanstack/react-query'],
        },
      },
    },
  },
})
