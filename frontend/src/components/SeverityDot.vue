<!-- Copyright (c) 2026, Satya and contributors. For license information, please see license.txt -->
<template><span class="inline-block h-2.5 w-2.5 shrink-0 rounded-full" :class="cls" :title="`${level} severity`" :aria-label="`${level} severity`"></span></template>
<script setup>
import { computed } from "vue";
const props = defineProps({ level: { type: String, default: "Medium" } });
const cls = computed(() => ({ Critical: "bg-red-600", High: "bg-orange-500", Medium: "bg-amber-400", Low: "bg-emerald-500" })[props.level] || "bg-ink-300");
</script>
