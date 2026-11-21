// Copyright (c) 2026, Satya and contributors. For license information, please see license.txt
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
	plugins: [vue()],
	base: "/assets/stackpilot/spa/",
	build: { outDir: path.resolve(__dirname, "../stackpilot/public/spa"), emptyOutDir: true, chunkSizeWarningLimit: 1500 },
	server: { port: 8081, proxy: { "^/(api|assets|login|files)": { target: "http://127.0.0.1:8002" } } },
});
