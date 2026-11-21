<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template>
	<header class="sticky top-0 z-30 border-b border-ink-100 bg-white/85 backdrop-blur dark:border-ink-800 dark:bg-ink-950/85">
		<div class="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
			<router-link to="/" class="flex items-center gap-2 font-display text-lg font-bold tracking-tight">
				<svg class="h-8 w-8" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" class="fill-brand-600"/><path d="M8 17h13l-3.5-3.5M21 17l-3.5 3.5" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="23.5" cy="10" r="2.2" fill="#2dd4bf"/></svg>
				Runvane
			</router-link>
			<nav class="hidden items-center gap-1 text-sm font-medium md:flex">
				<router-link v-for="item in nav" :key="item.to" :to="item.to" class="rounded-lg px-3 py-1.5 text-ink-600 hover:bg-ink-50 hover:text-ink-900 dark:text-ink-300 dark:hover:bg-ink-800 dark:hover:text-white" active-class="!text-brand-600 dark:!text-brand-300">{{ item.label }}</router-link>
			</nav>
			<button class="ml-auto flex min-w-0 items-center gap-2 rounded-xl border border-ink-200 px-3 py-1.5 text-sm text-ink-400 hover:border-ink-300 dark:border-ink-700 sm:w-64" @click="palette = true" aria-label="Search">
				<span aria-hidden="true">⌕</span><span class="hidden truncate sm:inline">Search problems, guides…</span><kbd class="ml-auto hidden rounded border border-ink-200 px-1.5 text-[10px] dark:border-ink-700 sm:inline">/</kbd>
			</button>
			<template v-if="session.loaded">
				<div v-if="!session.logged_in" class="flex items-center gap-2"><a class="hidden text-sm text-ink-600 hover:text-ink-900 dark:text-ink-300 sm:inline" href="/login?redirect-to=/">Sign in</a><router-link class="btn btn-primary" to="/join">Join free</router-link></div>
				<UserMenu v-else />
			</template>
		</div>
		<nav class="flex gap-1 overflow-x-auto px-4 pb-2 text-sm [scrollbar-width:none] md:hidden" aria-label="Sections">
			<router-link v-for="item in nav" :key="item.to" :to="item.to" class="whitespace-nowrap rounded-lg px-3 py-1 text-ink-600 dark:text-ink-300" active-class="bg-brand-50 !text-brand-700 dark:bg-brand-900/40 dark:!text-brand-200">{{ item.label }}</router-link>
		</nav>
	</header>
	<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6"><router-view /></main>
	<footer class="border-t border-ink-100 py-8 text-center text-xs text-ink-400 dark:border-ink-800">Runvane · playbooks, forum, AI and architecture for people who keep systems running</footer>
	<SearchPalette v-if="palette" @close="palette = false" />
	<div v-if="toast.text" class="fixed bottom-4 right-4 z-50 max-w-sm rounded-xl px-4 py-3 text-sm shadow-lg" :class="toast.kind === 'bad' ? 'bg-red-600 text-white' : 'bg-ink-900 text-white dark:bg-white dark:text-ink-900'" role="status">{{ toast.text }}</div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { loadSession, session, toast } from "./api.js";
import SearchPalette from "./components/SearchPalette.vue";
import UserMenu from "./components/UserMenu.vue";

const nav = [
	{ to: "/playbooks", label: "Playbooks" }, { to: "/q", label: "Forum" }, { to: "/ai", label: "AI assistant" },
	{ to: "/board", label: "Architecture" }, { to: "/guides", label: "Guides" }, { to: "/interview", label: "Interview prep" },
];
const palette = ref(false);

/**
 * Open the search palette on "/" or Ctrl/Cmd+K.
 *
 * @param {KeyboardEvent} event - Key event.
 * @returns {void}
 */
function onKey(event) {
	const typing = ["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName);
	if ((event.key === "/" && !typing) || ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k")) {
		event.preventDefault();
		palette.value = true;
	}
}

onMounted(() => { loadSession(); addEventListener("keydown", onKey); });
onUnmounted(() => removeEventListener("keydown", onKey));
</script>
