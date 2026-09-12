import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules') && /recharts|d3-|victory-vendor|decimal.js/.test(id)) return 'charts';
        },
      },
    },
  },
});
