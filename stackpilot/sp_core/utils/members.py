# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Members: give every new website user the SP Member role and a profile,
and keep reputation in one place."""

import frappe

ROLES = ("SP Member", "SP Moderator", "SP Editor")
POINTS = {"answer_accepted": 15, "answer_upvoted": 10, "question_upvoted": 5, "downvoted": -2, "playbook_helpful": 2}


def on_user_insert(doc, method=None):
	"""
	User after_insert hook: add the member role and create the public profile.

	Parameters:
		doc (Document, required): New User.
		method (str, optional): Hook name.

	Returns:
		None
	"""
	if doc.name in ("Administrator", "Guest"):
		return
	if "SP Member" not in [r.role for r in doc.roles]:
		doc.add_roles("SP Member")
	ensure_profile(doc.name)


def ensure_profile(user):
	"""
	Create the member's profile if missing.

	Parameters:
		user (str, required): User id.

	Returns:
		str: Profile name.
	"""
	if not frappe.db.exists("SP Profile", user):
		frappe.get_doc({"doctype": "SP Profile", "user": user, "display_name": frappe.db.get_value("User", user, "full_name") or user.split("@")[0]}).insert(ignore_permissions=True)
	return user


def add_reputation(user, key, reference_doctype=None, reference_name=None):
	"""
	Record a reputation change and update the profile total.

	Parameters:
		user (str, required): Who gets the points.
		key (str, required): Key of POINTS.
		reference_doctype (str, optional): Why: the doctype.
		reference_name (str, optional): Why: the record.

	Returns:
		None
	"""
	if not user or user in ("Administrator", "Guest"):
		return
	ensure_profile(user)
	points = POINTS[key]
	frappe.get_doc({"doctype": "Reputation Event", "user": user, "points": points, "reason": key,
		"reference_doctype": reference_doctype, "reference_name": reference_name}).insert(ignore_permissions=True)
	frappe.db.set_value("SP Profile", user, "reputation", (frappe.db.get_value("SP Profile", user, "reputation") or 0) + points, update_modified=False)


def create_roles():
	"""
	Create the platform roles (no Desk access for members).

	Returns:
		None
	"""
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 0 if role == "SP Member" else 1}).insert(ignore_permissions=True)
