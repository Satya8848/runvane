<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<section class="relative overflow-hidden rounded-3xl border border-ink-100 bg-gradient-to-br from-brand-50 via-white to-teal-50 px-6 py-12 dark:border-ink-800 dark:from-ink-900 dark:via-ink-950 dark:to-ink-900 sm:px-12">
		<p class="eyebrow">For DevOps · DevSecOps · Architects · Programmers · Linux admins · DBAs · Cloud</p>
		<h1 class="mt-3 max-w-3xl text-balance font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">What are you stuck on today?</h1>
		<p class="mt-3 max-w-2xl text-lg text-ink-600 dark:text-ink-300">Search real-world playbooks, paste a log for AI analysis, ask the community, or draw your architecture and get it reviewed.</p>
		<form class="mt-7 flex max-w-2xl flex-col gap-2 sm:flex-row" @submit.prevent="$router.push({ path: '/search', query: { q } })">
			<input v-model="q" class="input !py-3.5 !text-base" placeholder="e.g. 502 after deploy, disk full, replication lag, OIDC to AWS" aria-label="Describe your problem" />
			<button class="btn btn-primary justify-center !px-6 !py-3.5">Search</button>
		</form>
		<div class="mt-4 flex flex-wrap gap-2 text-sm">
			<router-link v-for="s in suggestions" :key="s" :to="{ path: '/search', query: { q: s } }" class="chip hover:border-brand-400 hover:text-brand-700">{{ s }}</router-link>
		</div>
	</section>

	<section class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<router-link v-for="f in features" :key="f.to" :to="f.to" class="card group transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md">
			<div class="text-2xl" aria-hidden="true">{{ f.icon }}</div>
			<h2 class="mt-3 font-display text-lg font-semibold group-hover:text-brand-700 dark:group-hover:text-brand-300">{{ f.title }}</h2>
			<p class="mt-1 text-sm text-ink-500 dark:text-ink-400">{{ f.text }}</p>
		</router-link>
	</section>

	<section class="mt-12">
		<div class="flex items-end justify-between"><h2 class="font-display text-2xl font-bold">Pick your role</h2><span class="text-sm text-ink-500" v-if="data">{{ data.totals.playbook }} playbooks · {{ data.totals.config_guide }} guides · {{ data.totals.interview_item }} interview questions</span></div>
		<div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
			<router-link v-for="t in data?.tracks || []" :key="t.slug" :to="`/t/${t.slug}`" class="card group relative overflow-hidden transition hover:shadow-md">
				<span class="absolute inset-x-0 top-0 h-1" :style="{ background: t.color }"></span>
				<h3 class="font-display text-lg font-semibold">{{ t.title }}</h3>
				<p class="mt-1 text-sm text-ink-500 dark:text-ink-400">{{ t.tagline }}</p>
				<p class="mt-4 text-xs font-medium text-ink-400">{{ t.playbooks }} playbooks →</p>
			</router-link>
		</div>
	</section>

	<section class="mt-12 grid gap-6 lg:grid-cols-2">
		<div>
			<h2 class="font-display text-xl font-bold">Most-used playbooks</h2>
			<div class="mt-3 space-y-2">
				<router-link v-for="p in data?.popular || []" :key="p.name" :to="`/playbooks/${p.name}`" class="card block !p-4 hover:border-brand-300">
					<div class="flex items-center gap-2"><SeverityDot :level="p.severity" /><span class="font-medium">{{ p.title }}</span></div>
					<p class="mt-1 line-clamp-1 text-sm text-ink-500">{{ p.summary }}</p>
				</router-link>
			</div>
		</div>
		<div>
			<div class="flex items-center justify-between"><h2 class="font-display text-xl font-bold">Latest questions</h2><router-link to="/ask" class="btn btn-primary !py-1.5">Ask</router-link></div>
			<div class="mt-3 space-y-2">
				<router-link v-for="q in data?.questions || []" :key="q.name" :to="`/q/${q.name}`" class="card flex items-center gap-4 !p-4 hover:border-brand-300">
					<div class="w-14 shrink-0 text-center text-xs text-ink-500"><b class="block text-lg text-ink-800 dark:text-ink-100">{{ q.answer_count }}</b>answers</div>
					<span class="font-medium">{{ q.title }}</span>
				</router-link>
				<div v-if="data && !data.questions.length" class="card text-sm text-ink-500">No questions yet. Be the first: <router-link class="text-brand-600" to="/ask">ask one</router-link>.</div>
			</div>
		</div>
	</section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { call, KB } from "../api.js";
import SeverityDot from "../components/SeverityDot.vue";

const q = ref("");
const data = ref(null);
const suggestions = ["502 after deploy", "disk full", "replication lag", "secret leaked", "pods pending", "slow query", "OOMKilled"];
const features = [
	{ to: "/playbooks", icon: "🧭", title: "Problem playbooks", text: "Symptoms → diagnose → fix → prevent, with copy-ready commands." },
	{ to: "/ai", icon: "✨", title: "AI analysis", text: "Paste logs, errors, configs or SQL. Secrets are masked before anything is sent." },
	{ to: "/q", icon: "💬", title: "Community forum", text: "Ask, answer, vote. Every new question gets an AI first draft." },
	{ to: "/board", icon: "🗺️", title: "Architecture board", text: "Start from templates, draw with text, get an AI design review." },
];
onMounted(async () => (data.value = await call(`${KB}.home`)));
</script>
