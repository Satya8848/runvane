<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
		<form class="min-w-0" @submit.prevent="submit">
			<p class="eyebrow">Ask the community</p>
			<h1 class="mt-1 font-display text-3xl font-bold">Describe your problem</h1>
			<label class="mt-6 block text-sm font-medium" for="title">Title</label>
			<input id="title" v-model="title" class="input mt-1" placeholder="e.g. nginx returns 502 right after every Kubernetes deploy" />
			<div class="mt-4 grid gap-3 sm:grid-cols-2">
				<div><label class="block text-sm font-medium" for="role">Role</label><select id="role" v-model="role" class="input mt-1"><option value="">Choose…</option><option v-for="t in tracks" :key="t.slug" :value="t.slug">{{ t.title }}</option></select></div>
				<div><label class="block text-sm font-medium" for="tags">Tags (comma-separated)</label><input id="tags" v-model="tags" class="input mt-1" placeholder="nginx, kubernetes, aws" /></div>
			</div>
			<label class="mt-4 block text-sm font-medium" for="body">Details</label>
			<p class="text-xs text-ink-500">What you tried, what you expected, what happened. Paste errors in ``` blocks. Remove passwords and keys.</p>
			<textarea id="body" v-model="body" class="input mt-1 min-h-[240px] font-mono"></textarea>
			<div class="mt-4 flex gap-2"><button class="btn btn-primary" :disabled="busy">{{ session.logged_in ? "Post question" : "Sign in to post" }}</button><button type="button" class="btn" @click="preview = !preview">{{ preview ? "Hide preview" : "Preview" }}</button></div>
			<div v-if="preview" class="mt-4 rounded-xl border border-ink-100 p-4 dark:border-ink-800"><Markdown :markdown="body" /></div>
		</form>
		<aside class="space-y-3 lg:sticky lg:top-24 lg:self-start">
			<div class="card"><h2 class="font-semibold">Maybe already answered</h2><p v-if="!similar.length" class="mt-1 text-sm text-ink-500">Start typing a title to see similar playbooks and questions.</p><router-link v-for="s in similar" :key="s.id" :to="s.url" class="mt-2 block text-sm hover:text-brand-600"><span class="chip mr-1">{{ s.kind }}</span>{{ s.title }}</router-link></div>
			<div class="card text-sm text-ink-500">✨ When you post, an AI writes a first draft answer within a minute. People can vote it up, correct it or answer better.</div>
		</aside>
	</div>
</template>
<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call, FORUM, KB, notify, post, session, signIn } from "../api.js";
import Markdown from "../components/Markdown.vue";
const route = useRoute();
const router = useRouter();
const title = ref(route.query.title || "");
const role = ref(route.query.role || "");
const tags = ref("");
const body = ref("");
const busy = ref(false);
const preview = ref(false);
const tracks = ref([]);
const similar = ref([]);
let timer;
watch(title, () => { clearTimeout(timer); timer = setTimeout(async () => (similar.value = await call(`${FORUM}.similar`, { title: title.value }).catch(() => [])), 300); }, { immediate: true });
async function submit() {
	if (!session.logged_in) return signIn();
	busy.value = true;
	try { const r = await post(`${FORUM}.ask`, { title: title.value, body: body.value, role_track: role.value, tags: tags.value }); router.push(`/q/${r.name}`); } catch (e) { notify(e.message, "bad"); }
	busy.value = false;
}
onMounted(async () => (tracks.value = (await call(`${KB}.home`)).tracks));
</script>
