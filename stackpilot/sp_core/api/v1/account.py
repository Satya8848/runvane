# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Account endpoints: sign up with a password and start a session at once
(no email round-trip), and update the public profile."""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import validate_email_address
from frappe.utils.password_strength import test_password_strength

from stackpilot.sp_core.utils.members import ensure_profile


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def signup(full_name, email, password, role_track=None):
	"""
	Create a member account and sign in.

	**Endpoint:** `/api/method/stackpilot.sp_core.api.v1.account.signup`
	**HTTP Method:** POST
	**Parameters:**
		- full_name (str, required): Display name (2–60 characters).
		- email (str, required): Email address (login id).
		- password (str, required): At least 10 characters and not easily guessed.
		- role_track (str, optional): Role Track slug for the profile.
	**Response:**
	```json
	{"message": {"ok": true, "user": "you@example.com"}}
	```
	"""
	full_name = (full_name or "").strip()
	email = (email or "").strip().lower()
	if not 2 <= len(full_name) <= 60:
		frappe.throw(_("Enter your name (2 to 60 characters)."))
	if not validate_email_address(email):
		frappe.throw(_("Enter a valid email address."))
	if frappe.db.exists("User", email):
		frappe.throw(_("An account with this email already exists. Sign in instead."))
	if len(password or "") < 10 or test_password_strength(password, user_inputs=(full_name, email)).get("score", 0) < 2:
		frappe.throw(_("Choose a stronger password: at least 10 characters, not a common word or your name."))

	user = frappe.get_doc({"doctype": "User", "email": email, "first_name": full_name, "user_type": "Website User", "enabled": 1,
		"send_welcome_email": 0, "new_password": password})
	user.flags.ignore_password_policy = True
	user.insert(ignore_permissions=True)
	ensure_profile(email)
	if role_track and frappe.db.exists("Role Track", role_track):
		frappe.db.set_value("SP Profile", email, "role_track", role_track)
	frappe.local.login_manager.login_as(email)
	return {"ok": True, "user": email}


@frappe.whitelist(methods=["POST"])
def update_profile(display_name=None, headline=None, role_track=None, bio=None, github=None, website=None, location=None):
	"""
	Update the signed-in member's public profile.

	**Endpoint:** `/api/method/stackpilot.sp_core.api.v1.account.update_profile`
	**HTTP Method:** POST
	**Parameters:**
		- display_name, headline, role_track, bio, github, website, location (str, optional): New values.
	**Response:**
	```json
	{"message": {"ok": true}}
	```
	"""
	user = frappe.session.user
	if user == "Guest":
		raise frappe.PermissionError
	ensure_profile(user)
	values = {k: (v or "").strip()[:500] for k, v in dict(display_name=display_name, headline=headline, role_track=role_track,
		bio=bio, github=github, website=website, location=location).items() if v is not None}
	if values.get("role_track") and not frappe.db.exists("Role Track", values["role_track"]):
		values.pop("role_track")
	frappe.db.set_value("SP Profile", user, values)
	return {"ok": True}


@frappe.whitelist(methods=["GET"])
def me():
	"""
	The signed-in member's profile, badges and own activity, for the My account page.

	**Endpoint:** `/api/method/stackpilot.sp_core.api.v1.account.me`
	**HTTP Method:** GET
	**Parameters:** none
	**Response:**
	```json
	{"message": {"profile": {"display_name": "...", "reputation": 25, ...}, "email": "...", "badges": [], "counts": {"questions": 2, "answers": 5, "boards": 1, "accepted": 1},
	             "questions": [...], "answers": [...], "boards": [...]}}
	```
	"""
	user = frappe.session.user
	if user == "Guest":
		raise frappe.PermissionError
	ensure_profile(user)
	profile = frappe.db.get_value("SP Profile", user, ["display_name", "headline", "role_track", "reputation", "location", "github", "website", "bio"], as_dict=True)
	questions = frappe.get_all("Question", filters={"owner": user}, fields=["name", "title", "status", "votes", "answer_count", "creation"], order_by="creation desc", limit=50, ignore_permissions=True)
	answers = frappe.get_all("Answer", filters={"owner": user, "is_ai": 0}, fields=["name", "question", "votes", "is_accepted", "creation"], order_by="creation desc", limit=50, ignore_permissions=True)
	titles = dict(frappe.get_all("Question", filters={"name": ["in", [a.question for a in answers]]}, fields=["name", "title"], as_list=True, ignore_permissions=True)) if answers else {}
	for answer in answers:
		answer["question_title"] = titles.get(answer.question)
	boards = frappe.get_all("Architecture Diagram", filters={"owner": user}, fields=["name", "title", "visibility", "votes", "modified"], order_by="modified desc", limit=50, ignore_permissions=True)
	badges = frappe.get_all("User Badge", filters={"user": user}, pluck="badge", ignore_permissions=True)
	return {
		"email": user, "profile": profile, "badges": badges, "questions": questions, "answers": answers, "boards": boards,
		"counts": {"questions": len(questions), "answers": len(answers), "boards": len(boards), "accepted": sum(1 for a in answers if a.is_accepted)},
	}
