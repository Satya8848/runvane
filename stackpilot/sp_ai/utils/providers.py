# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""One call shape for every AI provider: complete(provider, key, model,
system, messages) -> text and token counts. Claude, Gemini, Groq and OpenAI."""

import frappe
import requests
from frappe import _

TIMEOUT = 90
# Approximate list prices in USD per 1M tokens (input, output), for the spend cap only.
PRICES = {"claude": (3.0, 15.0), "gemini": (0.30, 2.50), "groq": (0.59, 0.79), "openai": (0.40, 1.60)}


class ProviderError(frappe.ValidationError):
	"""Raised when a provider refuses or fails a call."""


def complete(provider, api_key, model, system, messages, max_tokens=1800):
	"""
	Run one chat completion.

	Parameters:
		provider (str, required): claude, gemini, groq or openai.
		api_key (str, required): Provider API key.
		model (str, required): Model id.
		system (str, required): System prompt.
		messages (list[dict], required): [{"role": "user"|"assistant", "content": str}]
		max_tokens (int, optional): Output limit.

	Returns:
		dict: {"text": str, "tokens_in": int, "tokens_out": int}
	"""
	handler = {"claude": _claude, "gemini": _gemini, "groq": _openai_style, "openai": _openai_style}.get(provider)
	if not handler:
		raise ProviderError(_("Unknown AI provider {0}").format(provider))
	try:
		return handler(provider, api_key, model, system, messages, max_tokens)
	except requests.RequestException as exc:
		raise ProviderError(_("{0} is not reachable: {1}").format(provider, exc)) from exc


def cost(provider, tokens_in, tokens_out):
	"""
	Approximate USD cost of a call.

	Parameters:
		provider (str, required): Provider.
		tokens_in (int, required): Input tokens.
		tokens_out (int, required): Output tokens.

	Returns:
		float: USD.
	"""
	price_in, price_out = PRICES.get(provider, (0, 0))
	return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 6)


def _check(response, provider):
	"""
	Raise a readable error for a failed provider response.

	Parameters:
		response (requests.Response, required): Response.
		provider (str, required): Provider name.

	Returns:
		dict: Parsed JSON.
	"""
	if response.status_code >= 400:
		detail = response.text[:300]
		raise ProviderError(_("{0} answered {1}: {2}").format(provider, response.status_code, detail))
	return response.json()


def _claude(provider, api_key, model, system, messages, max_tokens):
	"""Anthropic Messages API. Returns: dict."""
	data = _check(requests.post("https://api.anthropic.com/v1/messages", timeout=TIMEOUT, headers={
		"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
		json={"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}), provider)
	text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
	usage = data.get("usage", {})
	return {"text": text, "tokens_in": usage.get("input_tokens", 0), "tokens_out": usage.get("output_tokens", 0)}


def _gemini(provider, api_key, model, system, messages, max_tokens):
	"""Google Gemini generateContent API. Returns: dict."""
	contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages]
	data = _check(requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", timeout=TIMEOUT,
		headers={"x-goog-api-key": api_key}, json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
		"generationConfig": {"maxOutputTokens": max_tokens}}), provider)
	parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
	usage = data.get("usageMetadata", {})
	return {"text": "".join(p.get("text", "") for p in parts), "tokens_in": usage.get("promptTokenCount", 0), "tokens_out": usage.get("candidatesTokenCount", 0)}


def _openai_style(provider, api_key, model, system, messages, max_tokens):
	"""OpenAI-compatible chat completions (OpenAI and Groq). Returns: dict."""
	base = "https://api.groq.com/openai/v1" if provider == "groq" else "https://api.openai.com/v1"
	data = _check(requests.post(f"{base}/chat/completions", timeout=TIMEOUT, headers={"Authorization": f"Bearer {api_key}"},
		json={"model": model, "max_tokens": max_tokens, "messages": [{"role": "system", "content": system}, *messages]}), provider)
	usage = data.get("usage", {})
	return {"text": data["choices"][0]["message"]["content"], "tokens_in": usage.get("prompt_tokens", 0), "tokens_out": usage.get("completion_tokens", 0)}
