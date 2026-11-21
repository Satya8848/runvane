<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<p class="eyebrow">Interview prep</p>
	<h1 class="mt-1 font-display text-3xl font-bold">{{ items.length }} questions with model answers</h1>
	<div class="mt-4 flex flex-wrap items-center gap-2">
		<select v-model="topic" class="input !w-auto" @change="load" aria-label="Topic"><option value="">All topics</option><option v-for="t in topics" :key="t">{{ t }}</option></select>
		<select v-model="level" class="input !w-auto" @change="load" aria-label="Level"><option value="">All levels</option><option>Junior</option><option>Mid</option><option>Senior</option></select>
		<label class="flex items-center gap-2 text-sm"><input type="checkbox" v-model="quiz" /> Quiz mode (hide answers)</label>
	</div>
	<div class="mt-6 space-y-3">
		<div v-for="it in items" :key="it.name" class="card">
			<div class="flex flex-wrap items-center gap-2 text-xs"><span class="chip" :class="lvl[it.level]">{{ it.level }}</span><span class="text-ink-400">{{ it.topic }}</span></div>
			<h2 class="mt-2 font-semibold">{{ it.question }}</h2>
			<button v-if="quiz && !open[it.name]" class="btn mt-3" @click="open[it.name] = true">Show answer</button>
			<div v-else class="mt-2"><Markdown :html="it.answer_html" /></div>
		</div>
	</div>
</template>
<script setup>
import { onMounted, reactive, ref } from "vue";
import { call, KB } from "../api.js";
import Markdown from "../components/Markdown.vue";
const items = ref([]);
const topics = ref([]);
const topic = ref("");
const level = ref("");
const quiz = ref(false);
const open = reactive({});
const lvl = { Junior: "!border-emerald-400 !text-emerald-700", Mid: "!border-amber-400 !text-amber-700", Senior: "!border-red-400 !text-red-700" };
async function load() { const d = await call(`${KB}.interview`, { topic: topic.value, level: level.value }); items.value = d.items; topics.value = d.topics; }
onMounted(load);
</script>
