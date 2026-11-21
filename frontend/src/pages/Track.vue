<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div v-if="data">
		<div class="rounded-3xl border border-ink-100 p-8 dark:border-ink-800" :style="{ background: `linear-gradient(135deg, ${data.track.color}18, transparent)` }">
			<p class="eyebrow">Role</p>
			<h1 class="mt-2 font-display text-4xl font-bold">{{ data.track.title }}</h1>
			<p class="mt-2 max-w-2xl text-lg text-ink-600 dark:text-ink-300">{{ data.track.tagline }}</p>
			<div class="mt-5 flex flex-wrap gap-2"><router-link class="btn btn-primary" :to="{ path: '/ai', query: { role: data.track.slug } }">Analyse something with AI</router-link><router-link class="btn" :to="{ path: '/ask', query: { role: data.track.slug } }">Ask a question</router-link></div>
		</div>
		<h2 class="mt-10 font-display text-2xl font-bold">Day-to-day problems</h2>
		<div class="mt-4 grid gap-3 md:grid-cols-2">
			<router-link v-for="p in data.playbooks" :key="p.name" :to="`/playbooks/${p.name}`" class="card block hover:border-brand-300">
				<div class="flex items-center gap-2"><SeverityDot :level="p.severity" /><h3 class="font-semibold">{{ p.title }}</h3></div>
				<p class="mt-1 text-sm text-ink-500">{{ p.summary }}</p>
				<div class="mt-3 flex flex-wrap gap-1"><span v-for="t in (p.tags || '').split(',').filter(Boolean)" :key="t" class="chip">{{ t.trim() }}</span></div>
			</router-link>
		</div>
		<h2 class="mt-10 font-display text-2xl font-bold">Recent questions</h2>
		<div class="mt-3 space-y-2">
			<router-link v-for="q in data.questions" :key="q.name" :to="`/q/${q.name}`" class="card block !p-4 hover:border-brand-300">{{ q.title }} <span class="text-sm text-ink-400">· {{ q.answer_count }} answers</span></router-link>
			<p v-if="!data.questions.length" class="text-sm text-ink-500">None yet for this role.</p>
		</div>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { call, KB } from "../api.js";
import SeverityDot from "../components/SeverityDot.vue";

const route = useRoute();
const data = ref(null);
watch(() => route.params.slug, async (slug) => { if (slug) { data.value = await call(`${KB}.track`, { slug }); document.title = `${data.value.track.title} · StackPilot`; } }, { immediate: true });
</script>
