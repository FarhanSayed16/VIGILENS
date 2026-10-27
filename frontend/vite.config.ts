import basicSsl from "@vitejs/plugin-basic-ssl";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const api = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    // Phone browsers only show a camera prompt on HTTPS.
    // The page proxies API calls so the phone never talks to port 8000 directly.
    proxy: {
      "/health": api,
      "/auth": api,
      "/rooms": api,
      "/sessions": api,
      "/jobs": api,
      "/pulse": api,
    },
  },
});
