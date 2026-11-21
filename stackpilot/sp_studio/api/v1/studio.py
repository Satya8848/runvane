# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Whitelisted endpoints for the architecture board: save, list, open,
fork, text-to-diagram and AI design review."""

import json
import re

import frappe
from frappe.rate_limiter import rate_limit

from stackpilot.sp_ai.utils.gateway import run
from stackpilot.sp_ai.utils.masking import mask
from stackpilot.sp_forum.utils.forum import require_member
from stackpilot.utils.markdown import render

DIAGRAM_SYSTEM = ("You are a principal cloud and solution architect. Output only valid Mermaid flowchart code "
	"(start with 'flowchart LR' or 'flowchart TB'), with subgraphs for VPCs/regions/clusters, short node labels, "
	"databases as [(name)], queues as [[name]]. No explanations, no code fences.")
REVIEW_SYSTEM = ("You are a principal solution architect reviewing a design against the Well-Architected pillars: "
	"reliability, security, performance, cost and operations. Be specific to the components you see.")


@frappe.whitelist(allow_guest=True, methods=["GET"])
def diagrams(mine=0):
	"""
	Public boards, or the member's own boards.

	**Endpoint:** `/api/method/stackpilot.sp_studio.api.v1.studio.diagrams`
	**HTTP Method:** GET
	**Parameters:**
		- mine (int, optional): 1 for the member's own boards.
	**Response:**
	```json
	{"message": [{"name": "...", "title": "...", "visibility": "Public", "votes": 3, "owner": "..."}]}
	```
	"""
	filters = {"owner": require_member()} if int(mine) else {"visibility": "Public"}
	return frappe.get_all("Architecture Diagram", filters=filters, fields=["name", "title", "description", "visibility", "votes", "owner", "modified"], order_by="modified desc", limit=60, ignore_permissions=True)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def diagram(name):
	"""
	Open one board (public, unlisted, or your own private board) with its reviews.

	**Endpoint:** `/api/method/stackpilot.sp_studio.api.v1.studio.diagram`
	**HTTP Method:** GET
	**Parameters:**
		- name (str, required): Board name.
	**Response:**
	```json
	{"message": {"name": "...", "title": "...", "mermaid": "flowchart LR ...", "is_owner": true, "reviews": [{"is_ai": 1, "html": "..."}]}}
	```
	"""
	doc = frappe.get_doc("Architecture Diagram", name)
	if doc.visibility == "Private" and doc.owner != frappe.session.user:
		raise frappe.PermissionError
	reviews = frappe.get_all("Diagram Review", filters={"diagram": name}, fields=["name", "owner", "is_ai", "body", "creation"], order_by="creation desc", ignore_permissions=True)
	for review in reviews:
		review["html"] = render(review.pop("body"))
	return {"name": doc.name, "title": doc.title, "description": doc.description, "mermaid": doc.mermaid, "visibility": doc.visibility,
		"votes": doc.votes, "tags": doc.tags, "is_owner": doc.owner == frappe.session.user, "reviews": reviews}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=60, seconds=60 * 10)
def save(title, mermaid, name=None, description=None, visibility="Private", tags=None):
	"""
	Create or update a board you own.

	**Endpoint:** `/api/method/stackpilot.sp_studio.api.v1.studio.save`
	**HTTP Method:** POST
	**Parameters:**
		- title (str, required): Title.
		- mermaid (str, required): Mermaid source (≤ 20,000 characters).
		- name (str, optional): Existing board to update.
		- description (str, optional): Description.
		- visibility (str, optional): Public, Unlisted or Private.
		- tags (str, optional): Comma-separated tags.
	**Response:**
	```json
	{"message": {"name": "..."}}
	```
	"""
	user = require_member()
	if len(mermaid or "") > 20000 or not (title or "").strip():
		frappe.throw(frappe._("Give the board a title; diagrams are limited to 20,000 characters."))
	values = {"title": title.strip()[:120], "mermaid": mermaid, "description": description, "visibility": visibility if visibility in ("Public", "Unlisted", "Private") else "Private", "tags": tags}
	if name:
		doc = frappe.get_doc("Architecture Diagram", name)
		if doc.owner != user:
			raise frappe.PermissionError
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Architecture Diagram", **values}).insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=15, seconds=60 * 10)
def generate(description):
	"""
	Turn a plain-language description into a Mermaid architecture diagram.

	**Endpoint:** `/api/method/stackpilot.sp_studio.api.v1.studio.generate`
	**HTTP Method:** POST
	**Parameters:**
		- description (str, required): What the system does and runs on.
	**Response:**
	```json
	{"message": {"mermaid": "flowchart LR ...", "provider": "claude"}}
	```
	"""
	require_member()
	text, _masked = mask((description or "")[:4000])
	result = run("diagram", DIAGRAM_SYSTEM, [{"role": "user", "content": text}], max_tokens=1500)
	code = re.sub(r"^```(?:mermaid)?|```$", "", result["text"].strip(), flags=re.M).strip()
	return {"mermaid": code, "provider": result["provider"]}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=10, seconds=60 * 10)
def review(name=None, mermaid=None, context=None):
	"""
	AI design review of a board (saved, or the unsaved Mermaid you send).

	**Endpoint:** `/api/method/stackpilot.sp_studio.api.v1.studio.review`
	**HTTP Method:** POST
	**Parameters:**
		- name (str, optional): Saved board (stores the review on it).
		- mermaid (str, optional): Unsaved Mermaid source.
		- context (str, optional): Traffic, SLOs, budget, compliance.
	**Response:**
	```json
	{"message": {"html": "<h3>Reliability</h3>...", "scores": {"reliability": 3, "security": 2}}}
	```
	"""
	user = require_member()
	if name:
		doc = frappe.get_doc("Architecture Diagram", name)
		if doc.visibility == "Private" and doc.owner != user:
			raise frappe.PermissionError
		mermaid = doc.mermaid
	ctx, _masked = mask((context or "")[:2000])
	prompt = (f"Design (Mermaid):\n{(mermaid or '')[:15000]}\n\nContext: {ctx or 'not given'}\n\n"
		"Start with one line of JSON: {\"reliability\":1-5,\"security\":1-5,\"performance\":1-5,\"cost\":1-5,\"operations\":1-5}. "
		"Then Markdown: for each pillar the top risks (name the component), the fix, and an improved-design summary. "
		"End with a short 'Interview talking points' list.")
	result = run("diagram", REVIEW_SYSTEM, [{"role": "user", "content": prompt}], max_tokens=2200)
	first, _, rest = result["text"].strip().partition("\n")
	try:
		scores = json.loads(first.strip().strip("`"))
	except ValueError:
		scores, rest = {}, result["text"]
	if name:
		frappe.get_doc({"doctype": "Diagram Review", "diagram": name, "is_ai": 1, "scores_json": json.dumps(scores), "body": rest}).insert(ignore_permissions=True)
	return {"html": render(rest), "scores": scores, "provider": result["provider"]}
