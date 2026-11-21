# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Mask secrets in text before it is stored or sent to any AI provider."""

import re

# (label, pattern). Order matters: specific patterns first.
PATTERNS = [
	("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----")),
	("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
	("AWS secret key", re.compile(r"(?i)(aws_secret_access_key|secret_access_key)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}")),
	("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
	("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
	("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
	("Stripe key", re.compile(r"\b(sk|rk)_(live|test)_[0-9A-Za-z]{16,}\b")),
	("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")),
	("OpenAI/Groq key", re.compile(r"\b(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,})\b")),
	("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
	("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}")),
	("URL credentials", re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://)([^\s:/@]+):([^\s@/]+)@")),
	("password/secret value", re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b(\s*[:=]\s*)(['\"]?)([^\s'\";,]{4,})")),
]


def mask(text):
	"""
	Replace secrets with [MASKED:<label>] and report what was masked.

	Parameters:
		text (str, required): Text the user pasted.

	Returns:
		tuple[str, list[str]]: (masked text, labels of what was masked, one per hit)
	"""
	found = []
	for label, pattern in PATTERNS:
		def repl(match, label=label):
			found.append(label)
			if label == "URL credentials":
				return f"{match.group(1)}[MASKED]:[MASKED]@"
			if label == "password/secret value":
				return f"{match.group(1)}{match.group(2)}{match.group(3)}[MASKED:{label}]"
			return f"[MASKED:{label}]"
		text = pattern.sub(repl, text or "")
	return text, found
