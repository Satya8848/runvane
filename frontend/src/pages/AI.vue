<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
		<aside class="space-y-3">
			<div class="card !p-3">
				<button v-for="m in modes" :key="m.value" class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm" :class="mode === m.value ? 'bg-brand-50 font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-200' : 'hover:bg-ink-50 dark:hover:bg-ink-800'" @click="mode = m.value"><span aria-hidden="true">{{ m.icon }}</span>{{ m.label }}</button>
			</div>
			<div v-if="status" class="card !p-4 text-xs text-ink-500">
				<p><b class="text-ink-800 dark:text-ink-100">Today:</b> {{ status.used_today.toLocaleString() }} / {{ status.quota.toLocaleString() }} tokens</p>
				<p class="mt-1">Site AI: {{ status.site_keys.length ? status.site_keys.join(", ") : "not configured" }}<span v-if="status.budget_reached"> (budget reached)</span></p>
				<p class="mt-1">Your keys: {{ status.own_keys.length ? status.own_keys.join(", ") : "none" }}</p>
			</div>
			<div v-if="convos.length" class="card !p-3 text-sm"><p class="px-2 text-xs font-semibold uppercase text-ink-400">Recent</p><button v-for="c in convos" :key="c.name" class="block w-full truncate rounded-lg px-2 py-1.5 text-left hover:bg-ink-50 dark:hover:bg-ink-800" @click="openConvo(c)">{{ c.title }}</button></div>
		</aside>

		<section class="min-w-0">
			<div v-if="!session.logged_in && session.loaded" class="card text-center"><h1 class="font-display text-2xl font-bold">AI assistant</h1><p class="mt-2 text-ink-500">Chat, log and config analysis need a free account (it keeps AI fair for everyone).</p><button class="btn btn-primary mt-4" @click="signIn">Sign in or join</button></div>

			<template v-else-if="mode === 'chat'">
				<h1 class="font-display text-2xl font-bold">Ask anything</h1>
				<p class="text-sm text-ink-500">Answers use StackPilot's playbooks and guides and link to them. Secrets you paste are masked before sending.</p>
				<div class="mt-4 space-y-4">
					<div v-for="(m, i) in messages" :key="i" class="rounded-2xl p-4" :class="m.role === 'user' ? 'ml-auto max-w-2xl bg-brand-600 text-white' : 'card'">
						<div v-if="m.role === 'user'" class="whitespace-pre-wrap text-sm">{{ m.content }}</div>
						<template v-else><Markdown :markdown="m.content" /><div v-if="m.sources?.length" class="mt-3 flex flex-wrap gap-2 border-t border-ink-100 pt-3 text-xs dark:border-ink-800"><span class="text-ink-400">Sources:</span><router-link v-for="s in m.sources" :key="s.id" :to="s.url" class="chip hover:text-brand-600">{{ s.title }}</router-link></div></template>
						<p v-if="m.masked?.length" class="mt-2 text-xs opacity-80">🔒 Masked before sending: {{ m.masked.join(", ") }}</p>
					</div>
					<div v-if="busy" class="card animate-pulse text-sm text-ink-500">Thinking…</div>
				</div>
				<form class="sticky bottom-4 mt-4 flex gap-2 rounded-2xl border border-ink-200 bg-white p-2 shadow-lg dark:border-ink-700 dark:bg-ink-900" @submit.prevent="send">
					<textarea v-model="input" rows="2" class="min-h-[48px] flex-1 resize-y bg-transparent px-2 py-1 text-sm outline-none" placeholder="e.g. Why does my pod get OOMKilled at night? How do I set up OIDC from Azure DevOps to AWS?" @keydown.enter.exact.prevent="send" aria-label="Message"></textarea>
					<button class="btn btn-primary self-end" :disabled="busy || !input.trim()">Send</button>
				</form>
			</template>

			<template v-else-if="mode === 'analyse'">
				<h1 class="font-display text-2xl font-bold">Analyse logs, errors &amp; configs</h1>
				<p class="text-sm text-ink-500">Get root cause, evidence lines, fix steps and risk. Keys, tokens and passwords are masked on the server before anything is sent to the AI.</p>
				<div class="mt-4 flex flex-wrap gap-2"><button v-for="k in kinds" :key="k.value" class="chip" :class="kind === k.value ? '!border-brand-500 !text-brand-700 dark:!text-brand-300' : ''" @click="kind = k.value">{{ k.label }}</button></div>
				<textarea v-model="pasted" class="input mt-3 min-h-[260px] font-mono text-xs" :placeholder="kinds.find((k) => k.value === kind).hint" aria-label="Content to analyse"></textarea>
				<input v-model="question" class="input mt-2" placeholder="Optional: what do you want to know?" aria-label="Question" />
				<button class="btn btn-primary mt-3" :disabled="busy || pasted.trim().length < 10" @click="analyse">{{ busy ? "Analysing…" : "Analyse" }}</button>
				<div v-if="analysis" class="card mt-6"><p v-if="analysis.masked.length" class="mb-3 rounded-lg bg-amber-50 p-2 text-xs text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">🔒 Masked before sending: {{ analysis.masked.join(", ") }}</p><Markdown :markdown="analysis.answer" /><p class="mt-3 text-xs text-ink-400">By {{ analysis.provider }}. Check before running anything in production.</p></div>
			</template>

			<template v-else>
				<h1 class="font-display text-2xl font-bold">Your own AI keys</h1>
				<p class="text-sm text-ink-500">Optional. Your key is used instead of the site's, with no daily limit. It is stored encrypted and never shown again.</p>
				<form class="card mt-4 grid gap-3 sm:grid-cols-[160px_minmax(0,1fr)_auto]" @submit.prevent="saveKey">
					<select v-model="keyProvider" class="input" aria-label="Provider"><option value="claude">Claude (Anthropic)</option><option value="gemini">Gemini (Google)</option><option value="groq">Groq</option><option value="openai">OpenAI</option></select>
					<input v-model="keyValue" type="password" autocomplete="off" class="input" placeholder="Paste API key" aria-label="API key" />
					<button class="btn btn-primary">Save key</button>
				</form>
				<div class="mt-3 flex flex-wrap gap-2"><span v-for="p in status?.own_keys || []" :key="p" class="chip">{{ p }} <button class="ml-1 text-red-500" @click="deleteKey(p)" :aria-label="`Remove ${p} key`">✕</button></span></div>
			</template>
		</section>
	</div>
