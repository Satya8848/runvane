# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Every AI call goes through here: pick provider and key (member's own key
first), enforce the daily quota and the monthly spend cap, call the
provider, and log tokens and cost."""

import frappe
from frappe import _
from frappe.query_builder.functions import Sum

from stackpilot.sp_ai.utils import providers

FEATURE_ROUTE = {"chat": "chat_provider", "analyse": "analyse_provider", "forum": "forum_draft_provider",
	"diagram": "diagram_provider", "builder": "builder_provider", "explain": "analyse_provider", "challenge": "analyse_provider"}


class AIUnavailable(frappe.ValidationError):
	"""Raised when no AI provider can be used for this call."""


def run(feature, system, messages, user=None, max_tokens=1800):
	"""
	Run one AI call for a feature, with routing, limits and usage logging.

	Parameters:
		feature (str, required): chat, analyse, forum, diagram, builder, explain or challenge.
		system (str, required): System prompt.
		messages (list[dict], required): Conversation messages.
		user (str, optional): Member (default: session user; None for system jobs).
		max_tokens (int, optional): Output limit.

	Returns:
		dict: {"text", "provider", "model", "tokens_in", "tokens_out", "byok"}
	"""
	settings = frappe.get_cached_doc("AI Settings")
	if not settings.ai_enabled:
		raise AIUnavailable(_("AI is turned off on this site."))
	user = user if user is not None else frappe.session.user
	provider, key, model, byok = _choose(settings, feature, user)
	if not byok:
		_check_limits(settings, user, feature)
	result = providers.complete(provider, key, model, system, messages, max_tokens=max_tokens)
	_log(settings, user, feature, provider, model, result, byok)
	return {**result, "provider": provider, "model": model, "byok": byok}


def status(user):
	"""
	What AI the member can use right now, for the UI.

	Parameters:
		user (str, required): Member.

	Returns:
		dict: {"enabled", "available", "site_keys", "own_keys", "used_today", "quota", "budget_reached", "guest", "guest_left"}
	"""
	settings = frappe.get_cached_doc("AI Settings")
	site_keys = [p for p in ("claude", "gemini", "groq", "openai") if settings.get_password(f"{_field(p)}_api_key", raise_exception=False)]
	own = frappe.get_all("AI Provider Key", filters={"user": user}, pluck="provider", ignore_permissions=True) if user != "Guest" else []
	guest = user == "Guest"
	return {"enabled": bool(settings.ai_enabled), "available": bool(settings.ai_enabled and (site_keys or own) and not (settings.byok_only and not own)),
		"site_keys": site_keys, "own_keys": own, "used_today": _used_today(user), "quota": settings.daily_token_quota,
		"budget_reached": bool(settings.byok_only), "guest": guest,
		"guest_left": max(int(settings.guest_daily_requests or 0) - guest_requests_today(), 0) if guest else None}


def _choose(settings, feature, user):
	"""
	Pick provider, key and model: the member's own key for the routed
	provider, then any own key, then the site key (unless the budget is spent).

	Parameters:
		settings (Document, required): AI Settings.
		feature (str, required): Feature.
		user (str, required): Member.

	Returns:
		tuple[str, str, str, bool]: (provider, key, model, byok)
	"""
	preferred = settings.get(FEATURE_ROUTE.get(feature, "chat_provider")) or "claude"
	if user and user != "Guest":
		own = frappe.get_all("AI Provider Key", filters={"user": user}, fields=["name", "provider", "model"], ignore_permissions=True)
		own.sort(key=lambda row: row.provider != preferred)
		for row in own:
			key = frappe.get_doc("AI Provider Key", row.name).get_password("api_key", raise_exception=False)
			if key:
				return row.provider, key, row.model or settings.get(f"{_field(row.provider)}_model"), True
	if settings.byok_only:
		raise AIUnavailable(_("The site's monthly AI budget is used up. Add your own API key in AI settings to keep going."))
	for provider in [preferred, "claude", "gemini", "groq", "openai"]:
		key = settings.get_password(f"{_field(provider)}_api_key", raise_exception=False)
		if key:
			return provider, key, settings.get(f"{_field(provider)}_model"), False
	raise AIUnavailable(_("No AI provider is configured yet. Add your own key in AI settings."))


def _check_limits(settings, user, feature):
	"""
	Enforce the visitor per-IP limit and the per-member daily quota.
	System jobs (user None, e.g. forum drafts) are only bound by the monthly budget.

	Parameters:
		settings (Document, required): AI Settings.
		user (str, optional): Member, "Guest" for visitors, None for system jobs.
		feature (str, required): Feature being used.

	Returns:
		None
	"""
	if user is None:
		return
	if user == "Guest":
		allowed = int(settings.guest_daily_requests or 0)
		if not allowed:
			raise AIUnavailable(_("Join free to use the AI assistant."))
		if guest_requests_today() >= allowed:
			raise AIUnavailable(_("You used today's {0} free AI questions. Join free (10 seconds) for more, or come back tomorrow.").format(allowed))
		return
	if settings.daily_token_quota and _used_today(user) >= settings.daily_token_quota:
		raise AIUnavailable(_("You reached today's AI limit. It resets at midnight UTC, or add your own API key."))


def guest_requests_today():
	"""
	AI requests made today from the visitor's IP without an account.

	Returns:
		int: Request count.
	"""
	return frappe.db.count("AI Usage", {"user": ["is", "not set"], "ip": frappe.local.request_ip, "creation": [">=", frappe.utils.today()]})


def _used_today(user):
	"""
	Tokens a member used today on site keys.

	Parameters:
		user (str, required): Member.

	Returns:
		int: Tokens.
	"""
	if not user or user == "Guest":
		return 0
	usage = frappe.qb.DocType("AI Usage")
	row = (frappe.qb.from_(usage).select(Sum(usage.tokens_in), Sum(usage.tokens_out))
		.where((usage.user == user) & (usage.byok == 0) & (usage.creation >= frappe.utils.today())).run())
	return int((row[0][0] or 0) + (row[0][1] or 0)) if row else 0


def _log(settings, user, feature, provider, model, result, byok):
	"""
	Record usage and update the month's spend; pause site keys at the cap.

	Parameters:
		settings (Document, required): AI Settings.
		user (str, optional): Member.
		feature (str, required): Feature.
		provider (str, required): Provider.
		model (str, required): Model.
		result (dict, required): Provider result.
		byok (bool, required): Member's own key.

	Returns:
		None
	"""
	usd = 0 if byok else providers.cost(provider, result["tokens_in"], result["tokens_out"])
	frappe.get_doc({"doctype": "AI Usage", "user": user if user and user != "Guest" else None, "feature": feature, "provider": provider, "model": model,
		"tokens_in": result["tokens_in"], "tokens_out": result["tokens_out"], "cost_usd": usd, "byok": 1 if byok else 0,
		"ip": getattr(frappe.local, "request_ip", None) if user == "Guest" else None}).insert(ignore_permissions=True)
	if usd:
		spend = (frappe.db.get_single_value("AI Settings", "month_spend_usd") or 0) + usd
		values = {"month_spend_usd": spend}
		if settings.monthly_budget_usd and spend >= settings.monthly_budget_usd:
			values["byok_only"] = 1
		frappe.db.set_single_value("AI Settings", values)
		frappe.clear_document_cache("AI Settings", "AI Settings")


def reset_month():
	"""
	Scheduler (monthly): reset the spend counter and re-enable site keys.

	Returns:
		None
	"""
	frappe.db.set_single_value("AI Settings", {"month_spend_usd": 0, "byok_only": 0})
	frappe.clear_document_cache("AI Settings", "AI Settings")


def _field(provider):
	"""
	AI Settings field prefix for a provider.

	Parameters:
		provider (str, required): Provider.

	Returns:
		str: Field prefix.
	"""
	return "anthropic" if provider == "claude" else provider
