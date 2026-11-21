<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div v-if="d" class="mx-auto max-w-4xl">
		<div class="flex flex-wrap items-center gap-2 text-sm"><router-link to="/q" class="eyebrow">Forum</router-link><span v-if="d.question.role_track" class="chip">{{ d.question.role_track }}</span><span class="chip" :class="d.question.status === 'Answered' ? '!border-emerald-400 !text-emerald-700' : ''">{{ d.question.status }}</span></div>
		<h1 class="mt-2 text-balance font-display text-3xl font-bold">{{ d.question.title }}</h1>
		<p class="mt-1 text-sm text-ink-500">Asked by {{ d.question.author?.name }} · {{ d.question.views }} views</p>
		<div class="mt-6 flex gap-4">
			<VoteBox doctype="Question" :name="d.question.name" :votes="d.question.votes" :my="d.my_votes[d.question.name]" />
			<div class="min-w-0 flex-1"><Markdown :html="d.question.html" /><div class="mt-3 flex flex-wrap gap-1"><span v-for="t in d.question.tags" :key="t" class="chip">{{ t }}</span></div><Comments :list="commentsFor(d.question.name)" doctype="Question" :name="d.question.name" @added="load" /></div>
		</div>
		<div v-if="d.question.ai_draft_status === 'Queued' || (!d.answers.length && !d.question.ai_draft_status)" class="mt-6 rounded-xl border border-dashed border-brand-300 p-4 text-sm text-brand-700 dark:text-brand-300">✨ An AI first draft is being prepared. Refresh in a moment.</div>
		<h2 class="mt-10 font-display text-xl font-bold">{{ d.answers.length }} answers</h2>
		<div v-for="a in d.answers" :key="a.name" class="mt-4 flex gap-4 rounded-2xl border p-4" :class="a.is_accepted ? 'border-emerald-300 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-900/10' : 'border-ink-100 dark:border-ink-800'">
			<VoteBox doctype="Answer" :name="a.name" :votes="a.votes" :my="d.my_votes[a.name]" />
			<div class="min-w-0 flex-1">
				<div class="mb-2 flex flex-wrap items-center gap-2 text-xs">
					<span v-if="a.is_accepted" class="chip !border-emerald-500 !text-emerald-700">✓ Accepted</span>
					<span v-if="a.is_ai" class="chip !border-brand-400 !text-brand-700">✨ AI draft · {{ a.ai_provider }}</span>
					<span v-else class="text-ink-500">{{ a.author?.name }} · ★ {{ a.author?.reputation }}</span>
					<button v-if="(d.is_owner || session.is_moderator) && !a.is_accepted" class="btn ml-auto !py-1 !text-xs" @click="accept(a.name)">Accept this answer</button>
				</div>
				<Markdown :html="a.html" />
				<Comments :list="commentsFor(a.name)" doctype="Answer" :name="a.name" @added="load" />
			</div>
		</div>
		<form class="card mt-10" @submit.prevent="submit">
			<h2 class="font-display text-lg font-semibold">Your answer</h2>
			<p class="text-sm text-ink-500">Markdown supported. Put commands in ``` code blocks.</p>
			<textarea v-model="body" class="input mt-3 min-h-[180px] font-mono" placeholder="Explain the cause, how to confirm it, and the fix…" aria-label="Your answer"></textarea>
			<div class="mt-3 flex gap-2"><button class="btn btn-primary" :disabled="busy">{{ session.logged_in ? "Post answer" : "Sign in to answer" }}</button><button type="button" class="btn" @click="preview = !preview">{{ preview ? "Hide" : "Preview" }}</button></div>
			<div v-if="preview" class="mt-4 rounded-xl border border-ink-100 p-4 dark:border-ink-800"><Markdown :markdown="body" /></div>
		</form>
	</div>
</template>
<script setup>
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { call, FORUM, notify, post, session, signIn } from "../api.js";
import Comments from "../components/Comments.vue";
import Markdown from "../components/Markdown.vue";
import VoteBox from "../components/VoteBox.vue";
const route = useRoute();
const d = ref(null);
const body = ref("");
const busy = ref(false);
const preview = ref(false);
async function load() { d.value = await call(`${FORUM}.question`, { name: route.params.name }); document.title = `${d.value.question.title} · StackPilot`; }
const commentsFor = (name) => (d.value?.comments || []).filter((c) => c.reference_name === name);
async function submit() {
	if (!session.logged_in) return signIn();
	busy.value = true;
	try { await post(`${FORUM}.answer`, { question: route.params.name, body: body.value }); body.value = ""; preview.value = false; notify("Answer posted"); await load(); } catch (e) { notify(e.message, "bad"); }
	busy.value = false;
}
async function accept(answer) { try { await post(`${FORUM}.accept`, { answer }); notify("Marked as accepted"); load(); } catch (e) { notify(e.message, "bad"); } }
watch(() => route.params.name, (n) => n && load(), { immediate: true });
</script>
