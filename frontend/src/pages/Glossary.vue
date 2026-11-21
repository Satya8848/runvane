<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<p class="eyebrow">Glossary</p>
	<h1 class="mt-1 font-display text-3xl font-bold">{{ terms.length }} key terms</h1>
	<input v-model="q" class="input mt-4 max-w-md" placeholder="Filter terms…" aria-label="Filter terms" />
	<div class="mt-6 grid gap-3 md:grid-cols-2">
		<div v-for="t in shown" :key="t.name" :id="slug(t.name)" class="card scroll-mt-24">
			<div class="flex items-center justify-between gap-2"><h2 class="font-semibold">{{ t.name }}</h2><span class="chip">{{ t.category }}</span></div>
			<p class="mt-1 text-sm font-medium">{{ t.short_definition }}</p>
			<p class="mt-2 text-sm text-ink-500">{{ t.explanation }}</p>
		</div>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import { call, KB } from "../api.js";
const terms = ref([]);
const q = ref("");
const shown = computed(() => terms.value.filter((t) => !q.value || `${t.name} ${t.short_definition} ${t.category}`.toLowerCase().includes(q.value.toLowerCase())));
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "_");
onMounted(async () => { terms.value = await call(`${KB}.glossary`); if (location.hash) setTimeout(() => document.querySelector(location.hash)?.scrollIntoView(), 50); });
</script>
