import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // Requests to /api or /files from the browser get passed to the Python backend.
    proxy: {
      "/api": "http://localhost:8000",
      "/files": "http://localhost:8000",
    },
  },
});