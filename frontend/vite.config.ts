import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  base: mode === "production" ? "/rep-trainer/" : "/",
  plugins: [react()],
  server: { port: 5173, host: true, proxy: { "/api": "http://127.0.0.1:8000" } },
  test: { environment: "node" },
}));
