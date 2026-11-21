<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="fixed inset-0 z-40 flex items-start justify-center bg-ink-950/50 p-4 pt-[12vh] backdrop-blur-sm" @click.self="$emit('close')" @keydown.esc="$emit('close')">
		<div class="w-full max-w-2xl overflow-hidden rounded-2xl border border-ink-100 bg-white shadow-2xl dark:border-ink-800 dark:bg-ink-900" role="dialog" aria-label="Search">
			<input ref="box" v-model="q" class="w-full border-b border-ink-100 bg-transparent px-5 py-4 text-base outline-none dark:border-ink-800" placeholder="Describe the problem: 502 after deploy, replication lag, OIDC…" @keydown.down.prevent="move(1)" @keydown.up.prevent="move(-1)" @keydown.enter.prevent="go(hits[active])" @keydown.esc="$emit('close')" aria-label="Search everything" />
			<ul class="max-h-[60vh] overflow-y-auto p-2">
				<li v-for="(hit, i) in hits" :key="hit.id">
					<button class="flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left" :class="i === active ? 'bg-brand-50 dark:bg-brand-900/40' : ''" @mouseenter="active = i" @click="go(hit)">
						<span class="chip mt-0.5 shrink-0">{{ hit.kind }}</span>
						<span class="min-w-0"><span class="block font-medium" v-html="hit.title_html || escape(hit.title)"></span><span class="line-clamp-2 block text-sm text-ink-500" v-html="hit.excerpt_html || escape(hit.excerpt)"></span></span>
					</button>
				</li>
				<li v-if="q && !hits.length && !loading" class="px-3 py-6 text-center text-sm text-ink-500">Nothing yet. <router-link class="text-brand-600" :to="{ path: '/ai', query: { q } }" @click="$emit('close')">Ask the AI</router-link> or <router-link class="text-brand-600" :to="{ path: '/ask', query: { title: q } }" @click="$emit('close')">ask the community</router-link>.</li>
			</ul>
			<div class="flex justify-between border-t border-ink-100 px-4 py-2 text-xs text-ink-400 dark:border-ink-800"><span>↑↓ to move · Enter to open · Esc to close</span><router-link :to="{ path: '/search', query: { q } }" @click="$emit('close')" class="text-brand-600">All results →</router-link></div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { call, KB } from "../api.js";

const emit = defineEmits(["close"]);
const router = useRouter();
const box = ref(null);
const q = ref("");
const hits = ref([]);
const active = ref(0);
const loading = ref(false);
let timer;

watch(q, () => {
	clearTimeout(timer);
	timer = setTimeout(async () => {
		if (!q.value.trim()) return (hits.value = []);
		loading.value = true;
		hits.value = (await call(`${KB}.search`, { q: q.value, limit: 12 }).catch(() => ({ hits: [] }))).hits;
		loading.value = false;
		active.value = 0;
	}, 150);
});

/**
 * Move the keyboard selection.
 *
 * @param {number} step - +1 or -1.
 * @returns {void}
 */
const move = (step) => (active.value = Math.max(0, Math.min(hits.value.length - 1, active.value + step)));

/**
 * Open a hit.
 *
 * @param {object} hit - Search hit.
 * @returns {void}
 */
function go(hit) {
	if (!hit) return;
	emit("close");
	router.push(hit.url);
}

const escape = (text) => String(text || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
onMounted(() => nextTick(() => box.value?.focus()));
</script>
