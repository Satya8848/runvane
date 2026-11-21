<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<div class="mt-3 border-t border-ink-100 pt-2 text-sm dark:border-ink-800">
		<div v-for="c in list" :key="c.name" class="py-1 text-ink-600 dark:text-ink-300"><span v-html="c.html"></span> <span class="text-xs text-ink-400">— {{ c.author?.name }}</span></div>
		<button v-if="!open" class="text-xs text-ink-400 hover:text-brand-600" @click="session.logged_in ? (open = true) : signIn()">Add a comment</button>
		<form v-else class="mt-1 flex gap-2" @submit.prevent="send"><input v-model="text" class="input !py-1.5" placeholder="Short comment" aria-label="Comment" /><button class="btn !py-1.5">Send</button></form>
	</div>
</template>
<script setup>
import { ref } from "vue";
import { FORUM, notify, post, session, signIn } from "../api.js";
const props = defineProps({ list: Array, doctype: String, name: String });
const emit = defineEmits(["added"]);
const open = ref(false);
const text = ref("");
async function send() {
	try { await post(`${FORUM}.comment`, { reference_doctype: props.doctype, reference_name: props.name, body: text.value }); text.value = ""; open.value = false; emit("added"); } catch (e) { notify(e.message, "bad"); }
}
</script>
