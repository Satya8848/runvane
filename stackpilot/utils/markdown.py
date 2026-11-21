# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Markdown to safe HTML for everything members write (questions, answers,
comments) and for seeded content."""

import frappe
from frappe.utils.html_utils import sanitize_html


def render(text):
	"""
	Render Markdown to sanitised HTML.

	Parameters:
		text (str, optional): Markdown source.

	Returns:
		str: Safe HTML ("" for empty input).
	"""
	if not text:
		return ""
	return sanitize_html(frappe.utils.md_to_html(text), linkify=True)


def excerpt(text, length=220):
	"""
	Plain-text excerpt of Markdown for cards and search results.

	Parameters:
		text (str, optional): Markdown source.
		length (int, optional): Maximum characters.

	Returns:
		str: Plain text, cut on a word boundary.
	"""
	plain = frappe.utils.strip_html(render(text or "")).replace("\n", " ").strip()
	return plain if len(plain) <= length else plain[:length].rsplit(" ", 1)[0] + "…"
