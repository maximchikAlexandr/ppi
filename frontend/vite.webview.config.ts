import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Webview build: HTML entry reusing the same App, output into the extension package.
// `base: "./"` produces relative asset paths so the host can rewrite them to
// vscode-resource URIs without fragile absolute-path assumptions.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "../vscode-extension/dist-webview",
    emptyOutDir: true,
    rollupOptions: {
      input: "webview.html",
    },
  },
});
