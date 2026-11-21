<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="mx-auto grid max-w-5xl items-center gap-10 py-6 lg:grid-cols-2">
		<div>
			<p class="eyebrow">Free account</p>
			<h1 class="mt-2 font-display text-4xl font-bold">Join StackPilot</h1>
			<ul class="mt-6 space-y-3 text-ink-600 dark:text-ink-300">
				<li>✨ AI analysis of your logs, errors, configs and SQL</li>
				<li>💬 Ask the community, with an AI first draft on every question</li>
				<li>🗺️ Save architecture boards and get design reviews</li>
				<li>★ Earn reputation for answers people accept</li>
			</ul>
		</div>
		<form class="card space-y-4" @submit.prevent="submit">
			<div><label class="text-sm font-medium" for="name">Name</label><input id="name" v-model="name" class="input mt-1" autocomplete="name" required /></div>
			<div><label class="text-sm font-medium" for="email">Email</label><input id="email" v-model="email" type="email" class="input mt-1" autocomplete="email" required /></div>
			<div><label class="text-sm font-medium" for="pw">Password</label><input id="pw" v-model="password" type="password" class="input mt-1" autocomplete="new-password" minlength="10" required /><p class="mt-1 text-xs text-ink-500">At least 10 characters. Avoid common words.</p></div>
			<div><label class="text-sm font-medium" for="role">I work as</label><select id="role" v-model="role" class="input mt-1"><option value="">Choose…</option><option v-for="t in tracks" :key="t.slug" :value="t.slug">{{ t.title }}</option></select></div>
			<button class="btn btn-primary w-full justify-center" :disabled="busy">{{ busy ? "Creating…" : "Create account" }}</button>
			<p class="text-center text-sm text-ink-500">Already a member? <a class="text-brand-600" :href="`/login?redirect-to=${encodeURIComponent(next)}`">Sign in</a></p>
		</form>
	</div>
</template>
<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { call, KB, notify, post } from "../api.js";
const route = useRoute();
const next = route.query.next || "/";
const name = ref(""); const email = ref(""); const password = ref(""); const role = ref(""); const busy = ref(false); const tracks = ref([]);
async function submit() {
	busy.value = true;
	try { await post("stackpilot.sp_core.api.v1.account.signup", { full_name: name.value, email: email.value, password: password.value, role_track: role.value }); location.href = next; }
	catch (e) { notify(e.message, "bad"); busy.value = false; }
}
onMounted(async () => (tracks.value = (await call(`${KB}.home`)).tracks));
</script>
