# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Background and scheduled AI jobs."""


def draft_forum_answer(question):
	"""
	Write the AI draft answer for a new question.

	Parameters:
		question (str, required): Question name.

	Returns:
		None
	"""
	from stackpilot.sp_ai.utils.features import draft_forum_answer as draft

	draft(question)


def reset_monthly_spend():
	"""
	Monthly scheduler: reset the AI spend counter.

	Returns:
		None
	"""
	from stackpilot.sp_ai.utils.gateway import reset_month

	reset_month()
