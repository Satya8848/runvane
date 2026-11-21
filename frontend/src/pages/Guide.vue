<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<!-- A guide shown as tabs: one tab per "##" section, with "###" items as cards. -->
<template>
	<article v-if="g" class="mx-auto max-w-5xl">
		<router-link to="/guides" class="eyebrow">{{ g.category }}</router-link>
		<h1 class="mt-2 text-balance font-display text-3xl font-bold sm:text-4xl">{{ g.title }}</h1>
		<p class="mt-3 max-w-3xl text-lg text-ink-600 dark:text-ink-300">{{ g.intro }}</p>

		<div class="sticky top-[57px] z-20 -mx-4 mt-6 border-b border-ink-100 bg-white/95 px-4 backdrop-blur dark:border-ink-800 dark:bg-ink-950/95 sm:mx-0 sm:px-0 md:top-[61px]">
			<div class="tabfade"><div class="flex gap-1 overflow-x-auto py-2 pr-10 [scrollbar-width:none]" role="tablist" aria-label="Guide sections" @keydown.right.prevent="step(1)" @keydown.left.prevent="step(-1)">
				<button v-for="(t, i) in tabs" :key="t.id" :id="`tab-${t.id}`" role="tab" :aria-selected="active === i" :aria-controls="`panel-${t.id}`" :tabindex="active === i ? 0 : -1"
					class="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-xl px-3.5 py-2 text-sm font-medium transition"
					:class="active === i ? 'bg-brand-600 text-white shadow-sm' : 'text-ink-600 hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800'" @click="select(i)">
					<span aria-hidden="true">{{ t.icon }}</span>{{ t.label }}<span v-if="t.count" class="rounded-full px-1.5 text-[11px]" :class="active === i ? 'bg-white/20' : 'bg-ink-100 dark:bg-ink-800'">{{ t.count }}</span>
				</button>
			</div></div>
		</div>

		<section v-for="(t, i) in tabs" v-show="active === i" :key="t.id" :id="`panel-${t.id}`" role="tabpanel" :aria-labelledby="`tab-${t.id}`" class="mt-6">
			<div v-if="i === 0 && g.diagram" class="mb-6"><h2 class="font-display text-xl font-bold">Architecture</h2><Markdown :markdown="'```mermaid\n' + g.diagram + '\n```'" /></div>
			<div v-if="t.cards" class="grid gap-4 lg:grid-cols-2"><div v-for="(c, j) in t.cards" :key="j" class="card min-w-0"><Markdown :html="c" /></div></div>
			<Markdown v-else :html="t.html" />
			<div class="mt-8 flex items-center justify-between gap-3 border-t border-ink-100 pt-4 text-sm dark:border-ink-800">
				<button v-if="i > 0" class="btn" @click="select(i - 1)">← {{ tabs[i - 1].label }}</button><span v-else></span>
				<button v-if="i < tabs.length - 1" class="btn btn-primary" @click="select(i + 1)">{{ tabs[i + 1].label }} →</button>
				<router-link v-else :to="{ path: '/ai', query: { q: `Help me apply: ${g.title}` } }" class="btn btn-primary">Ask the AI about this →</router-link>
			</div>
		</section>
	</article>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call, KB } from "../api.js";
import Markdown from "../components/Markdown.vue";

const route = useRoute();
const router = useRouter();
const g = ref(null);
const active = ref(0);
const ICONS = [["overview", "📘"], ["concept", "🧩"], ["best", "✅"], ["mistake", "⚠️"], ["setup", "⌨️"], ["command", "⌨️"], ["recommend", "🎯"],
	["identity", "🔐"], ["network", "🌐"], ["compute", "🖥️"], ["storage", "🗄️"], ["database", "🛢️"], ["serverless", "⚡"], ["container", "📦"],
	["integration", "🔗"], ["operation", "📈"], ["security", "🛡️"], ["iac", "📜"], ["cost", "💰"], ["delivery", "🚀"], ["analytics", "📊"], ["how to choose", "🧭"], ["other", "☁️"]];

/**
 * Split the guide HTML into tabs at each <h2>; inside a tab, each <h3> and what follows becomes a card.
 */
const tabs = computed(() => {
	if (!g.value) return [];
	const doc = new DOMParser().parseFromString(`<div>${g.value.html}</div>`, "text/html").body.firstChild;
	const groups = [{ label: "Overview", nodes: [] }];
	for (const node of [...doc.childNodes]) {
		if (node.nodeName === "H2") groups.push({ label: node.textContent.trim(), nodes: [] });
		else groups[groups.length - 1].nodes.push(node);
	}
	return groups
		.filter((grp, i) => i > 0 || grp.nodes.some((n) => n.textContent.trim()) || g.value.diagram)
		.map((grp, i) => {
			const wrap = document.createElement("div");
			grp.nodes.forEach((n) => wrap.appendChild(n.cloneNode(true)));
			const cards = splitCards(wrap);
			const key = grp.label.toLowerCase();
			return { id: `${i}-${key.replace(/[^a-z0-9]+/g, "-")}`, label: grp.label, icon: (ICONS.find(([k]) => key.includes(k)) || [null, "📄"])[1],
				html: wrap.innerHTML, cards, count: cards ? cards.length : countItems(wrap) };
		});
});

/**
 * Turn "### item + its content" runs into card HTML strings, or null when a tab has no items.
 *
 * @param {HTMLElement} wrap - Tab content.
 * @returns {string[]|null} Card HTML strings.
 */
function splitCards(wrap) {
	const nodes = [...wrap.childNodes];
	if (!nodes.some((n) => n.nodeName === "H3")) return null;
	const cards = [];
	let lead = "";
	for (const node of nodes) {
		if (node.nodeName === "H3") cards.push("");
		const html = node.outerHTML ?? node.textContent;
		if (cards.length) cards[cards.length - 1] += html; else lead += html;
	}
	if (lead.replace(/<[^>]+>/g, "").trim()) cards.unshift(lead);
	return cards;
}

/**
 * Number of list items in a tab (shown as a badge), or 0.
 *
 * @param {HTMLElement} wrap - Tab content.
 * @returns {number} Count.
 */
function countItems(wrap) {
	const list = wrap.querySelector("ul, ol, tbody");
	return list ? list.children.length : 0;
}

/**
 * Show a tab and keep it in the URL.
 *
 * @param {number} i - Tab index.
 * @returns {void}
 */
function select(i) {
	active.value = i;
	router.replace({ query: i ? { tab: tabs.value[i].id.split("-").slice(1).join("-") } : {} });
	nextTick(() => document.getElementById(`tab-${tabs.value[i].id}`)?.scrollIntoView({ block: "nearest", inline: "center" }));
}

/**
 * Keyboard: move to the next or previous tab.
 *
 * @param {number} delta - +1 or -1.
 * @returns {void}
 */
function step(delta) {
	select((active.value + delta + tabs.value.length) % tabs.value.length);
	nextTick(() => document.getElementById(`tab-${tabs.value[active.value].id}`)?.focus());
}

watch(() => route.params.slug, async (slug) => {
	if (!slug) return;
	g.value = await call(`${KB}.guide`, { slug });
	document.title = `${g.value.title} · Runvane`;
	await nextTick();
	const wanted = route.query.tab;
	const found = wanted ? tabs.value.findIndex((t) => t.id.split("-").slice(1).join("-") === wanted) : 0;
	active.value = found > 0 ? found : 0;
}, { immediate: true });
</script>
