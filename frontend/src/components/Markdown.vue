<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<!-- Renders server HTML or Markdown: highlights code, adds copy buttons, draws mermaid blocks. -->
<template><div ref="root" class="prose-sp" v-html="html"></div></template>

<script setup>
import DOMPurify from "dompurify";
import hljs from "highlight.js/lib/common";
import { marked } from "marked";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { renderMermaid } from "./mermaid.js";

const props = defineProps({ html: { type: String, default: "" }, markdown: { type: String, default: "" } });
const root = ref(null);
const html = computed(() => DOMPurify.sanitize(props.markdown ? marked.parse(props.markdown) : props.html || ""));

/**
 * Highlight code, add copy buttons and draw diagrams after render.
 *
 * @returns {Promise<void>}
 */
async function enhance() {
	await nextTick();
	if (!root.value) return;
	for (const pre of root.value.querySelectorAll("pre")) {
		const code = pre.querySelector("code");
		if (!code || pre.dataset.done) continue;
		pre.dataset.done = "1";
		if (code.classList.contains("language-mermaid")) {
			const box = document.createElement("div");
			box.className = "mermaid-box not-prose my-4 overflow-x-auto rounded-xl border border-ink-100 bg-white p-3 dark:border-ink-800 dark:bg-ink-900";
			pre.replaceWith(box);
			renderMermaid(box, code.textContent);
			continue;
		}
		hljs.highlightElement(code);
		const wrap = document.createElement("div");
		wrap.className = "codewrap";
		pre.parentNode.insertBefore(wrap, pre);
		wrap.appendChild(pre);
		const button = document.createElement("button");
		button.className = "copy";
		button.type = "button";
		button.textContent = "Copy";
		button.onclick = async () => {
			try { await navigator.clipboard.writeText(code.innerText); button.textContent = "Copied"; } catch (e) { button.textContent = "Select & copy"; }
			setTimeout(() => (button.textContent = "Copy"), 1500);
		};
		wrap.appendChild(button);
	}
}
onMounted(enhance);
watch(html, enhance);
</script>
