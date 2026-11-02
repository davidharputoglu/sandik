import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// En développement, l'interface (port 5173) parle au serveur Python (port 8460).
const backend = process.env.SANDIK_BACKEND || 'http://127.0.0.1:8460'

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: process.env.SANDIK_STATIC_DIR || '../sandik/static',
    emptyOutDir: true,
    chunkSizeWarningLimit: 800,
  },
  server: {
    proxy: {
      '/api': backend,
      '/edition': backend,
      '/favicon.ico': backend,
      '/modules': backend,
    },
  },
})
