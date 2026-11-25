import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, las llamadas a /api se reenvían al backend FastAPI (puerto 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: process.env.VITE_BACKEND_URL ?? "http://localhost:8000", changeOrigin: true },
    },
  },
});
