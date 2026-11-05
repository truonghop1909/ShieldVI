import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [react()],
  base: '/dashboard/',
  build: {
    outDir: fileURLToPath(new URL('../../../services/moderation-ai/app/static', import.meta.url)),
    emptyOutDir: true
  },
  server: {
    port: 5175,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000'
    }
  }
})
