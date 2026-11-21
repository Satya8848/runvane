# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Whitelisted forum endpoints. Reading is public; writing needs a signed-in
member and is rate-limited."""

import frappe
from frappe.rate_limiter import rate_limit

from stackpilot.sp_forum.utils import forum
from stackpilot.utils import search as search_engine

SORTS = {"newest": "creation desc", "votes": "votes desc, creation desc", "unanswered": "answer_count asc, creation desc", "active": "modified desc"}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def questions(track=None, tag=None, sort="newest", page=1):
	"""
	List questions.

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.questions`
	**HTTP Method:** GET
	**Parameters:**
		- track (str, optional): Role Track slug.
		- tag (str, optional): Tag.
		- sort (str, optional): newest, votes, unanswered or active.
		- page (int, optional): Page (20 per page).
	**Response:**
	```json
	{"message": {"items": [{"name": "...", "title": "...", "votes": 3, "answer_count": 2, "status": "Answered"}], "total": 41}}
	```
	"""
	filters = {}
	if track:
		filters["role_track"] = track
	if tag:
		filters["tags"] = ["like", f"%{tag}%"]
	page = max(int(page), 1)
	items = frappe.get_all("Question", filters=filters, fields=["name", "title", "role_track", "tags", "votes", "answer_count", "views", "status", "owner", "creation"],
		order_by=SORTS.get(sort, SORTS["newest"]), start=(page - 1) * 20, limit=20, ignore_permissions=True)
	return {"items": items, "total": frappe.db.count("Question", filters)}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def question(name):
	"""
	One question with answers and comments.

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.question`
	**HTTP Method:** GET
	**Parameters:**
		- name (str, required): Question name.
	**Response:**
	```json
	{"message": {"question": {...}, "answers": [{"html": "...", "is_ai": 0, "is_accepted": 1}], "comments": [...], "my_votes": {}}}
	```
	"""
	return forum.question_detail(name)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=5, seconds=60 * 10)
def ask(title, body, role_track=None, tags=None):
	"""
	Ask a question (an AI draft answer is prepared in the background when AI is on).

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.ask`
	**HTTP Method:** POST
	**Parameters:**
		- title (str, required): At least 12 characters.
		- body (str, required): Markdown.
		- role_track (str, optional): Role Track slug.
		- tags (str, optional): Comma-separated, up to 5.
	**Response:**
	```json
	{"message": {"name": "a1b2c3d4"}}
	```
	"""
	name = forum.ask(title, body, role_track, tags)
	frappe.enqueue("stackpilot.sp_ai.tasks.draft_forum_answer", queue="long", question=name, enqueue_after_commit=True)
	return {"name": name}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 10)
def answer(question, body):
	"""
	Answer a question.

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.answer`
	**HTTP Method:** POST
	**Parameters:**
		- question (str, required): Question name.
		- body (str, required): Markdown.
	**Response:**
	```json
	{"message": {"name": "e5f6"}}
	```
	"""
	return {"name": forum.answer(question, body)}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=60, seconds=60 * 10)
def vote(doctype, name, value):
	"""
	Vote on a question, answer or public board (+1, -1, 0 removes).

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.vote`
	**HTTP Method:** POST
	**Parameters:**
		- doctype (str, required): Question, Answer or Architecture Diagram.
		- name (str, required): Record.
		- value (int, required): 1, -1 or 0.
	**Response:**
	```json
	{"message": {"votes": 7}}
	```
	"""
	return {"votes": forum.vote(doctype, name, value)}


@frappe.whitelist(methods=["POST"])
def accept(answer):
	"""
	Accept an answer (question owner or moderator).

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.accept`
	**HTTP Method:** POST
	**Parameters:**
		- answer (str, required): Answer name.
	**Response:**
	```json
	{"message": {"ok": true}}
	```
	"""
	forum.accept(answer)
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 10)
def comment(reference_doctype, reference_name, body):
	"""
	Comment on a question, answer, playbook or board.

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.comment`
	**HTTP Method:** POST
	**Parameters:**
		- reference_doctype (str, required): Question, Answer, Playbook or Architecture Diagram.
		- reference_name (str, required): Record.
		- body (str, required): 3–1000 characters.
	**Response:**
	```json
	{"message": {"name": "c1"}}
	```
	"""
	forum.require_member()
	if reference_doctype not in ("Question", "Answer", "Playbook", "Architecture Diagram") or not 3 <= len((body or "").strip()) <= 1000:
		frappe.throw(frappe._("Comments are 3 to 1000 characters."))
	doc = frappe.get_doc({"doctype": "SP Comment", "reference_doctype": reference_doctype, "reference_name": reference_name, "body": body.strip()}).insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def report(reference_doctype, reference_name, reason, details=None):
	"""
	Report a post to moderators.

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.report`
	**HTTP Method:** POST
	**Parameters:**
		- reference_doctype (str, required): Doctype of the post.
		- reference_name (str, required): Post name.
		- reason (str, required): Spam, Abuse, Off-topic, Unsafe advice or Other.
		- details (str, optional): Free text.
	**Response:**
	```json
	{"message": {"ok": true}}
	```
	"""
	forum.require_member()
	frappe.get_doc({"doctype": "Report", "reference_doctype": reference_doctype, "reference_name": reference_name, "reason": reason, "details": details}).insert(ignore_permissions=True)
	return {"ok": True}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def similar(title):
	"""
	Questions and playbooks similar to a draft title (shown while asking).

	**Endpoint:** `/api/method/stackpilot.sp_forum.api.v1.forum.similar`
	**HTTP Method:** GET
	**Parameters:**
		- title (str, required): Draft title.
	**Response:**
	```json
	{"message": [{"kind": "playbook", "title": "...", "url": "..."}]}
	```
	"""
	if len((title or "").strip()) < 8:
		return []
	return [hit for hit in search_engine.search(title[:200], limit=8)["hits"] if hit["kind"] in ("question", "playbook")][:6]
