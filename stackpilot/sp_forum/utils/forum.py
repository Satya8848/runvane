# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Forum rules: asking, answering, voting (one vote per member), accepting
an answer, and the counters and reputation they change."""

import frappe
from frappe import _

from stackpilot.sp_core.utils.members import add_reputation, ensure_profile
from stackpilot.utils.markdown import render

VOTABLE = ("Question", "Answer", "Architecture Diagram")
MIN_TITLE, MAX_BODY = 12, 30000


def require_member():
	"""
	Allow only signed-in members.

	Returns:
		str: The user id.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Sign in to do this."), frappe.PermissionError)
	ensure_profile(frappe.session.user)
	return frappe.session.user


def ask(title, body, role_track=None, tags=None):
	"""
	Create a question.

	Parameters:
		title (str, required): Question title.
		body (str, required): Markdown body.
		role_track (str, optional): Role Track slug.
		tags (str, optional): Comma-separated tags.

	Returns:
		str: Question name.
	"""
	require_member()
	title = (title or "").strip()
	if len(title) < MIN_TITLE or not looks_like_words(title):
		frappe.throw(_("Write a clear title of at least {0} characters and 3 words that says what is wrong.").format(MIN_TITLE))
	_check_body(body)
	doc = frappe.get_doc({"doctype": "Question", "title": title[:140], "body": body, "role_track": role_track or None,
		"tags": _clean_tags(tags), "status": "Open"}).insert(ignore_permissions=True)
	return doc.name


def answer(question, body, is_ai=False, provider=None):
	"""
	Add an answer and update the question's counters.

	Parameters:
		question (str, required): Question name.
		body (str, required): Markdown answer.
		is_ai (bool, optional): True for an AI draft.
		provider (str, optional): AI provider of a draft.

	Returns:
		str: Answer name.
	"""
	if not is_ai:
		require_member()
	_check_body(body)
	if frappe.db.get_value("Question", question, "status") == "Closed":
		frappe.throw(_("This question is closed."))
	doc = frappe.get_doc({"doctype": "Answer", "question": question, "body": body, "is_ai": 1 if is_ai else 0, "ai_provider": provider}).insert(ignore_permissions=True)
	frappe.db.set_value("Question", question, "answer_count", frappe.db.count("Answer", {"question": question}), update_modified=False)
	return doc.name


def vote(doctype, name, value):
	"""
	Set the member's vote (+1, -1 or 0 to remove) and recount.

	Parameters:
		doctype (str, required): Question, Answer or Architecture Diagram.
		name (str, required): Record name.
		value (int, required): 1, -1 or 0.

	Returns:
		int: New total.
	"""
	user = require_member()
	if doctype not in VOTABLE or int(value) not in (-1, 0, 1):
		frappe.throw(_("Invalid vote."))
	owner = frappe.db.get_value(doctype, name, "owner")
	if owner == user:
		frappe.throw(_("You cannot vote on your own post."))
	existing = frappe.db.get_value("Vote", {"user": user, "reference_doctype": doctype, "reference_name": name}, ["name", "value"], as_dict=True)
	if existing:
		frappe.delete_doc("Vote", existing.name, ignore_permissions=True)
	if int(value):
		frappe.get_doc({"doctype": "Vote", "user": user, "reference_doctype": doctype, "reference_name": name, "value": int(value)}).insert(ignore_permissions=True)
		if not existing or existing.value != int(value):
			key = "downvoted" if int(value) < 0 else ("answer_upvoted" if doctype == "Answer" else "question_upvoted")
			add_reputation(owner, key, doctype, name)
	total = frappe.db.sql("select coalesce(sum(value), 0) from `tabVote` where reference_doctype=%s and reference_name=%s", (doctype, name))[0][0]
	frappe.db.set_value(doctype, name, "votes", int(total), update_modified=False)
	return int(total)


def accept(answer_name):
	"""
	Mark an answer as the accepted one (question owner or moderator only).

	Parameters:
		answer_name (str, required): Answer name.

	Returns:
		None
	"""
	user = require_member()
	ans = frappe.get_doc("Answer", answer_name)
	question = frappe.get_doc("Question", ans.question)
	if question.owner != user and not ({"SP Moderator", "System Manager"} & set(frappe.get_roles())):
		frappe.throw(_("Only the person who asked can accept an answer."), frappe.PermissionError)
	frappe.db.set_value("Answer", {"question": question.name, "is_accepted": 1}, "is_accepted", 0, update_modified=False)
	frappe.db.set_value("Answer", answer_name, "is_accepted", 1, update_modified=False)
	frappe.db.set_value("Question", question.name, {"accepted_answer": answer_name, "status": "Answered"}, update_modified=False)
	if not ans.is_ai:
		add_reputation(ans.owner, "answer_accepted", "Answer", answer_name)


