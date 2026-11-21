<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<p class="eyebrow">Guides</p>
	<h1 class="mt-1 font-display text-3xl font-bold">Setup &amp; configuration guides</h1>
	<p class="mt-2 max-w-2xl text-ink-500">From Linux and networking to Kubernetes, CI/CD, every major cloud, security and architecture: concepts, real commands and interview questions.</p>
	<section class="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
		<router-link v-for="c in clouds" :key="c.to" :to="c.to" class="card group !p-4 transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md">
			<p class="eyebrow">{{ c.eyebrow }}</p>
			<h2 class="mt-1 font-display text-lg font-semibold group-hover:text-brand-700 dark:group-hover:text-brand-300">{{ c.title }}</h2>
			<p class="mt-1 text-sm text-ink-500">{{ c.text }}</p>
		</router-link>
	</section>
	<section v-for="(items, group) in grouped" :key="group" class="mt-8">
		<h2 class="font-display text-xl font-bold">{{ group }}</h2>
		<div class="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
			<router-link v-for="g in items" :key="g.name" :to="`/guides/${g.name}`" class="card block !p-4 hover:border-brand-300"><h3 class="font-semibold">{{ g.title }}</h3><p class="mt-1 line-clamp-2 text-sm text-ink-500">{{ g.intro }}</p></router-link>
		</div>
	</section>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import { call, KB } from "../api.js";
const guides = ref([]);
const clouds = [
	{ to: "/guides/cloud-comparison", eyebrow: "Start here", title: "Which cloud service should I use?", text: "Every job mapped across AWS, Azure and Google Cloud, plus how to choose a cloud." },
	{ to: "/guides/aws-services", eyebrow: "AWS", title: "AWS services explained", text: "29 services in plain words: when to use, equivalents, first command, best practice." },
	{ to: "/guides/azure-services", eyebrow: "Azure", title: "Azure services explained", text: "22 services from Entra ID and managed identities to AKS, Key Vault and DevOps." },
	{ to: "/guides/gcp-services", eyebrow: "Google Cloud", title: "Google Cloud services explained", text: "18 services from IAM and Cloud Run to GKE, BigQuery and Cloud Armor." },
];
const grouped = computed(() => guides.value.reduce((acc, g) => ((acc[g.category] ||= []).push(g), acc), {}));
onMounted(async () => (guides.value = await call(`${KB}.guides`)));
</script>
