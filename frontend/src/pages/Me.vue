<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div v-if="!session.logged_in && session.loaded" class="card mx-auto max-w-md text-center"><h1 class="font-display text-2xl font-bold">My account</h1><p class="mt-2 text-ink-500">Sign in to see your profile and activity.</p><router-link to="/join?next=/me" class="btn btn-primary mt-4">Join or sign in</router-link></div>
	<div v-else-if="d" class="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
		<aside class="space-y-4">
			<div class="card text-center">
				<span class="mx-auto grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-signal-500 text-2xl font-bold text-white">{{ initials }}</span>
				<h1 class="mt-3 font-display text-xl font-bold">{{ d.profile.display_name }}</h1>
				<p class="text-sm text-ink-500">{{ d.profile.headline || roleTitle || "Member" }}</p>
				<div class="mt-4 grid grid-cols-3 gap-2 text-center text-xs text-ink-500">
					<div><b class="block text-lg text-ink-900 dark:text-ink-100">{{ d.profile.reputation || 0 }}</b>reputation</div>
					<div><b class="block text-lg text-ink-900 dark:text-ink-100">{{ d.counts.answers }}</b>answers</div>
					<div><b class="block text-lg text-ink-900 dark:text-ink-100">{{ d.counts.accepted }}</b>accepted</div>
				</div>
				<div v-if="d.badges.length" class="mt-4 flex flex-wrap justify-center gap-1"><span v-for="b in d.badges" :key="b" class="chip">🏅 {{ b }}</span></div>
			</div>
			<nav class="card !p-2 text-sm">
				<button v-for="t in tabs" :key="t.value" class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left" :class="tab === t.value ? 'bg-brand-50 font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-200' : 'hover:bg-ink-50 dark:hover:bg-ink-800'" @click="go(t.value)">
					{{ t.label }}<span v-if="t.count !== undefined" class="text-xs text-ink-400">{{ t.count }}</span>
				</button>
			</nav>
		</aside>
		<section class="min-w-0">
			<form v-if="tab === 'profile'" class="card space-y-4" @submit.prevent="save">
				<h2 class="font-display text-xl font-bold">Profile</h2>
				<div class="grid gap-4 sm:grid-cols-2">
					<div><label class="text-sm font-medium" for="dn">Display name</label><input id="dn" v-model="form.display_name" class="input mt-1" /></div>
					<div><label class="text-sm font-medium" for="hl">Headline</label><input id="hl" v-model="form.headline" class="input mt-1" placeholder="e.g. Senior DevOps engineer, AWS & Kubernetes" /></div>
					<div><label class="text-sm font-medium" for="rt">Main role</label><select id="rt" v-model="form.role_track" class="input mt-1"><option value="">Choose…</option><option v-for="t in tracks" :key="t.slug" :value="t.slug">{{ t.title }}</option></select></div>
					<div><label class="text-sm font-medium" for="lc">Location</label><input id="lc" v-model="form.location" class="input mt-1" /></div>
					<div><label class="text-sm font-medium" for="gh">GitHub</label><input id="gh" v-model="form.github" class="input mt-1" placeholder="github.com/you" /></div>
					<div><label class="text-sm font-medium" for="ws">Website</label><input id="ws" v-model="form.website" class="input mt-1" /></div>
				</div>
				<div><label class="text-sm font-medium" for="bio">About you</label><textarea id="bio" v-model="form.bio" class="input mt-1 min-h-[100px]"></textarea></div>
				<div class="flex items-center gap-3"><button class="btn btn-primary" :disabled="busy">Save profile</button><span class="text-sm text-ink-500">{{ d.email }}</span></div>
			</form>

			<div v-else-if="tab === 'questions'" class="space-y-6">
				<div class="card"><div class="flex items-center justify-between"><h2 class="font-display text-xl font-bold">My questions</h2><router-link to="/ask" class="btn btn-primary !py-1.5">Ask</router-link></div>
					<router-link v-for="q in d.questions" :key="q.name" :to="`/q/${q.name}`" class="mt-3 flex items-center justify-between gap-3 rounded-xl border border-ink-100 p-3 hover:border-brand-300 dark:border-ink-800"><span class="min-w-0 truncate font-medium">{{ q.title }}</span><span class="chip shrink-0" :class="q.status === 'Answered' ? '!border-emerald-400 !text-emerald-700' : ''">{{ q.answer_count }} answers · {{ q.status }}</span></router-link>
					<p v-if="!d.questions.length" class="mt-3 text-sm text-ink-500">You haven't asked anything yet.</p></div>
				<div class="card"><h2 class="font-display text-xl font-bold">My answers</h2>
					<router-link v-for="a in d.answers" :key="a.name" :to="`/q/${a.question}`" class="mt-3 flex items-center justify-between gap-3 rounded-xl border border-ink-100 p-3 hover:border-brand-300 dark:border-ink-800"><span class="min-w-0 truncate">{{ a.question_title }}</span><span class="chip shrink-0">▲ {{ a.votes || 0 }}<template v-if="a.is_accepted"> · ✓ accepted</template></span></router-link>
					<p v-if="!d.answers.length" class="mt-3 text-sm text-ink-500">No answers yet. <router-link to="/q?sort=unanswered" class="text-brand-600">Help with an unanswered question</router-link>.</p></div>
			</div>

			<div v-else-if="tab === 'boards'" class="card">
				<div class="flex items-center justify-between"><h2 class="font-display text-xl font-bold">My architecture boards</h2><router-link to="/board" class="btn btn-primary !py-1.5">New board</router-link></div>
				<router-link v-for="b in d.boards" :key="b.name" :to="`/board/${b.name}`" class="mt-3 flex items-center justify-between gap-3 rounded-xl border border-ink-100 p-3 hover:border-brand-300 dark:border-ink-800"><span class="min-w-0 truncate font-medium">{{ b.title }}</span><span class="chip shrink-0">{{ b.visibility }}</span></router-link>
				<p v-if="!d.boards.length" class="mt-3 text-sm text-ink-500">No boards yet. Start from a template on the board page.</p>
			</div>

			<div v-else class="space-y-4">
				<div class="card">
					<h2 class="font-display text-xl font-bold">AI keys</h2>
					<p class="mt-1 text-sm text-ink-500">Optional. Add your own key to use AI without daily limits. Stored encrypted, never shown again.</p>
					<router-link to="/ai" class="btn mt-3" @click="aiKeys">Manage keys on the AI page</router-link>
				</div>
				<div class="card">
					<h2 class="font-display text-xl font-bold">Password</h2>
					<p class="mt-1 text-sm text-ink-500">Send yourself a reset link, or change it in the account page.</p>
					<a href="/update-password" class="btn mt-3">Change password</a>
				</div>
				<div class="card">
					<h2 class="font-display text-xl font-bold">Sign out</h2>
					<button class="btn mt-3 !border-red-300 !text-red-600" @click="logout">Sign out of Runvane</button>
				</div>
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call, KB, notify, post, session } from "../api.js";

