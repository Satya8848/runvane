# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""One search over playbooks, guides, questions, terms, interview items and
public diagrams. Uses Meilisearch (typo-tolerant, fast) when it is
reachable, and falls back to a database LIKE search so search never breaks."""

import re

import frappe
import requests

from stackpilot.utils.markdown import excerpt

INDEX = "stackpilot"
TIMEOUT = 3

# doctype -> (kind label, title field, text fields, url builder, extra filter)
SOURCES = {
	"Playbook": ("playbook", "title", ("summary", "symptoms", "causes", "fix", "tags"), lambda d: f"/playbooks/{d.name}", {"published": 1}),
	"Config Guide": ("guide", "title", ("intro", "body", "tags", "category"), lambda d: f"/guides/{d.name}", {"published": 1}),
	"Question": ("question", "title", ("body", "tags"), lambda d: f"/q/{d.name}", {"status": ["!=", "Closed"]}),
	"SP Term": ("term", "term", ("short_definition", "explanation"), lambda d: f"/glossary#{frappe.scrub(d.name)}", {}),
	"Interview Item": ("interview", "question", ("answer", "topic"), lambda d: f"/interview?q={d.name}", {}),
	"Architecture Diagram": ("diagram", "title", ("description", "tags"), lambda d: f"/board/{d.name}", {"visibility": "Public"}),
}


def _meili():
	"""
	Meilisearch URL and key from site config, or (None, None).

	Returns:
		tuple[str|None, str|None]: (url, key)
	"""
	return frappe.conf.get("meili_url"), frappe.conf.get("meili_key")


def document_for(doc):
	"""
	Build the search document for one record.

	Parameters:
		doc (Document, required): A record of a SOURCES doctype.

	Returns:
		dict: Search document.
	"""
	kind, title_field, text_fields, url, _filters = SOURCES[doc.doctype]
	text = " ".join(str(doc.get(f) or "") for f in text_fields)
	return {
		"id": re.sub(r"[^A-Za-z0-9_-]", "_", f"{kind}-{doc.name}")[:500],
		"kind": kind, "name": doc.name, "title": doc.get(title_field), "url": url(doc),
		"role_track": doc.get("role_track"), "tags": [t.strip() for t in (doc.get("tags") or "").split(",") if t.strip()],
		"excerpt": excerpt(text, 240), "text": frappe.utils.strip_html(text)[:20000],
	}


def index_doc(doc, method=None):
	"""
	doc_events hook: add, update or remove one record in the index.

	Parameters:
		doc (Document, required): Saved record.
		method (str, optional): Hook name.

	Returns:
		None
	"""
	url, key = _meili()
	if not url or doc.doctype not in SOURCES:
		return
	_kind, _t, _f, _u, filters = SOURCES[doc.doctype]
	visible = all(_matches(doc.get(k), v) for k, v in filters.items())
	try:
		if visible and method != "on_trash":
			requests.post(f"{url}/indexes/{INDEX}/documents", json=[document_for(doc)], headers=_headers(key), timeout=TIMEOUT)
		else:
			requests.delete(f"{url}/indexes/{INDEX}/documents/{document_for(doc)['id']}", headers=_headers(key), timeout=TIMEOUT)
	except requests.RequestException:
		frappe.log_error(title="StackPilot search index", message=frappe.get_traceback())


def rebuild():
	"""
	Recreate the index settings and push every searchable record.
	`bench --site <site> execute stackpilot.utils.search.rebuild`

	Returns:
		int: Documents sent.
	"""
	url, key = _meili()
	if not url:
		return 0
	headers = _headers(key)
	requests.post(f"{url}/indexes", json={"uid": INDEX, "primaryKey": "id"}, headers=headers, timeout=TIMEOUT)
	requests.patch(f"{url}/indexes/{INDEX}/settings", headers=headers, timeout=TIMEOUT, json={
		"searchableAttributes": ["title", "tags", "excerpt", "text"],
		"filterableAttributes": ["kind", "role_track", "tags"],
		"displayedAttributes": ["id", "kind", "name", "title", "url", "role_track", "tags", "excerpt"],
	})
	docs = []
	for doctype, (_k, _t, _f, _u, filters) in SOURCES.items():
		for name in frappe.get_all(doctype, filters=filters, pluck="name"):
			docs.append(document_for(frappe.get_doc(doctype, name)))
	for start in range(0, len(docs), 500):
		requests.post(f"{url}/indexes/{INDEX}/documents", json=docs[start:start + 500], headers=headers, timeout=30)
	return len(docs)


def search(query, kind=None, role_track=None, limit=20):
	"""
	Search everything. Meilisearch first, database fallback.

	Parameters:
		query (str, required): Search text.
		kind (str, optional): playbook, guide, question, term, interview or diagram.
		role_track (str, optional): Role Track slug.
		limit (int, optional): Maximum hits.

	Returns:
		dict: {"hits": [...], "engine": "meilisearch"|"database"}
	"""
	url, key = _meili()
	if url:
		filters = [f'kind = "{kind}"'] if kind else []
		if role_track:
			filters.append(f'role_track = "{role_track}"')
		try:
			response = requests.post(f"{url}/indexes/{INDEX}/search", headers=_headers(key), timeout=TIMEOUT, json={
				"q": query, "limit": int(limit), "filter": " AND ".join(filters) or None,
				"attributesToHighlight": ["title", "excerpt"], "highlightPreTag": "<mark>", "highlightPostTag": "</mark>",
			})
			response.raise_for_status()
			hits = [{**hit, "title_html": hit.get("_formatted", {}).get("title"), "excerpt_html": hit.get("_formatted", {}).get("excerpt")} for hit in response.json()["hits"]]
			for hit in hits:
				hit.pop("_formatted", None)
			return {"hits": hits, "engine": "meilisearch"}
		except requests.RequestException:
			pass
	return {"hits": _db_search(query, kind, role_track, limit), "engine": "database"}


def _db_search(query, kind, role_track, limit):
	"""
	LIKE search over titles and main text, used when Meilisearch is down.

	Parameters:
		query (str, required): Search text.
		kind (str, optional): Kind filter.
		role_track (str, optional): Role filter.
		limit (int, required): Maximum hits.

	Returns:
		list[dict]: Hits.
	"""
	hits = []
	like = f"%{query}%"
	for doctype, (k, title_field, text_fields, _u, filters) in SOURCES.items():
		if kind and k != kind:
			continue
		meta = frappe.get_meta(doctype)
		extra = dict(filters)
		if role_track and meta.has_field("role_track"):
			extra["role_track"] = role_track
		or_filters = {title_field: ["like", like], text_fields[0]: ["like", like]}
		for name in frappe.get_all(doctype, filters=extra, or_filters=or_filters, pluck="name", limit=limit):
			hits.append(document_for(frappe.get_doc(doctype, name)))
	return hits[:limit]


def _matches(value, condition):
	"""
	Check one SOURCES filter against a value.

	Parameters:
		value (any, required): Field value.
		condition (any, required): Expected value or ["!=", x].

	Returns:
		bool: Whether it matches.
	"""
	if isinstance(condition, list) and condition[0] == "!=":
		return value != condition[1]
	return value == condition


def _headers(key):
	"""
	Meilisearch request headers.

	Parameters:
		key (str, optional): Master or search key.

	Returns:
		dict: Headers.
	"""
	return {"Authorization": f"Bearer {key}"} if key else {}
