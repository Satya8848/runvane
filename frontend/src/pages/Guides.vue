<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<p class="eyebrow">Guides</p>
	<h1 class="mt-1 font-display text-3xl font-bold">Setup &amp; configuration guides</h1>
	<p class="mt-2 max-w-2xl text-ink-500">From Linux and networking to Kubernetes, CI/CD, every major cloud, security and architecture: concepts, real commands and interview questions.</p>
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
const grouped = computed(() => guides.value.reduce((acc, g) => ((acc[g.category] ||= []).push(g), acc), {}));
onMounted(async () => (guides.value = await call(`${KB}.guides`)));
</script>
