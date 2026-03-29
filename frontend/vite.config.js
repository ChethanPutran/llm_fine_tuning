import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  // Better source map configuration
  build: {
    sourcemap: true, // Enable source maps
    minify: false, // Disable minification for better debugging
    rollupOptions: {
      output: {
        sourcemap: true,
        sourcemapExcludeSources: false,
      }
    }
  },
  
  server: {
    port: 3000,
    sourcemap: true, // For development
    open: true,
    hmr: {
      overlay: true, // Show errors as overlay
    },
  },
  
  // Important: Tell Vite to preserve source maps
  define: {
    'process.env.NODE_ENV': '"development"',
  },
  
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
    alias: {
      '@': '/src',
      '@components': '/src/components',
    }
  },
  
  // Force source maps for all files
  optimizeDeps: {
    force: true, // Force dependency pre-bundling
  },
})