<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div v-if="d" class="mx-auto max-w-4xl">
		<div class="flex flex-wrap items-center gap-2 text-sm"><router-link to="/q" class="eyebrow">Forum</router-link><span v-if="d.question.role_track" class="chip">{{ d.question.role_track }}</span><span class="chip" :class="d.question.status === 'Answered' ? '!border-emerald-400 !text-emerald-700' : ''">{{ d.question.status }}</span></div>
		<template v-if="!editingQ">
			<h1 class="mt-2 text-balance font-display text-3xl font-bold">{{ d.question.title }}</h1>
			<div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-500">
				<span>Asked by {{ d.question.author?.name }} · {{ d.question.views }} {{ d.question.views === 1 ? "view" : "views" }}<template v-if="d.question.edited"> · edited</template></span>
				<span v-if="d.can_manage" class="flex flex-wrap gap-1">
					<button class="btn !px-2.5 !py-1 !text-xs" @click="startEditQ">✏️ Edit</button>
					<button class="btn !px-2.5 !py-1 !text-xs" @click="setStatus(d.question.status === 'Closed' ? 'Open' : 'Closed')">{{ d.question.status === "Closed" ? "↺ Reopen" : "🔒 Close" }}</button>
					<button class="btn !px-2.5 !py-1 !text-xs !text-red-600" :disabled="d.others_answered && !session.is_moderator" :title="d.others_answered && !session.is_moderator ? 'Others answered; close it instead' : ''" @click="confirmDelete = { kind: 'question', name: d.question.name }">🗑 Delete</button>
				</span>
				<button v-else-if="session.logged_in" class="text-xs text-ink-400 hover:text-red-600" @click="report('Question', d.question.name)">⚑ Report</button>
			</div>
		</template>
		<form v-else class="card mt-3 space-y-3" @submit.prevent="saveQ">
			<label class="block text-sm font-medium" for="eqt">Title</label><input id="eqt" v-model="qForm.title" class="input" />
			<label class="block text-sm font-medium" for="eqtags">Tags</label><input id="eqtags" v-model="qForm.tags" class="input" />
			<label class="block text-sm font-medium" for="eqb">Details</label><textarea id="eqb" v-model="qForm.body" class="input min-h-[200px] font-mono"></textarea>
			<div class="flex gap-2"><button class="btn btn-primary">Save changes</button><button type="button" class="btn" @click="editingQ = false">Cancel</button></div>
		</form>
		<div v-if="d.question.status === 'Closed'" class="mt-4 rounded-xl bg-ink-100 p-3 text-sm text-ink-600 dark:bg-ink-800 dark:text-ink-300">🔒 This question is closed. New answers are turned off.</div>
		<div v-if="!editingQ" class="mt-6 flex gap-4">
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
					<span v-else class="text-ink-500">{{ a.author?.name }} · ★ {{ a.author?.reputation }}<template v-if="a.edited"> · edited</template></span>
					<span class="ml-auto flex flex-wrap gap-1">
						<button v-if="(d.is_owner || session.is_moderator) && !a.is_accepted" class="btn !py-1 !text-xs" @click="accept(a.name)">✓ Accept</button>
						<template v-if="a.can_edit">
							<button class="btn !py-1 !text-xs" @click="startEditA(a)">✏️ Edit</button>
							<button class="btn !py-1 !text-xs !text-red-600" @click="confirmDelete = { kind: 'answer', name: a.name }">🗑 Delete</button>
						</template>
						<button v-else-if="session.logged_in" class="px-1 text-xs text-ink-400 hover:text-red-600" @click="report('Answer', a.name)">⚑ Report</button>
					</span>
				</div>
				<form v-if="editingA === a.name" class="space-y-2" @submit.prevent="saveA(a.name)">
					<textarea v-model="aForm" class="input min-h-[160px] font-mono" aria-label="Edit answer"></textarea>
					<div class="flex gap-2"><button class="btn btn-primary !py-1.5">Save</button><button type="button" class="btn !py-1.5" @click="editingA = null">Cancel</button></div>
				</form>
				<Markdown v-else :html="a.html" />
				<Comments :list="commentsFor(a.name)" doctype="Answer" :name="a.name" @added="load" />
			</div>
		</div>
		<div v-if="confirmDelete" class="fixed inset-0 z-50 grid place-items-center bg-ink-950/50 p-4" @click.self="confirmDelete = null">
			<div class="card max-w-sm" role="dialog" aria-label="Confirm delete">
				<h2 class="font-display text-lg font-bold">Delete this {{ confirmDelete.kind }}?</h2>
				<p class="mt-1 text-sm text-ink-500">{{ confirmDelete.kind === "question" ? "Its answers, comments and votes are deleted too." : "Its comments and votes are deleted too." }} This can't be undone.</p>
				<div class="mt-4 flex justify-end gap-2"><button class="btn" @click="confirmDelete = null">Cancel</button><button class="btn !border-red-600 !bg-red-600 !text-white" @click="doDelete">Delete</button></div>
			</div>
		</div>
		<form v-if="d.question.status !== 'Closed'" class="card mt-10" @submit.prevent="submit">
			<h2 class="font-display text-lg font-semibold">Your answer</h2>
			<p class="text-sm text-ink-500">Markdown supported. Put commands in ``` code blocks.</p>
			<textarea v-model="body" class="input mt-3 min-h-[180px] font-mono" placeholder="Explain the cause, how to confirm it, and the fix…" aria-label="Your answer"></textarea>
			<div class="mt-3 flex gap-2"><button class="btn btn-primary" :disabled="busy">{{ session.logged_in ? "Post answer" : "Sign in to answer" }}</button><button type="button" class="btn" @click="preview = !preview">{{ preview ? "Hide" : "Preview" }}</button></div>
			<div v-if="preview" class="mt-4 rounded-xl border border-ink-100 p-4 dark:border-ink-800"><Markdown :markdown="body" /></div>
		</form>
	</div>
</template>
<script setup>
import { reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call, FORUM, notify, post, session, signIn } from "../api.js";
import Comments from "../components/Comments.vue";
import Markdown from "../components/Markdown.vue";
import VoteBox from "../components/VoteBox.vue";
const route = useRoute();
const d = ref(null);
const body = ref("");
const busy = ref(false);
const preview = ref(false);
const editingQ = ref(false);
const qForm = reactive({ title: "", tags: "", body: "" });
const editingA = ref(null);
const aForm = ref("");
const confirmDelete = ref(null);
const router = useRouter();

/** Open the question editor with current values. @returns {void} */
function startEditQ() { Object.assign(qForm, { title: d.value.question.title, tags: d.value.question.tags.join(", "), body: d.value.question.markdown }); editingQ.value = true; }
/** Save question edits. @returns {Promise<void>} */
async function saveQ() { try { await post(`${FORUM}.edit_question`, { name: route.params.name, ...qForm }); editingQ.value = false; notify("Question updated"); load(); } catch (e) { notify(e.message, "bad"); } }
/** Close or reopen. @param {string} status - Open or Closed. @returns {Promise<void>} */
async function setStatus(status) { try { await post(`${FORUM}.set_status`, { name: route.params.name, status }); notify(status === "Closed" ? "Question closed" : "Question reopened"); load(); } catch (e) { notify(e.message, "bad"); } }
/** Open the answer editor. @param {object} a - Answer. @returns {void} */
function startEditA(a) { aForm.value = a.markdown; editingA.value = a.name; }
/** Save an answer edit. @param {string} name - Answer. @returns {Promise<void>} */
async function saveA(name) { try { await post(`${FORUM}.edit_answer`, { name, body: aForm.value }); editingA.value = null; notify("Answer updated"); load(); } catch (e) { notify(e.message, "bad"); } }
/** Delete the confirmed post. @returns {Promise<void>} */
async function doDelete() {
	const { kind, name } = confirmDelete.value;
	confirmDelete.value = null;
	try {
		await post(`${FORUM}.delete_${kind}`, { name });
		notify(kind === "question" ? "Question deleted" : "Answer deleted");
		if (kind === "question") router.push("/q"); else load();
	} catch (e) { notify(e.message, "bad"); }
}
/** Report a post to moderators. @param {string} doctype - Doctype. @param {string} name - Record. @returns {Promise<void>} */
async function report(doctype, name) { try { await post(`${FORUM}.report`, { reference_doctype: doctype, reference_name: name, reason: "Spam" }); notify("Reported to moderators. Thank you."); } catch (e) { notify(e.message, "bad"); } }
async function load() { d.value = await call(`${FORUM}.question`, { name: route.params.name }); document.title = `${d.value.question.title} · Runvane`; }
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
