import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// The backend serves no CORS headers (correlation/middleware is intentionally minimal), so in dev
// the SPA reaches the API through this same-origin proxy: requests to `/api/*` are forwarded to the
// backend. Production serving is a deployment concern handled in a later slice.
const API_TARGET = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': { target: API_TARGET, changeOrigin: true } },
  },
  preview: { host: true, port: 4173 },
  test: {
    environment: 'jsdom',
    globals: false,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.{ts,tsx}', 'src/test/**', 'src/vite-env.d.ts', 'src/index.tsx'],
      thresholds: { statements: 80, branches: 80, functions: 80, lines: 80 },
    },
  },
})