def question_detail(name):
	"""
	A question with rendered body, answers (accepted first, then votes) and comments.

	Parameters:
		name (str, required): Question name.

	Returns:
		dict: Question, answers, comments and the viewer's votes.
	"""
	q = frappe.get_doc("Question", name)
	frappe.db.set_value("Question", name, "views", (q.views or 0) + 1, update_modified=False)
	answers = frappe.get_all("Answer", filters={"question": name}, fields=["name", "owner", "body", "votes", "is_accepted", "is_ai", "ai_provider", "creation"],
		order_by="is_accepted desc, votes desc, creation asc", ignore_permissions=True)
	names = {name: "Question", **{a.name: "Answer" for a in answers}}
	comments = frappe.get_all("SP Comment", filters={"reference_name": ["in", list(names)]}, fields=["name", "owner", "reference_name", "body", "creation"], order_by="creation asc", ignore_permissions=True)
	authors = _authors([q.owner] + [a.owner for a in answers] + [c.owner for c in comments])
	my_votes = {}
	if frappe.session.user != "Guest":
		my_votes = dict(frappe.get_all("Vote", filters={"user": frappe.session.user, "reference_name": ["in", list(names)]}, fields=["reference_name", "value"], as_list=True))
	for a in answers:
		a["html"] = render(a.pop("body"))
		a["author"] = authors.get(a.owner)
	for c in comments:
		c["html"] = render(c.pop("body"))
		c["author"] = authors.get(c.owner)
	return {
		"question": {"name": q.name, "title": q.title, "html": render(q.body), "role_track": q.role_track, "status": q.status, "votes": q.votes, "views": (q.views or 0) + 1,
			"tags": [t for t in (q.tags or "").split(",") if t], "creation": q.creation, "owner": q.owner, "author": authors.get(q.owner), "ai_draft_status": q.ai_draft_status},
		"answers": answers, "comments": comments, "my_votes": my_votes, "is_owner": frappe.session.user == q.owner,
	}


def looks_like_words(text):
	"""
	Reject keyboard-mash titles: needs 3+ words and a normal share of vowels.

	Parameters:
		text (str, required): Title.

	Returns:
		bool: True when it reads like a sentence.
	"""
	words = [w for w in text.split() if any(c.isalpha() for c in w)]
	letters = [c for c in text.lower() if c.isalpha()]
	vowels = sum(c in "aeiouy" for c in letters)
	return len(words) >= 3 and bool(letters) and 0.2 <= vowels / len(letters) <= 0.7


def _authors(users):
	"""
	Display names and reputation for a set of users.

	Parameters:
		users (list[str], required): User ids.

	Returns:
		dict: {user: {"name", "reputation"}}
	"""
	rows = frappe.get_all("SP Profile", filters={"user": ["in", list(set(users))]}, fields=["user", "display_name", "reputation"], ignore_permissions=True)
	return {r.user: {"name": r.display_name or r.user.split("@")[0], "reputation": r.reputation or 0} for r in rows}


def _check_body(body):
	"""
	Validate a Markdown body's length.

	Parameters:
		body (str, required): Markdown.

	Returns:
		None
	"""
	if len((body or "").strip()) < 20:
		frappe.throw(_("Add more detail: what you tried, what you expected, what happened (at least 20 characters)."))
	if len(body) > MAX_BODY:
		frappe.throw(_("That is too long ({0} characters max).").format(MAX_BODY))


def _clean_tags(tags):
	"""
	Normalise a comma-separated tag string (lower case, max 5).

	Parameters:
		tags (str | list, optional): Tags.

	Returns:
		str: Clean comma-separated tags.
	"""
	if isinstance(tags, list):
		tags = ",".join(tags)
	items = [t.strip().lower().replace(" ", "-")[:30] for t in (tags or "").split(",") if t.strip()]
	return ",".join(list(dict.fromkeys(items))[:5])
