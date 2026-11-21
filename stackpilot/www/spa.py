# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Page controller for the single-page app. Sets a real title and
description per URL so links and search engines show the right content."""

import frappe

no_cache = 1
SITE = "StackPilot"
DEFAULT_DESCRIPTION = ("Real-world playbooks, AI log and config analysis, a community forum and an architecture board "
	"for DevOps, DevSecOps, solution architects, programmers, Linux admins, DBAs and cloud engineers.")


def get_context(context):
	"""
	Fill title/description for the requested path and boot data for the app.

	Parameters:
		context (frappe._dict, required): Page context.

	Returns:
		frappe._dict: The context.
	"""
	path = (frappe.request.path or "/").strip("/").split("/")
	title, description = _meta(path)
	context.meta_title = f"{title} · {SITE}" if title else f"{SITE} · Fix it faster"
	context.meta_description = (description or DEFAULT_DESCRIPTION)[:300]
	context.boot = {"user": frappe.session.user}
	return context


def _meta(parts):
	"""
	Title and description for a path.

	Parameters:
		parts (list[str], required): Path segments.

	Returns:
		tuple[str|None, str|None]: (title, description)
	"""
	if len(parts) < 2:
		return None, None
	kind, name = parts[0], parts[1]
	lookups = {"playbooks": ("Playbook", "title", "summary"), "guides": ("Config Guide", "title", "intro"),
		"q": ("Question", "title", "title"), "t": ("Role Track", "title", "tagline")}
	if kind not in lookups:
		return None, None
	doctype, title_field, desc_field = lookups[kind]
	row = frappe.db.get_value(doctype, name, [title_field, desc_field], as_dict=True)
	return (row.get(title_field), row.get(desc_field)) if row else (None, None)
