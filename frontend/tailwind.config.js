/** @type {import('tailwindcss').Config} */
export default {
  // Tailwind scans these files to purge unused CSS classes in production builds
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary:  { DEFAULT: '#2563eb', dark: '#1d4ed8', light: '#3b82f6' },
        secondary:{ DEFAULT: '#7c3aed', dark: '#6d28d9' },
        accent:   { DEFAULT: '#f59e0b' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
