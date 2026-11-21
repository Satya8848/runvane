<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div><p class="eyebrow">Community</p><h1 class="mt-1 font-display text-3xl font-bold">Questions</h1></div>
		<router-link to="/ask" class="btn btn-primary">Ask a question</router-link>
	</div>
	<div class="mt-5 flex flex-wrap gap-2">
		<button v-for="s in sorts" :key="s.value" class="chip" :class="sort === s.value ? '!border-brand-500 !text-brand-700 dark:!text-brand-300' : ''" @click="sort = s.value; load()">{{ s.label }}</button>
		<select v-model="track" class="input ml-auto !w-auto !py-1" @change="load" aria-label="Role"><option value="">All roles</option><option v-for="t in tracks" :key="t.slug" :value="t.slug">{{ t.title }}</option></select>
	</div>
	<div class="mt-4 divide-y divide-ink-100 rounded-2xl border border-ink-100 dark:divide-ink-800 dark:border-ink-800">
		<router-link v-for="q in items" :key="q.name" :to="`/q/${q.name}`" class="flex gap-4 p-4 hover:bg-ink-50 dark:hover:bg-ink-900">
			<div class="grid w-24 shrink-0 grid-cols-2 gap-1 text-center text-xs text-ink-500">
				<div><b class="block text-base text-ink-800 dark:text-ink-100">{{ q.votes || 0 }}</b>votes</div>
				<div :class="q.status === 'Answered' ? 'rounded-lg bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200' : ''"><b class="block text-base">{{ q.answer_count || 0 }}</b>answers</div>
			</div>
			<div class="min-w-0"><h2 class="font-medium">{{ q.title }}</h2><div class="mt-1 flex flex-wrap gap-1"><span v-if="q.role_track" class="chip">{{ q.role_track }}</span><span v-for="t in (q.tags || '').split(',').filter(Boolean)" :key="t" class="chip">{{ t }}</span></div></div>
		</router-link>
		<p v-if="!items.length" class="p-6 text-center text-sm text-ink-500">No questions here yet. <router-link to="/ask" class="text-brand-600">Ask the first one.</router-link></p>
	</div>
</template>
<script setup>
import { onMounted, ref } from "vue";
import { call, FORUM, KB } from "../api.js";
const items = ref([]);
const tracks = ref([]);
const sort = ref("newest");
const track = ref("");
const sorts = [{ value: "newest", label: "Newest" }, { value: "votes", label: "Top" }, { value: "unanswered", label: "Unanswered" }, { value: "active", label: "Active" }];
async function load() { items.value = (await call(`${FORUM}.questions`, { sort: sort.value, track: track.value })).items; }
onMounted(async () => { load(); tracks.value = (await call(`${KB}.home`)).tracks; });
</script>
