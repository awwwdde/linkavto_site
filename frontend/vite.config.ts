import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Прокси на Django-бэкенд (:8000) для API, медиа и статики.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000',
    },
  },
})