</template>
<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { AI, call, notify, post, session, signIn } from "../api.js";
import Markdown from "../components/Markdown.vue";
const route = useRoute();
const modes = [{ value: "chat", label: "Ask anything", icon: "✨" }, { value: "analyse", label: "Analyse", icon: "🔍" }, { value: "keys", label: "My AI keys", icon: "🔑" }];
const kinds = [
	{ value: "logs", label: "Logs", hint: "Paste application, nginx, Kubernetes or system logs…" },
	{ value: "error", label: "Error / stack trace", hint: "Paste the full error and stack trace…" },
	{ value: "config", label: "Config", hint: "Paste nginx, Kubernetes YAML, Terraform, Ansible, systemd…" },
	{ value: "sql", label: "SQL / EXPLAIN", hint: "Paste the query and its EXPLAIN output…" },
	{ value: "dockerfile", label: "Dockerfile", hint: "Paste your Dockerfile…" },
	{ value: "pipeline", label: "CI/CD pipeline", hint: "Paste azure-pipelines.yml, Jenkinsfile or GitHub Actions workflow…" },
];
const mode = ref("chat");
const status = ref(null);
const convos = ref([]);
const messages = ref([]);
const conversation = ref(null);
const input = ref(route.query.q || "");
const busy = ref(false);
const kind = ref("logs");
const pasted = ref("");
const question = ref("");
const analysis = ref(null);
const keyProvider = ref("claude");
const keyValue = ref("");
async function refresh() { if (!session.logged_in) return; status.value = await call(`${AI}.status`).catch(() => null); convos.value = await call(`${AI}.conversations`).catch(() => []); }
async function send() {
	if (!input.value.trim() || busy.value) return;
	const text = input.value; input.value = ""; messages.value.push({ role: "user", content: text }); busy.value = true;
	try { const r = await post(`${AI}.chat`, { message: text, conversation: conversation.value, role_track: route.query.role }); conversation.value = r.conversation; messages.value[messages.value.length - 1].masked = r.masked; messages.value.push({ role: "assistant", content: r.answer, sources: r.sources }); refresh(); }
	catch (e) { messages.value.push({ role: "assistant", content: `⚠️ ${e.message}` }); }
	busy.value = false;
}
async function analyse() { busy.value = true; analysis.value = null; try { analysis.value = await post(`${AI}.analyse`, { kind: kind.value, text: pasted.value, question: question.value, role_track: route.query.role }); refresh(); } catch (e) { notify(e.message, "bad"); } busy.value = false; }
async function openConvo(c) { mode.value = c.feature === "analyse" ? "analyse" : "chat"; conversation.value = c.name; messages.value = (await call(`${AI}.conversation`, { name: c.name })).map((m) => ({ ...m, masked: m.masked ? m.masked.split(", ") : [], sources: JSON.parse(m.sources_json || "[]") })); if (mode.value === "analyse") { mode.value = "chat"; } }
async function saveKey() { try { await post(`${AI}.save_key`, { provider: keyProvider.value, api_key: keyValue.value }); keyValue.value = ""; notify("Key saved"); refresh(); } catch (e) { notify(e.message, "bad"); } }
async function deleteKey(p) { await post(`${AI}.delete_key`, { provider: p }); refresh(); }
watch(() => session.logged_in, refresh);
onMounted(refresh);
</script>
