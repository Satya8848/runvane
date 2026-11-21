# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Whitelisted AI endpoints for members: chat, analysers, own keys and status."""

import frappe
from frappe.rate_limiter import rate_limit

from stackpilot.sp_ai.utils import features, gateway
from stackpilot.sp_forum.utils.forum import require_member


@frappe.whitelist(methods=["GET"])
def status():
	"""
	What AI the member can use now.

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.status`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": {"enabled": true, "site_keys": ["claude"], "own_keys": [], "used_today": 1200, "quota": 60000, "budget_reached": false}}
	```
	"""
	return gateway.status(require_member())


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 10)
def chat(message, conversation=None, role_track=None):
	"""
	Ask anything; answers use platform content and cite it.

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.chat`
	**HTTP Method:** POST
	**Parameters:**
		- message (str, required): Question (secrets are masked).
		- conversation (str, optional): Continue a conversation.
		- role_track (str, optional): Role Track slug.
	**Response:**
	```json
	{"message": {"conversation": "...", "answer": "markdown", "sources": [...], "masked": [], "provider": "claude"}}
	```
	"""
	require_member()
	return features.chat(message, conversation, role_track)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 10)
def analyse(kind, text, role_track=None, question=None):
	"""
	Analyse logs, errors, configs, SQL, Dockerfiles or pipelines.

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.analyse`
	**HTTP Method:** POST
	**Parameters:**
		- kind (str, required): logs, error, config, sql, dockerfile or pipeline.
		- text (str, required): Pasted content (secrets are masked first).
		- role_track (str, optional): Role Track slug.
		- question (str, optional): What you want to know.
	**Response:**
	```json
	{"message": {"conversation": "...", "answer": "markdown", "masked": ["AWS access key"], "provider": "claude"}}
	```
	"""
	require_member()
	return features.analyse(kind, text, role_track, question)


@frappe.whitelist(methods=["GET"])
def conversations():
	"""
	The member's recent AI conversations.

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.conversations`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": [{"name": "...", "title": "...", "feature": "chat", "creation": "..."}]}
	```
	"""
	user = require_member()
	return frappe.get_all("AI Conversation", filters={"user": user}, fields=["name", "title", "feature", "creation"], order_by="creation desc", limit=30, ignore_permissions=True)


@frappe.whitelist(methods=["GET"])
def conversation(name):
	"""
	Messages of one of the member's conversations.

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.conversation`
	**HTTP Method:** GET
	**Parameters:**
		- name (str, required): Conversation.
	**Response:**
	```json
	{"message": [{"role": "user", "content": "...", "masked": ""}, {"role": "assistant", "content": "..."}]}
	```
	"""
	user = require_member()
	if frappe.db.get_value("AI Conversation", name, "user") != user:
		raise frappe.PermissionError
	return frappe.get_all("AI Message", filters={"conversation": name}, fields=["role", "content", "masked", "sources_json", "provider"], order_by="creation asc", ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def save_key(provider, api_key, model=None):
	"""
	Save the member's own API key for a provider (replaces an existing one).

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.save_key`
	**HTTP Method:** POST
	**Parameters:**
		- provider (str, required): claude, gemini, groq or openai.
		- api_key (str, required): The key (stored encrypted, never shown again).
		- model (str, optional): Model id override.
	**Response:**
	```json
	{"message": {"ok": true}}
	```
	"""
	user = require_member()
	if provider not in ("claude", "gemini", "groq", "openai") or len(api_key or "") < 20:
		frappe.throw(frappe._("Choose a provider and paste a valid key."))
	for name in frappe.get_all("AI Provider Key", filters={"user": user, "provider": provider}, pluck="name", ignore_permissions=True):
		frappe.delete_doc("AI Provider Key", name, ignore_permissions=True)
	frappe.get_doc({"doctype": "AI Provider Key", "user": user, "provider": provider, "api_key": api_key, "model": model}).insert(ignore_permissions=True)
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def delete_key(provider):
	"""
	Remove the member's own key for a provider.

	**Endpoint:** `/api/method/stackpilot.sp_ai.api.v1.ai.delete_key`
	**HTTP Method:** POST
	**Parameters:**
		- provider (str, required): Provider.
	**Response:**
	```json
	{"message": {"ok": true}}
	```
	"""
	user = require_member()
	for name in frappe.get_all("AI Provider Key", filters={"user": user, "provider": provider}, pluck="name", ignore_permissions=True):
		frappe.delete_doc("AI Provider Key", name, ignore_permissions=True)
	return {"ok": True}
