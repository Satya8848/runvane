<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div><p class="eyebrow">Architecture board</p><h1 class="mt-1 font-display text-3xl font-bold">{{ title || "Design a system" }}</h1></div>
		<div class="flex flex-wrap gap-2"><button class="btn" @click="newBoard">New</button><button class="btn" :disabled="!canEdit" @click="save">Save</button><button class="btn btn-primary" @click="review">✨ AI review</button></div>
	</div>
	<div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
		<div class="space-y-3">
			<div class="card !p-4">
				<label class="text-sm font-semibold" for="describe">Describe it, AI draws it</label>
				<div class="mt-2 flex gap-2"><input id="describe" v-model="describe" class="input" placeholder="e.g. Django app on EKS with RDS, Redis, S3 and CloudFront in two regions" /><button class="btn btn-primary shrink-0" :disabled="busy" @click="describe ? generate() : notify('Describe the system first, e.g. web app on EKS with RDS and Redis', 'bad')">{{ busy ? "Drawing…" : "Draw" }}</button></div>
			</div>
			<div class="card !p-4">
				<div class="flex items-center justify-between"><label class="text-sm font-semibold" for="code">Diagram as code (Mermaid)</label><a class="text-xs text-brand-600" href="https://mermaid.js.org/syntax/flowchart.html" target="_blank" rel="noopener">syntax</a></div>
				<textarea id="code" v-model="code" class="input mt-2 min-h-[220px] font-mono text-xs leading-relaxed" spellcheck="false"></textarea>
				<div class="mt-3 grid gap-2 sm:grid-cols-[minmax(0,1fr)_140px]"><input v-model="title" class="input" placeholder="Board title" aria-label="Board title" /><select v-model="visibility" class="input" aria-label="Visibility"><option>Private</option><option>Unlisted</option><option>Public</option></select></div>
				<input v-model="context" class="input mt-2" placeholder="Context for review: users, SLO, budget, compliance" aria-label="Review context" />
			</div>
			<div class="card !p-4"><h2 class="text-sm font-semibold">Start from a template</h2><div class="mt-2 grid gap-2 sm:grid-cols-2"><button v-for="t in templates" :key="t.name" class="rounded-xl border border-ink-100 p-3 text-left text-sm hover:border-brand-300 dark:border-ink-800" @click="useTemplate(t)"><b class="block">{{ t.name }}</b><span class="text-xs text-ink-500">{{ t.description }}</span></button></div></div>
		</div>
		<div class="space-y-4">
			<div class="card mermaid-box flex min-h-[280px] items-center justify-center overflow-auto" ref="canvas" aria-label="Diagram preview"></div>
			<div v-if="reviewResult" class="card">
				<h2 class="font-display text-lg font-bold">AI design review</h2>
				<div v-if="Object.keys(reviewResult.scores || {}).length" class="mt-3 grid grid-cols-5 gap-2 text-center text-xs">
					<div v-for="(score, pillar) in reviewResult.scores" :key="pillar" class="rounded-xl border border-ink-100 p-2 dark:border-ink-800"><b class="block text-xl" :class="score >= 4 ? 'text-emerald-600' : score >= 3 ? 'text-amber-500' : 'text-red-600'">{{ score }}/5</b>{{ pillar }}</div>
				</div>
				<div class="mt-4"><Markdown :html="reviewResult.html" /></div>
			</div>
			<div v-if="publicBoards.length" class="card !p-4"><h2 class="text-sm font-semibold">Community boards</h2><router-link v-for="b in publicBoards" :key="b.name" :to="`/board/${b.name}`" class="mt-2 block text-sm hover:text-brand-600">{{ b.title }} <span class="text-ink-400">· ▲ {{ b.votes || 0 }}</span></router-link></div>
		</div>
	</div>
</template>
<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call, KB, notify, post, session, signIn, STUDIO } from "../api.js";
import Markdown from "../components/Markdown.vue";
import { renderMermaid } from "../components/mermaid.js";
const route = useRoute();
const router = useRouter();
const START = "flowchart LR\n  U[Users] --> LB[Load balancer]\n  LB --> A1[App] & A2[App]\n  A1 & A2 --> DB[(Database)]\n  A1 & A2 --> C[(Cache)]";
const code = ref(START);
const title = ref("");
const visibility = ref("Private");
const context = ref("");
const describe = ref("");
const templates = ref([]);
const publicBoards = ref([]);
const canvas = ref(null);
const busy = ref(false);
const canEdit = ref(true);
const reviewResult = ref(null);
let timer;
watch(code, () => { clearTimeout(timer); timer = setTimeout(draw, 300); });
async function draw() { if (canvas.value) await renderMermaid(canvas.value, code.value); }
function useTemplate(t) { code.value = t.mermaid; title.value = `${t.name} (my version)`; reviewResult.value = null; router.replace("/board"); canEdit.value = true; }
function newBoard() { code.value = START; title.value = ""; reviewResult.value = null; router.replace("/board"); canEdit.value = true; }
async function generate() {
	if (!session.logged_in) return signIn();
	busy.value = true;
	try { const r = await post(`${STUDIO}.generate`, { description: describe.value }); code.value = r.mermaid; title.value ||= describe.value.slice(0, 60); } catch (e) { notify(e.message, "bad"); }
	busy.value = false;
}
async function save() {
	if (!session.logged_in) return signIn();
	try { const r = await post(`${STUDIO}.save`, { name: route.params.name, title: title.value || "Untitled board", mermaid: code.value, visibility: visibility.value }); notify("Saved"); if (!route.params.name) router.replace(`/board/${r.name}`); } catch (e) { notify(e.message, "bad"); }
}
async function review() {
	if (!session.logged_in) return signIn();
	busy.value = true; reviewResult.value = { html: "<p>Reviewing your design…</p>", scores: {} };
	try { reviewResult.value = await post(`${STUDIO}.review`, { name: route.params.name && canEdit.value ? route.params.name : undefined, mermaid: code.value, context: context.value }); } catch (e) { reviewResult.value = null; notify(e.message, "bad"); }
	busy.value = false;
}
async function open(name) {
	const d = await call(`${STUDIO}.diagram`, { name });
	code.value = d.mermaid; title.value = d.title; visibility.value = d.visibility; canEdit.value = d.is_owner;
	if (d.reviews.length) reviewResult.value = { html: d.reviews[0].html, scores: {} };
}
watch(() => route.params.name, (n) => n && open(n), { immediate: true });
onMounted(async () => { draw(); templates.value = await call(`${KB}.templates`); publicBoards.value = await call(`${STUDIO}.diagrams`).catch(() => []); });
</script>
