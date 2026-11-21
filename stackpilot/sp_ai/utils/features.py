# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""AI features: grounded chat, role analysers and forum draft answers.
Every user text is masked for secrets before it is stored or sent."""

import json

import frappe
from frappe import _

from stackpilot.sp_ai.utils.gateway import run
from stackpilot.sp_ai.utils.masking import mask
from stackpilot.utils import search as search_engine

BASE_SYSTEM = (
	"You are StackPilot, a senior engineer helping DevOps, DevSecOps, solution architects, programmers, "
	"Linux administrators, database administrators and cloud engineers. Answer precisely and practically: "
	"commands in fenced code blocks, real config, the why behind each step, and risks. Say when you are not sure. "
	"Never ask for secrets. Never claim to have run anything. Use Markdown."
)
ANALYSERS = {
	"logs": "Analyse these logs. Find the first real error, group repeated errors, and explain the chain of events.",
	"error": "Analyse this error or stack trace. Name the failing component and the most likely root cause.",
	"config": "Review this configuration (nginx, Kubernetes, Terraform, Ansible, Docker, systemd...). Find bugs, security risks and performance issues.",
	"sql": "Analyse this SQL / EXPLAIN output. Find why it is slow and what index or rewrite fixes it.",
	"dockerfile": "Review this Dockerfile for size, cache efficiency, security (root user, secrets, pinned versions) and correctness.",
	"pipeline": "Review this CI/CD pipeline (Azure DevOps, Jenkins, GitHub Actions, GitLab) for correctness, speed and security (secrets, OIDC, permissions).",
}
ANALYSE_FORMAT = (
	"Reply with these sections: **Summary** (2 lines), **Likely root cause**, **Evidence** (quote the exact lines), "
	"**Fix** (numbered steps with commands or corrected config), **Risk** (Low/Medium/High and why), **Prevent it next time**."
)


def chat(message, conversation=None, role_track=None):
	"""
	Answer a question using platform content as context, and keep the conversation.

	Parameters:
		message (str, required): The member's message.
		conversation (str, optional): Existing AI Conversation to continue.
		role_track (str, optional): Role Track slug for tone and focus.

	Returns:
		dict: {"conversation", "answer", "sources", "masked", "provider"}
	"""
	text, masked = mask((message or "").strip()[:12000])
	if not text:
		frappe.throw(_("Type a question."))
	conv = _conversation(conversation, "chat", text, role_track)
	hits = [h for h in search_engine.search(text[:200], limit=6)["hits"]][:5]
	context = "\n".join(f"- [{h['kind']}] {h['title']} ({h['url']}): {h.get('excerpt', '')}" for h in hits)
	system = BASE_SYSTEM + (f"\nThe member works as: {role_track}." if role_track else "") + (
		f"\n\nRelevant StackPilot pages (cite them by title and link when you use them):\n{context}" if context else "")
	history = frappe.get_all("AI Message", filters={"conversation": conv}, fields=["role", "content"], order_by="creation desc", limit=10, ignore_permissions=True)[::-1]
	messages = [{"role": m.role, "content": m.content} for m in history] + [{"role": "user", "content": text}]
	result = run("chat", system, messages)
	_store(conv, "user", text, masked=masked)
	_store(conv, "assistant", result["text"], result=result, sources=hits)
	return {"conversation": conv, "answer": result["text"], "sources": hits, "masked": masked, "provider": result["provider"]}


def analyse(kind, text, role_track=None, question=None):
	"""
	Analyse pasted logs, errors, configs, SQL, Dockerfiles or pipelines.

	Parameters:
		kind (str, required): Key of ANALYSERS.
		text (str, required): Pasted content.
		role_track (str, optional): Role Track slug.
		question (str, optional): What the member wants to know.

	Returns:
		dict: {"conversation", "answer", "masked", "provider"}
	"""
	if kind not in ANALYSERS:
		frappe.throw(_("Unknown analyser."))
	content, masked = mask((text or "")[:40000])
	if len(content.strip()) < 10:
		frappe.throw(_("Paste the logs, error or config to analyse."))
	ask = (question or "").strip()[:1000]
	prompt = f"{ANALYSERS[kind]}\n{ANALYSE_FORMAT}\n" + (f"\nThe member asks: {ask}\n" if ask else "") + f"\n```\n{content}\n```"
	conv = _conversation(None, "analyse", f"{kind}: {ask or content[:60]}", role_track)
	result = run("analyse", BASE_SYSTEM, [{"role": "user", "content": prompt}], max_tokens=2200)
	_store(conv, "user", prompt, masked=masked)
	_store(conv, "assistant", result["text"], result=result)
	return {"conversation": conv, "answer": result["text"], "masked": masked, "provider": result["provider"]}


def draft_forum_answer(question):
	"""
	Write a clearly-labelled AI draft answer to a new question (background job).

	Parameters:
		question (str, required): Question name.

	Returns:
		None
	"""
	from stackpilot.sp_forum.utils.forum import answer as post_answer

	q = frappe.get_doc("Question", question)
	body, _masked = mask(q.body or "")
	hits = [h for h in search_engine.search(q.title, limit=5)["hits"] if h["kind"] == "playbook"][:3]
	context = "\n".join(f"- {h['title']} ({h['url']})" for h in hits)
	prompt = (f"Question title: {q.title}\nRole: {q.role_track or 'unknown'}\nTags: {q.tags or ''}\n\n{body}\n\n"
		"Write a helpful first answer: likely causes, how to confirm each (commands), the fix, and what to check next. "
		"Keep it under 400 words." + (f"\nRelated playbooks you may link:\n{context}" if context else ""))
	try:
		result = run("forum", BASE_SYSTEM, [{"role": "user", "content": prompt}], user=None, max_tokens=1200)
	except Exception as exc:
		frappe.db.set_value("Question", question, "ai_draft_status", "Skipped" if "configured" in str(exc) or "turned off" in str(exc) else "Failed", update_modified=False)
		return
	note = "\n\n---\n*AI draft by StackPilot ({0}). Check it before you run anything; vote or answer to improve it.*".format(result["provider"])
	post_answer(question, result["text"] + note, is_ai=True, provider=result["provider"])
	frappe.db.set_value("Question", question, "ai_draft_status", "Done", update_modified=False)


def _conversation(name, feature, title, role_track):
	"""
	Reuse the member's conversation or start a new one.

	Parameters:
		name (str, optional): Conversation name.
		feature (str, required): Feature.
		title (str, required): First message (for the title).
		role_track (str, optional): Role Track.

	Returns:
		str: Conversation name.
	"""
	if name and frappe.db.get_value("AI Conversation", name, "user") == frappe.session.user:
		return name
	return frappe.get_doc({"doctype": "AI Conversation", "user": frappe.session.user, "feature": feature, "title": title[:80],
		"role_track": role_track or None}).insert(ignore_permissions=True).name


def _store(conversation, role, content, masked=None, result=None, sources=None):
	"""
	Save one message.

	Parameters:
		conversation (str, required): Conversation.
		role (str, required): user or assistant.
		content (str, required): Text.
		masked (list, optional): Masked labels.
		result (dict, optional): Provider result.
		sources (list, optional): Search hits used.

	Returns:
		None
	"""
	result = result or {}
	frappe.get_doc({"doctype": "AI Message", "conversation": conversation, "role": role, "content": content,
		"masked": ", ".join(masked or []), "sources_json": json.dumps(sources or []), "provider": result.get("provider"),
		"model": result.get("model"), "tokens_in": result.get("tokens_in"), "tokens_out": result.get("tokens_out")}).insert(ignore_permissions=True)
