<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div v-if="p" class="grid gap-8 lg:grid-cols-[minmax(0,1fr)_280px]">
		<article class="min-w-0">
			<router-link :to="`/t/${p.role_track}`" class="eyebrow">{{ p.role_track }} playbook</router-link>
			<h1 class="mt-2 text-balance font-display text-3xl font-bold sm:text-4xl">{{ p.title }}</h1>
			<p class="mt-3 text-lg text-ink-600 dark:text-ink-300" v-html="inlineCode(p.summary)"></p>
			<div class="mt-3 flex flex-wrap items-center gap-2 text-sm"><SeverityDot :level="p.severity" /><span>{{ p.severity }} severity</span><span class="text-ink-300">·</span><span class="text-ink-500">{{ p.views }} {{ p.views === 1 ? "view" : "views" }}</span><span v-for="t in p.tags" :key="t" class="chip">{{ t }}</span></div>
			<section v-for="s in sections" :key="s.key" :id="s.key" class="mt-8 scroll-mt-24">
				<h2 class="flex items-center gap-2 font-display text-xl font-bold"><span class="grid h-7 w-7 place-items-center rounded-lg text-sm" :class="s.cls">{{ s.icon }}</span>{{ s.label }}</h2>
				<div class="mt-3"><Markdown :html="p.sections[s.key]" /></div>
			</section>
		</article>
		<aside class="space-y-4 lg:sticky lg:top-24 lg:self-start">
			<div class="card">
				<h2 class="font-semibold">Still stuck?</h2>
				<p class="mt-1 text-sm text-ink-500">Paste your own logs or config and get an analysis.</p>
				<router-link class="btn btn-primary mt-3 w-full justify-center" :to="{ path: '/ai', query: { q: `Help me with: ${p.title}`, role: p.role_track } }">Analyse with AI</router-link>
				<router-link class="btn mt-2 w-full justify-center" :to="{ path: '/ask', query: { title: p.title, role: p.role_track } }">Ask the community</router-link>
			</div>
			<nav class="card text-sm"><h2 class="font-semibold">On this page</h2><a v-for="s in sections" :key="s.key" :href="`#${s.key}`" class="mt-2 block text-ink-500 hover:text-brand-600">{{ s.label }}</a></nav>
			<div class="card" v-if="p.related.length"><h2 class="font-semibold">Related</h2><router-link v-for="r in p.related" :key="r.id" :to="r.url" class="mt-2 block text-sm text-ink-600 hover:text-brand-600 dark:text-ink-300"><span class="chip mr-1">{{ r.kind }}</span>{{ r.title }}</router-link></div>
		</aside>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { call, KB } from "../api.js";
import Markdown from "../components/Markdown.vue";
import SeverityDot from "../components/SeverityDot.vue";

const route = useRoute();
const p = ref(null);
/**
 * Escape text and turn `code` spans into <code>.
 *
 * @param {string} text - Plain summary.
 * @returns {string} Safe HTML.
 */
const inlineCode = (text) => String(text || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]).replace(/`([^`]+)`/g, '<code class="rounded bg-ink-100 px-1.5 py-0.5 font-mono text-[0.9em] dark:bg-ink-800">$1</code>');
const sections = [
	{ key: "symptoms", label: "Symptoms", icon: "!", cls: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200" },
	{ key: "causes", label: "Likely causes", icon: "?", cls: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200" },
	{ key: "diagnose", label: "Diagnose", icon: "⌕", cls: "bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200" },
	{ key: "fix", label: "Fix", icon: "✓", cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200" },
	{ key: "prevent", label: "Prevent it", icon: "↻", cls: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-200" },
];
watch(() => route.params.slug, async (slug) => { if (slug) { p.value = await call(`${KB}.playbook`, { slug }); document.title = `${p.value.title} · Runvane`; } }, { immediate: true });
</script>
