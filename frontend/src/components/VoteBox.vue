<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="flex flex-col items-center gap-1 text-ink-500">
		<button class="grid h-8 w-8 place-items-center rounded-lg border border-ink-200 hover:border-brand-400 dark:border-ink-700" :class="mine === 1 ? '!border-brand-500 !text-brand-600' : ''" @click="cast(mine === 1 ? 0 : 1)" aria-label="Upvote">▲</button>
		<b class="text-lg text-ink-800 dark:text-ink-100">{{ total }}</b>
		<button class="grid h-8 w-8 place-items-center rounded-lg border border-ink-200 hover:border-red-400 dark:border-ink-700" :class="mine === -1 ? '!border-red-500 !text-red-600' : ''" @click="cast(mine === -1 ? 0 : -1)" aria-label="Downvote">▼</button>
	</div>
</template>
<script setup>
import { ref } from "vue";
import { FORUM, notify, post, session, signIn } from "../api.js";
const props = defineProps({ doctype: String, name: String, votes: Number, my: Number });
const total = ref(props.votes || 0);
const mine = ref(props.my || 0);
async function cast(value) {
	if (!session.logged_in) return signIn();
	try { total.value = (await post(`${FORUM}.vote`, { doctype: props.doctype, name: props.name, value })).votes; mine.value = value; } catch (e) { notify(e.message, "bad"); }
}
</script>
