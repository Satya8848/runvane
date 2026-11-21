# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Public (guest-readable) endpoints: home, role tracks, playbooks, guides,
glossary, interview bank, diagram templates and search."""

import frappe
from frappe.query_builder.functions import Count

from stackpilot.utils import search as search_engine
from stackpilot.utils.markdown import render

PLAYBOOK_SECTIONS = ("symptoms", "causes", "diagnose", "fix", "prevent")


@frappe.whitelist(allow_guest=True, methods=["GET"])
def home():
	"""
	Data for the home page: role tracks with counts, newest questions, popular playbooks, totals.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.home`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": {"tracks": [{"slug": "devops", "title": "DevOps Engineer", "playbooks": 5}], "questions": [...], "popular": [...], "totals": {"playbooks": 32}}}
	```
	"""
	tracks = frappe.get_all("Role Track", fields=["slug", "title", "tagline", "icon", "color"], order_by="sort_order asc", ignore_permissions=True)
	playbook = frappe.qb.DocType("Playbook")
	counts = dict(frappe.qb.from_(playbook).select(playbook.role_track, Count(playbook.name)).where(playbook.published == 1).groupby(playbook.role_track).run())
	for track in tracks:
		track["playbooks"] = counts.get(track.slug, 0)
	return {
		"tracks": tracks,
		"questions": frappe.get_all("Question", filters={"status": ["!=", "Closed"]}, fields=["name", "title", "role_track", "votes", "answer_count", "status", "creation"], order_by="creation desc", limit=6, ignore_permissions=True),
		"popular": frappe.get_all("Playbook", filters={"published": 1}, fields=["name", "title", "role_track", "summary", "severity"], order_by="views desc, creation asc", limit=6, ignore_permissions=True),
		"totals": {doctype.lower().replace(" ", "_"): frappe.db.count(doctype) for doctype in ("Playbook", "Config Guide", "Question", "SP Term", "Interview Item", "Diagram Template")},
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def track(slug):
	"""
	One role track with its playbooks, recent questions and related guides.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.track`
	**HTTP Method:** GET
	**Parameters:**
		- slug (str, required): Role Track slug, e.g. "dba".
	**Response:**
	```json
	{"message": {"track": {...}, "playbooks": [...], "questions": [...]}}
	```
	"""
	doc = frappe.get_doc("Role Track", slug)
	return {
		"track": {f: doc.get(f) for f in ("slug", "title", "tagline", "icon", "color", "description")},
		"playbooks": frappe.get_all("Playbook", filters={"role_track": slug, "published": 1}, fields=["name", "title", "summary", "severity", "tags"], order_by="severity desc, title asc", ignore_permissions=True),
		"questions": frappe.get_all("Question", filters={"role_track": slug}, fields=["name", "title", "votes", "answer_count", "status", "creation"], order_by="creation desc", limit=10, ignore_permissions=True),
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def playbook(slug):
	"""
	One playbook with each section rendered to safe HTML. Counts a view.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.playbook`
	**HTTP Method:** GET
	**Parameters:**
		- slug (str, required): Playbook slug.
	**Response:**
	```json
	{"message": {"title": "...", "summary": "...", "sections": {"symptoms": "<ul>...</ul>", "diagnose": "<pre>...</pre>"}, "related": [...]}}
	```
	"""
	doc = frappe.get_doc("Playbook", slug)
	if not doc.published:
		raise frappe.DoesNotExistError
	frappe.db.set_value("Playbook", slug, "views", (doc.views or 0) + 1, update_modified=False)
	related = [hit for hit in search_engine.search(doc.title, limit=8)["hits"] if hit.get("name") != slug][:5]
	return {
		"name": doc.name, "title": doc.title, "summary": doc.summary, "severity": doc.severity, "role_track": doc.role_track,
		"tags": [t.strip() for t in (doc.tags or "").split(",") if t.strip()], "views": (doc.views or 0) + 1,
		"sections": {s: render(doc.get(s)) for s in PLAYBOOK_SECTIONS}, "related": related,
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def guides():
	"""
	List configuration guides grouped by category.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.guides`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": [{"name": "linux", "title": "Linux administration", "category": "Foundations", "intro": "..."}]}
	```
	"""
	return frappe.get_all("Config Guide", filters={"published": 1}, fields=["name", "title", "category", "intro"], order_by="category asc, title asc", ignore_permissions=True)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def guide(slug):
	"""
	One configuration guide rendered to HTML, with its Mermaid diagram source.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.guide`
	**HTTP Method:** GET
	**Parameters:**
		- slug (str, required): Guide slug.
	**Response:**
	```json
	{"message": {"title": "...", "intro": "...", "html": "<h2>...", "diagram": "flowchart LR ..."}}
	```
	"""
	doc = frappe.get_doc("Config Guide", slug)
	return {"name": doc.name, "title": doc.title, "category": doc.category, "intro": doc.intro, "html": render(doc.body), "diagram": doc.diagram}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def glossary():
	"""
	All glossary terms, A to Z.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.glossary`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": [{"name": "HPA", "category": "Kubernetes", "short_definition": "...", "explanation": "..."}]}
	```
	"""
	return frappe.get_all("SP Term", fields=["name", "category", "short_definition", "explanation", "related_terms"], order_by="term asc", ignore_permissions=True)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def interview(topic=None, level=None):
	"""
	Interview questions with answers, filterable by topic and level.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.interview`
	**HTTP Method:** GET
	**Parameters:**
		- topic (str, optional): Topic.
		- level (str, optional): Junior, Mid or Senior.
	**Response:**
	```json
	{"message": {"items": [{"name": "...", "question": "...", "answer_html": "...", "topic": "...", "level": "Mid"}], "topics": [...]}}
	```
	"""
	filters = {k: v for k, v in (("topic", topic), ("level", level)) if v}
	rows = frappe.get_all("Interview Item", filters=filters, fields=["name", "question", "topic", "level", "answer"], order_by="topic asc", ignore_permissions=True)
	for row in rows:
		row["answer_html"] = render(row.pop("answer"))
	topics = frappe.get_all("Interview Item", pluck="topic", distinct=True, order_by="topic asc", ignore_permissions=True)
	return {"items": rows, "topics": topics}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def templates():
	"""
	Architecture templates to start a board from.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.templates`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": [{"name": "3-tier web app on AWS", "category": "AWS", "description": "...", "mermaid": "flowchart LR ..."}]}
	```
	"""
	return frappe.get_all("Diagram Template", fields=["name", "category", "description", "mermaid"], order_by="category asc", ignore_permissions=True)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def search(q, kind=None, track=None, limit=20):
	"""
	Search playbooks, guides, questions, terms, interview items and public boards.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.search`
	**HTTP Method:** GET
	**Parameters:**
		- q (str, required): Search text.
		- kind (str, optional): playbook, guide, question, term, interview or diagram.
		- track (str, optional): Role Track slug.
		- limit (int, optional): Maximum hits (≤ 50).
	**Response:**
	```json
	{"message": {"hits": [{"kind": "playbook", "title": "...", "url": "/playbooks/...", "excerpt": "..."}], "engine": "meilisearch"}}
	```
	"""
	q = (q or "").strip()[:200]
	if not q:
		return {"hits": [], "engine": None}
	return search_engine.search(q, kind=kind, role_track=track, limit=min(int(limit), 50))


@frappe.whitelist(allow_guest=True, methods=["GET"])
def session():
	"""
	Who is signed in, for the app header.

	**Endpoint:** `/api/method/stackpilot.sp_knowledge.api.v1.public.session`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": {"user": "Guest", "logged_in": false, "display_name": null, "reputation": 0, "is_moderator": false}}
	```
	"""
	user = frappe.session.user
	if user == "Guest":
		return {"user": "Guest", "logged_in": False, "display_name": None, "reputation": 0, "is_moderator": False}
	profile = frappe.db.get_value("SP Profile", user, ["display_name", "reputation"], as_dict=True) or {}
	roles = frappe.get_roles()
	return {"user": user, "logged_in": True, "display_name": profile.get("display_name") or user.split("@")[0], "reputation": profile.get("reputation") or 0,
		"is_moderator": bool({"SP Moderator", "System Manager"} & set(roles))}
