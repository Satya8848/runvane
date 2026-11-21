// Copyright (c) 2026, Satya and contributors. For license information, please see license.txt
import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./style.css";

const page = (name) => () => import(`./pages/${name}.vue`);
const routes = [
	{ path: "/", component: page("Home"), meta: { title: "Runvane" } },
	{ path: "/search", component: page("Search"), meta: { title: "Search" } },
	{ path: "/t/:slug", component: page("Track"), meta: { title: "Role" } },
	{ path: "/playbooks", component: page("Playbooks"), meta: { title: "Playbooks" } },
	{ path: "/playbooks/:slug", component: page("Playbook"), meta: { title: "Playbook" } },
	{ path: "/guides", component: page("Guides"), meta: { title: "Guides" } },
	{ path: "/guides/:slug", component: page("Guide"), meta: { title: "Guide" } },
	{ path: "/glossary", component: page("Glossary"), meta: { title: "Glossary" } },
	{ path: "/interview", component: page("Interview"), meta: { title: "Interview prep" } },
	{ path: "/q", component: page("Forum"), meta: { title: "Forum" } },
	{ path: "/q/:name", component: page("Question"), meta: { title: "Question" } },
	{ path: "/ask", component: page("Ask"), meta: { title: "Ask the community" } },
	{ path: "/ai", component: page("AI"), meta: { title: "AI assistant" } },
	{ path: "/board", component: page("Board"), meta: { title: "Architecture board" } },
	{ path: "/board/:name", component: page("Board"), meta: { title: "Architecture board" } },
	{ path: "/join", component: page("Join"), meta: { title: "Join" } },
	{ path: "/me", component: page("Me"), meta: { title: "My account" } },
	{ path: "/:rest(.*)*", component: page("NotFound"), meta: { title: "Not found" } },
];
const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: (to, from, saved) => saved || (to.hash ? { el: to.hash } : { top: 0 }) });
router.afterEach((to) => (document.title = to.meta.title === "Runvane" ? "Runvane · Fix it faster" : `${to.meta.title} · Runvane`));
createApp(App).use(router).mount("#app");
