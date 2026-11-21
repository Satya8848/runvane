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


def is_moderator():
	"""
	Whether the session user can manage anyone's posts.

	Returns:
		bool: True for SP Moderator or System Manager.
	"""
	return bool({"SP Moderator", "System Manager"} & set(frappe.get_roles()))


def require_owner_or_moderator(doctype, name):
	"""
	Load a post and allow only its author or a moderator.

	Parameters:
		doctype (str, required): Question, Answer or SP Comment.
		name (str, required): Record name.

	Returns:
		Document: The post.
	"""
	user = require_member()
	doc = frappe.get_doc(doctype, name)
	if doc.owner != user and not is_moderator():
		frappe.throw(_("You can only change your own posts."), frappe.PermissionError)
	return doc


def edit_question(name, title=None, body=None, tags=None, role_track=None):
	"""
	Edit a question (author or moderator).

	Parameters:
		name (str, required): Question.
		title, body, tags, role_track (str, optional): New values.

	Returns:
		None
	"""
	doc = require_owner_or_moderator("Question", name)
	if title is not None:
		title = title.strip()
		if len(title) < MIN_TITLE or not looks_like_words(title):
			frappe.throw(_("Write a clear title of at least {0} characters and 3 words.").format(MIN_TITLE))
		doc.title = title[:140]
	if body is not None:
		_check_body(body)
		doc.body = body
	if tags is not None:
		doc.tags = _clean_tags(tags)
	if role_track is not None:
		doc.role_track = role_track or None
	doc.save(ignore_permissions=True)


def set_question_status(name, status):
	"""
	Close or reopen a question (author or moderator).

	Parameters:
		name (str, required): Question.
		status (str, required): Open or Closed.

	Returns:
		str: New status.
	"""
	doc = require_owner_or_moderator("Question", name)
	if status not in ("Open", "Closed"):
		frappe.throw(_("Status must be Open or Closed."))
	new = "Answered" if status == "Open" and doc.accepted_answer else status
	frappe.db.set_value("Question", name, "status", new, update_modified=False)
	return new


def delete_question(name):
	"""
	Delete a question with its answers, comments, votes and reports.
	Authors can delete only while no one else has answered; moderators always.

	Parameters:
		name (str, required): Question.

	Returns:
		None
	"""
	doc = require_owner_or_moderator("Question", name)
	others = frappe.db.count("Answer", {"question": name, "is_ai": 0, "owner": ["!=", doc.owner]})
	if others and not is_moderator():
		frappe.throw(_("Others have answered this question, so it can't be deleted. Close it instead."))
	answers = frappe.get_all("Answer", filters={"question": name}, pluck="name", ignore_permissions=True)
	for ref in [name, *answers]:
		for doctype in ("Vote", "SP Comment", "Report", "Bookmark"):
			frappe.db.delete(doctype, {"reference_name": ref})
	frappe.db.delete("Answer", {"question": name})
	frappe.delete_doc("Question", name, ignore_permissions=True)


def edit_answer(name, body):
	"""
	Edit an answer (author or moderator).

	Parameters:
		name (str, required): Answer.
		body (str, required): New Markdown.

	Returns:
		None
	"""
	doc = require_owner_or_moderator("Answer", name)
	_check_body(body)
	doc.body = body
	doc.save(ignore_permissions=True)


def delete_answer(name):
	"""
	Delete an answer (author or moderator); clears the accepted mark if needed.

	Parameters:
		name (str, required): Answer.

	Returns:
		None
	"""
	doc = require_owner_or_moderator("Answer", name)
	question = doc.question
	for doctype in ("Vote", "SP Comment", "Report"):
		frappe.db.delete(doctype, {"reference_name": name})
	frappe.delete_doc("Answer", name, ignore_permissions=True)
	values = {"answer_count": frappe.db.count("Answer", {"question": question})}
	if frappe.db.get_value("Question", question, "accepted_answer") == name:
		values.update({"accepted_answer": None, "status": "Open"})
	frappe.db.set_value("Question", question, values, update_modified=False)


def delete_comment(name):
	"""
	Delete a comment (author or moderator).

	Parameters:
		name (str, required): SP Comment.

	Returns:
		None
	"""
	require_owner_or_moderator("SP Comment", name)
	frappe.delete_doc("SP Comment", name, ignore_permissions=True)


def _edited(row):
	"""
	Whether a post was edited after it was created (more than a minute later).

	Parameters:
		row (dict | Document, required): Post with creation and modified.

	Returns:
		bool: Edited.
	"""
	return bool(row.get("modified") and row.get("creation") and (row["modified"] - row["creation"]).total_seconds() > 60)


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
	answers = frappe.get_all("Answer", filters={"question": name}, fields=["name", "owner", "body", "votes", "is_accepted", "is_ai", "ai_provider", "creation", "modified"],
		order_by="is_accepted desc, votes desc, creation asc", ignore_permissions=True)
	names = {name: "Question", **{a.name: "Answer" for a in answers}}
	comments = frappe.get_all("SP Comment", filters={"reference_name": ["in", list(names)]}, fields=["name", "owner", "reference_name", "body", "creation"], order_by="creation asc", ignore_permissions=True)
	authors = _authors([q.owner] + [a.owner for a in answers] + [c.owner for c in comments])
	my_votes = {}
	if frappe.session.user != "Guest":
		my_votes = dict(frappe.get_all("Vote", filters={"user": frappe.session.user, "reference_name": ["in", list(names)]}, fields=["reference_name", "value"], as_list=True))
	me, mod = frappe.session.user, is_moderator()
	for a in answers:
		a["markdown"] = a.pop("body")
		a["html"] = render(a["markdown"])
		a["author"] = authors.get(a.owner)
		a["can_edit"] = (a.owner == me and not a.is_ai) or mod
		a["edited"] = _edited(a)
	for c in comments:
		c["html"] = render(c.pop("body"))
		c["author"] = authors.get(c.owner)
		c["can_delete"] = c.owner == me or mod
	return {
		"question": {"name": q.name, "title": q.title, "html": render(q.body), "role_track": q.role_track, "status": q.status, "votes": q.votes, "views": (q.views or 0) + 1,
			"tags": [t for t in (q.tags or "").split(",") if t], "creation": q.creation, "owner": q.owner, "author": authors.get(q.owner), "ai_draft_status": q.ai_draft_status,
			"markdown": q.body, "edited": _edited(q.as_dict())},
		"answers": answers, "comments": comments, "my_votes": my_votes, "is_owner": frappe.session.user == q.owner,
		"can_manage": frappe.session.user == q.owner or is_moderator(),
		"others_answered": any(a.owner != q.owner and not a.is_ai for a in answers),
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
