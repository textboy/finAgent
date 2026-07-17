import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base path depends on deployment mode:
//   local       → served at root (no reverse proxy prefix)
//   production  → served behind nginx at /finagent/
const isProduction = process.env.RUN_MODE === 'production'

export default defineConfig({
  plugins: [react()],
  base: isProduction ? '/finagent/' : '/',
  server: {
    host: '0.0.0.0',
    port: 3001,
  },
})