const route = useRoute();
const router = useRouter();
const d = ref(null);
const tracks = ref([]);
const busy = ref(false);
const tab = ref(route.query.tab || "profile");
const form = reactive({ display_name: "", headline: "", role_track: "", location: "", github: "", website: "", bio: "" });
const tabs = computed(() => [
	{ value: "profile", label: "Profile" },
	{ value: "questions", label: "Questions & answers", count: d.value ? d.value.counts.questions + d.value.counts.answers : undefined },
	{ value: "boards", label: "Architecture boards", count: d.value?.counts.boards },
	{ value: "settings", label: "Settings & AI keys" },
]);
const initials = computed(() => (d.value?.profile.display_name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join(""));
const roleTitle = computed(() => tracks.value.find((t) => t.slug === d.value?.profile.role_track)?.title);

/**
 * Load the member's profile and activity.
 *
 * @returns {Promise<void>}
 */
async function load() {
	d.value = await call("stackpilot.sp_core.api.v1.account.me");
	Object.keys(form).forEach((k) => (form[k] = d.value.profile[k] || ""));
}

/**
 * Switch tab and keep it in the URL.
 *
 * @param {string} value - Tab.
 * @returns {void}
 */
function go(value) { tab.value = value; router.replace({ query: value === "profile" ? {} : { tab: value } }); }

/**
 * Save the profile.
 *
 * @returns {Promise<void>}
 */
async function save() {
	busy.value = true;
	try { await post("stackpilot.sp_core.api.v1.account.update_profile", { ...form }); notify("Profile saved"); session.display_name = form.display_name; await load(); } catch (e) { notify(e.message, "bad"); }
	busy.value = false;
}

const aiKeys = () => { try { sessionStorage.setItem("rv_ai_mode", "keys"); } catch (e) { /* storage blocked */ } };
async function logout() { await fetch("/api/method/logout", { method: "POST", headers: { "X-Frappe-CSRF-Token": window.csrf_token || "" } }); location.href = "/"; }
watch(() => route.query.tab, (t) => (tab.value = t || "profile"));
watch(() => session.logged_in, (v) => v && load());
onMounted(async () => { if (session.logged_in) load(); tracks.value = (await call(`${KB}.home`)).tracks; });
</script>
