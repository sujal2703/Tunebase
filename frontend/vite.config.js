import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://127.0.0.1:5000",
      "/users": "http://127.0.0.1:5000",
      "/songs": "http://127.0.0.1:5000",
      "/playlists": "http://127.0.0.1:5000",
      "/plans": "http://127.0.0.1:5000",
      "/subscriptions": "http://127.0.0.1:5000",
      "/transactions": "http://127.0.0.1:5000",
      "/devices": "http://127.0.0.1:5000",
      "/sessions": "http://127.0.0.1:5000",
      "/recommendations": "http://127.0.0.1:5000",
      "/search": "http://127.0.0.1:5000",
      "/notifications": "http://127.0.0.1:5000",
      "/downloads": "http://127.0.0.1:5000"
    }
  },
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
