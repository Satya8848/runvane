<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<!-- Account menu: avatar with initials, then profile, activity, AI, admin and sign-out actions. -->
<template>
	<div ref="root" class="relative">
		<button class="flex items-center gap-2 rounded-full border border-ink-200 py-1 pl-1 pr-2.5 text-sm hover:border-ink-300 hover:bg-ink-50 dark:border-ink-700 dark:hover:bg-ink-800"
			:aria-expanded="open" aria-haspopup="menu" aria-label="Account menu" @click="open = !open">
			<span class="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-signal-500 text-xs font-bold text-white">{{ initials }}</span>
			<span class="hidden font-medium text-ink-700 dark:text-ink-200 lg:inline">{{ firstName }}</span>
			<span class="hidden text-xs text-ink-400 sm:inline" title="Reputation">★ {{ session.reputation }}</span>
			<svg class="h-4 w-4 text-ink-400 transition" :class="open ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.3 7.3a1 1 0 0 1 1.4 0L10 10.6l3.3-3.3a1 1 0 1 1 1.4 1.4l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 0 1 0-1.4z"/></svg>
		</button>
		<div v-if="open" class="absolute right-0 z-40 mt-2 w-72 overflow-hidden rounded-2xl border border-ink-100 bg-white shadow-xl dark:border-ink-800 dark:bg-ink-900" role="menu" @keydown.esc="open = false">
			<div class="flex items-center gap-3 border-b border-ink-100 p-4 dark:border-ink-800">
				<span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-signal-500 text-sm font-bold text-white">{{ initials }}</span>
				<div class="min-w-0">
					<p class="truncate font-semibold">{{ session.display_name }}</p>
					<p class="truncate text-xs text-ink-500">{{ session.user }}</p>
					<p class="mt-0.5 text-xs text-ink-500">★ {{ session.reputation }} reputation</p>
				</div>
			</div>
			<nav class="p-1.5 text-sm">
				<router-link v-for="item in items" :key="item.to" :to="item.to" class="flex items-center gap-3 rounded-xl px-3 py-2 hover:bg-ink-50 dark:hover:bg-ink-800" role="menuitem" @click="open = false">
					<span class="w-5 text-center" aria-hidden="true">{{ item.icon }}</span>{{ item.label }}
				</router-link>
				<template v-if="session.is_admin || session.is_moderator">
					<div class="my-1.5 border-t border-ink-100 dark:border-ink-800"></div>
					<p class="px-3 pb-1 pt-1 text-[11px] font-semibold uppercase tracking-wider text-ink-400">Admin</p>
					<a href="/app" class="flex items-center gap-3 rounded-xl px-3 py-2 hover:bg-ink-50 dark:hover:bg-ink-800" role="menuitem"><span class="w-5 text-center" aria-hidden="true">🛠️</span>Admin desk</a>
					<a v-if="session.is_admin" href="/app/ai-settings" class="flex items-center gap-3 rounded-xl px-3 py-2 hover:bg-ink-50 dark:hover:bg-ink-800" role="menuitem"><span class="w-5 text-center" aria-hidden="true">⚙️</span>AI settings &amp; budget</a>
					<a href="/app/report" class="flex items-center gap-3 rounded-xl px-3 py-2 hover:bg-ink-50 dark:hover:bg-ink-800" role="menuitem"><span class="w-5 text-center" aria-hidden="true">🚩</span>Moderation reports</a>
				</template>
				<div class="my-1.5 border-t border-ink-100 dark:border-ink-800"></div>
				<button class="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20" role="menuitem" @click="logout"><span class="w-5 text-center" aria-hidden="true">↩</span>Sign out</button>
			</nav>
		</div>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { session } from "../api.js";

const root = ref(null);
const open = ref(false);
const items = [
	{ to: "/me", icon: "👤", label: "My profile" },
	{ to: "/me?tab=questions", icon: "💬", label: "My questions & answers" },
	{ to: "/me?tab=boards", icon: "🗺️", label: "My architecture boards" },
	{ to: "/ai", icon: "✨", label: "AI assistant & history" },
	{ to: "/me?tab=settings", icon: "🔑", label: "Settings & AI keys" },
];
const initials = computed(() => (session.display_name || session.user || "?").split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join(""));
const firstName = computed(() => (session.display_name || "").split(" ")[0]);

/**
 * Close the menu on a click outside it.
 *
 * @param {MouseEvent} event - Click.
 * @returns {void}
 */
function outside(event) {
	if (open.value && root.value && !root.value.contains(event.target)) open.value = false;
}

/**
 * Sign out and go home.
 *
 * @returns {Promise<void>}
 */
async function logout() {
	await fetch("/api/method/logout", { method: "POST", headers: { "X-Frappe-CSRF-Token": window.csrf_token || "" } });
	location.href = "/";
}

onMounted(() => document.addEventListener("click", outside));
onBeforeUnmount(() => document.removeEventListener("click", outside));
</script>
