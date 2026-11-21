<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<article v-if="g" class="mx-auto max-w-4xl">
		<router-link to="/guides" class="eyebrow">{{ g.category }}</router-link>
		<h1 class="mt-2 font-display text-4xl font-bold">{{ g.title }}</h1>
		<p class="mt-3 text-lg text-ink-600 dark:text-ink-300">{{ g.intro }}</p>
		<div v-if="g.diagram" class="mt-6"><h2 class="font-display text-xl font-bold">Architecture</h2><Markdown :markdown="'```mermaid\n' + g.diagram + '\n```'" /></div>
		<div class="mt-6"><Markdown :html="g.html" /></div>
	</article>
</template>
<script setup>
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { call, KB } from "../api.js";
import Markdown from "../components/Markdown.vue";
const route = useRoute();
const g = ref(null);
watch(() => route.params.slug, async (slug) => { if (slug) { g.value = await call(`${KB}.guide`, { slug }); document.title = `${g.value.title} · StackPilot`; } }, { immediate: true });
</script>
