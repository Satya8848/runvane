// Copyright (c) 2026, Satya and contributors. For license information, please see license.txt
import { reactive } from "vue";

export const KB = "stackpilot.sp_knowledge.api.v1.public";
export const FORUM = "stackpilot.sp_forum.api.v1.forum";
export const AI = "stackpilot.sp_ai.api.v1.ai";
export const STUDIO = "stackpilot.sp_studio.api.v1.studio";

/**
 * Call a whitelisted Frappe method and return its message.
 *
 * @param {string} method - Dotted path.
 * @param {object} [args] - Arguments.
 * @param {"GET"|"POST"} [verb] - HTTP method.
 * @returns {Promise<any>} Message.
 */
export async function call(method, args = {}, verb = "GET") {
	const url = new URL(`/api/method/${method}`, location.origin);
	const init = { method: verb, credentials: "same-origin", headers: { Accept: "application/json" } };
	if (verb === "GET") Object.entries(args).forEach(([k, v]) => v !== undefined && v !== null && v !== "" && url.searchParams.set(k, v));
	else Object.assign(init, { body: JSON.stringify(args), headers: { ...init.headers, "Content-Type": "application/json", "X-Frappe-CSRF-Token": window.csrf_token || "" } });
	const res = await fetch(url, init);
	const data = await res.json().catch(() => ({}));
	if (!res.ok) throw new Error(readError(data, res));
	return data.message;
}

/**
 * POST shorthand.
 *
 * @param {string} method - Dotted path.
 * @param {object} [args] - Arguments.
 * @returns {Promise<any>} Message.
 */
export const post = (method, args) => call(method, args, "POST");

/**
 * Readable error text from a Frappe error response.
 *
 * @param {object} data - JSON body.
 * @param {Response} res - Response.
 * @returns {string} Message.
 */
function readError(data, res) {
	try {
		if (data._server_messages) return JSON.parse(data._server_messages).map((m) => JSON.parse(m).message).join(" ").replace(/<[^>]+>/g, "");
	} catch (e) { /* fall through */ }
	if (res.status === 429) return "Slow down a little: too many requests. Try again in a few minutes.";
	if (res.status === 403) return "Sign in to do this.";
	return data.exception?.split(":").slice(1).join(":").trim() || `${res.status} ${res.statusText}`;
}

export const session = reactive({ loaded: false, logged_in: false, display_name: null, reputation: 0, is_moderator: false });

/**
 * Load who is signed in.
 *
 * @returns {Promise<void>}
 */
export async function loadSession() {
	Object.assign(session, await call(`${KB}.session`).catch(() => ({})), { loaded: true });
}

/**
 * Send the visitor to join (with a link to sign in) and come back here.
 *
 * @returns {void}
 */
export function signIn() {
	location.href = `/join?next=${encodeURIComponent(location.pathname + location.search)}`;
}

export const toast = reactive({ text: "", kind: "ok" });

/**
 * Show a short message.
 *
 * @param {string} text - Message.
 * @param {"ok"|"bad"} [kind] - Colour.
 * @returns {void}
 */
export function notify(text, kind = "ok") {
	Object.assign(toast, { text, kind });
	clearTimeout(notify.t);
	notify.t = setTimeout(() => (toast.text = ""), kind === "bad" ? 8000 : 3500);
}
