import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The API client talks to http://127.0.0.1:8000 directly; the M9 server already
// allows http://localhost:5173 as a CORS origin, so no dev proxy is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
