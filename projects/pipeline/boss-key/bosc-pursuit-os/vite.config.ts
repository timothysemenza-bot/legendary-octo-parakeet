import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    open: false,
    port: 4173,
    proxy: {
      "/api": {
        target: `http://localhost:${process.env.BOSSKEY_IMPORT_PORT || "4174"}`,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
  },
});
