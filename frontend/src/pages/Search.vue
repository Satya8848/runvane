<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<form class="flex max-w-3xl gap-2" @submit.prevent="$router.replace({ query: { q: text, kind } })">
		<input v-model="text" class="input !py-3" placeholder="Search everything" aria-label="Search" />
		<button class="btn btn-primary">Search</button>
	</form>
	<div class="mt-4 flex flex-wrap gap-2">
		<button v-for="k in kinds" :key="k.value" class="chip" :class="kind === k.value ? '!border-brand-500 !text-brand-700 dark:!text-brand-300' : ''" @click="$router.replace({ query: { q: text, kind: k.value || undefined } })">{{ k.label }}</button>
	</div>
	<p class="mt-6 text-sm text-ink-500" v-if="$route.query.q">{{ hits.length }} results for “{{ $route.query.q }}”</p>
	<div class="mt-3 grid gap-3">
		<router-link v-for="h in hits" :key="h.id" :to="h.url" class="card block !p-4 hover:border-brand-300">
			<div class="flex items-center gap-2"><span class="chip">{{ h.kind }}</span><span class="font-medium" v-html="h.title_html || h.title"></span></div>
			<p class="mt-1 line-clamp-2 text-sm text-ink-500" v-html="h.excerpt_html || h.excerpt"></p>
		</router-link>
	</div>
	<div v-if="$route.query.q && !hits.length && !loading" class="card mt-4 max-w-3xl">
		<h2 class="font-display text-lg font-semibold">No match yet</h2>
		<p class="mt-1 text-sm text-ink-500">Get an answer another way:</p>
		<div class="mt-3 flex flex-wrap gap-2"><router-link class="btn btn-primary" :to="{ path: '/ai', query: { q: $route.query.q } }">Ask the AI</router-link><router-link class="btn" :to="{ path: '/ask', query: { title: $route.query.q } }">Ask the community</router-link></div>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { call, KB } from "../api.js";

const route = useRoute();
const text = ref(route.query.q || "");
const kind = ref(route.query.kind || "");
const hits = ref([]);
const loading = ref(false);
const kinds = [{ value: "", label: "All" }, { value: "playbook", label: "Playbooks" }, { value: "question", label: "Questions" }, { value: "guide", label: "Guides" }, { value: "term", label: "Glossary" }, { value: "interview", label: "Interview" }, { value: "diagram", label: "Boards" }];
watch(() => route.query, async (query) => {
	text.value = query.q || "";
	kind.value = query.kind || "";
	if (!query.q) return (hits.value = []);
	loading.value = true;
	hits.value = (await call(`${KB}.search`, { q: query.q, kind: query.kind, limit: 40 })).hits;
	loading.value = false;
}, { immediate: true });
</script>
