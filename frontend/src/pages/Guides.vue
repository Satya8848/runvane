<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<p class="eyebrow">Guides</p>
	<h1 class="mt-1 font-display text-3xl font-bold">Setup &amp; configuration guides</h1>
	<p class="mt-2 max-w-2xl text-ink-500">From Linux and networking to Kubernetes, CI/CD, every major cloud, security and architecture. Each guide is split into tabs: overview, key concepts, best practices, common mistakes, commands and recommendations.</p>

	<section class="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
		<router-link v-for="c in clouds" :key="c.to" :to="c.to" class="card group !p-4 transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md">
			<p class="eyebrow">{{ c.eyebrow }}</p>
			<h2 class="mt-1 font-display text-lg font-semibold group-hover:text-brand-700 dark:group-hover:text-brand-300">{{ c.title }}</h2>
			<p class="mt-1 text-sm text-ink-500">{{ c.text }}</p>
		</router-link>
	</section>

	<div class="mt-8 flex flex-wrap items-center gap-3">
		<div class="flex min-w-0 flex-1 gap-1 overflow-x-auto rounded-2xl border border-ink-100 p-1 [scrollbar-width:none] dark:border-ink-800" role="tablist" aria-label="Guide categories">
			<button v-for="c in categories" :key="c.name" role="tab" :aria-selected="category === c.name"
				class="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-xl px-3.5 py-2 text-sm font-medium transition"
				:class="category === c.name ? 'bg-brand-600 text-white shadow-sm' : 'text-ink-600 hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800'" @click="pick(c.name)">
				{{ c.name }}<span class="rounded-full px-1.5 text-[11px]" :class="category === c.name ? 'bg-white/20' : 'bg-ink-100 dark:bg-ink-800'">{{ c.count }}</span>
			</button>
		</div>
		<input v-model="q" class="input !w-56" placeholder="Filter guides…" aria-label="Filter guides" />
	</div>

	<div class="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3" role="tabpanel">
		<router-link v-for="g in shown" :key="g.name" :to="`/guides/${g.name}`" class="card group block !p-4 transition hover:border-brand-300 hover:shadow-md">
			<span class="chip">{{ g.category }}</span>
			<h3 class="mt-2 font-semibold group-hover:text-brand-700 dark:group-hover:text-brand-300">{{ g.title }}</h3>
			<p class="mt-1 line-clamp-3 text-sm text-ink-500">{{ g.intro }}</p>
		</router-link>
		<p v-if="!shown.length" class="text-sm text-ink-500">No guide matches that filter.</p>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call, KB } from "../api.js";

const route = useRoute();
const router = useRouter();
const guides = ref([]);
const q = ref("");
const category = ref(route.query.c || "All");
const ORDER = ["Foundations", "Build & run", "Delivery", "Cloud", "Cloud services explained", "Operate", "Secure", "Design"];
const clouds = [
	{ to: "/guides/cloud-comparison", eyebrow: "Start here", title: "Which cloud service should I use?", text: "Every job mapped across AWS, Azure and Google Cloud, plus how to choose a cloud." },
	{ to: "/guides/aws-services", eyebrow: "AWS", title: "AWS services explained", text: "29 services in plain words: when to use, equivalents, first command, best practice." },
	{ to: "/guides/azure-services", eyebrow: "Azure", title: "Azure services explained", text: "22 services from Entra ID and managed identities to AKS, Key Vault and DevOps." },
	{ to: "/guides/gcp-services", eyebrow: "Google Cloud", title: "Google Cloud services explained", text: "18 services from IAM and Cloud Run to GKE, BigQuery and Cloud Armor." },
];
const categories = computed(() => {
	const names = [...new Set(guides.value.map((g) => g.category))].sort((a, b) => (ORDER.indexOf(a) + 99) % 99 - (ORDER.indexOf(b) + 99) % 99);
	return [{ name: "All", count: guides.value.length }, ...names.map((name) => ({ name, count: guides.value.filter((g) => g.category === name).length }))];
});
const shown = computed(() => guides.value.filter((g) => (category.value === "All" || g.category === category.value)
	&& (!q.value || `${g.title} ${g.intro}`.toLowerCase().includes(q.value.toLowerCase()))));

/**
 * Show a category tab and keep it in the URL.
 *
 * @param {string} name - Category.
 * @returns {void}
 */
function pick(name) {
	category.value = name;
	router.replace({ query: name === "All" ? {} : { c: name } });
}

onMounted(async () => (guides.value = await call(`${KB}.guides`)));
</script>
