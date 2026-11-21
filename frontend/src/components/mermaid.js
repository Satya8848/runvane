// Copyright (c) 2026, Satya and contributors. For license information, please see license.txt
let loader = null;
let counter = 0;

/**
 * Render Mermaid source into an element (loads mermaid lazily).
 *
 * @param {HTMLElement} el - Target.
 * @param {string} source - Mermaid text.
 * @returns {Promise<boolean>} True when it rendered.
 */
export async function renderMermaid(el, source) {
	if (!loader) {
		loader = import("mermaid").then(({ default: mermaid }) => {
			const dark = matchMedia("(prefers-color-scheme: dark)").matches;
			mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "strict", fontFamily: "Inter, sans-serif" });
			return mermaid;
		});
	}
	const mermaid = await loader;
	try {
		const { svg } = await mermaid.render(`mmd-${++counter}`, source);
		el.innerHTML = svg;
		return true;
	} catch (error) {
		el.innerHTML = `<p class="text-sm text-red-600">Diagram error: ${String(error.message || error).slice(0, 200).replace(/</g, "&lt;")}</p>`;
		return false;
	}
}
