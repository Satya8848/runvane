// Copyright (c) 2026, Satya and contributors. For license information, please see license.txt
import typography from "@tailwindcss/typography";
export default {
	content: ["./index.html", "./src/**/*.{vue,js}"],
	darkMode: "media",
	theme: {
		extend: {
			fontFamily: {
				sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
				display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
				mono: ["JetBrains Mono", "ui-monospace", "Menlo", "monospace"],
			},
			colors: {
				ink: { 50: "#f5f7fb", 100: "#e9edf5", 200: "#d4dbe8", 300: "#a9b4c8", 400: "#7a879e", 500: "#56627a", 600: "#3e485d", 700: "#2b3346", 800: "#1a2030", 900: "#10141f", 950: "#0a0d15" },
				brand: { 50: "#eef4ff", 100: "#dbe7ff", 200: "#bcd2ff", 300: "#8fb2ff", 400: "#5c87ff", 500: "#3a63f5", 600: "#2a49d9", 700: "#2339ae", 800: "#22338a", 900: "#20306d" },
				signal: { 400: "#2dd4bf", 500: "#14b8a6" },
			},
		},
	},
	plugins: [typography],
};
