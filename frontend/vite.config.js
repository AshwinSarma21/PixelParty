import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": "http://backend:5000",
      "/socket.io": {
        target: "http://backend:5000",
        ws: true,
      },
    },
  },
})
