<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<p class="eyebrow">Playbooks</p>
	<h1 class="mt-1 font-display text-3xl font-bold">Real problems, step-by-step fixes</h1>
	<p class="mt-2 max-w-2xl text-ink-500">Each playbook: symptoms, likely causes, diagnosis commands, the fix and how to prevent it.</p>
	<div class="mt-6 space-y-10">
		<section v-for="t in tracks" :key="t.slug">
			<div class="flex items-baseline justify-between"><h2 class="font-display text-xl font-bold">{{ t.title }}</h2><router-link :to="`/t/${t.slug}`" class="text-sm text-brand-600">All for this role →</router-link></div>
			<div class="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
				<router-link v-for="p in t.items" :key="p.name" :to="`/playbooks/${p.name}`" class="card block !p-4 hover:border-brand-300">
					<div class="flex items-center gap-2"><SeverityDot :level="p.severity" /><h3 class="font-semibold">{{ p.title }}</h3></div>
					<p class="mt-1 line-clamp-2 text-sm text-ink-500">{{ p.summary }}</p>
				</router-link>
			</div>
		</section>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { call, KB } from "../api.js";
import SeverityDot from "../components/SeverityDot.vue";

const tracks = ref([]);
onMounted(async () => {
	const home = await call(`${KB}.home`);
	tracks.value = await Promise.all(home.tracks.map(async (t) => ({ ...t, items: (await call(`${KB}.track`, { slug: t.slug })).playbooks })));
});
</script>
