# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Tests: secret masking, search document ids, forum rules and AI routing limits."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from stackpilot.sp_ai.utils import gateway
from stackpilot.sp_ai.utils.masking import mask
from stackpilot.sp_forum.utils import forum
from stackpilot.utils.search import document_for


class TestMasking(UnitTestCase):
	"""Secrets never leave the server."""

	def test_masks_common_secrets(self):
		"""Keys, tokens, passwords and URL credentials are masked; normal text is kept."""
		text = ("password=Hunter2Secret AKIAABCDEFGHIJKLMNOP ghp_abcdefghijklmnopqrstuvwxyz0123456789 "
			"postgres://admin:pw123@db/app normal 502 line")
		out, found = mask(text)
		for secret in ("Hunter2Secret", "AKIAABCDEFGHIJKLMNOP", "ghp_abcdef", "pw123"):
			self.assertNotIn(secret, out)
		self.assertIn("normal 502 line", out)
		self.assertEqual(len(found), 4)

	def test_private_key_block(self):
		"""A whole private key block is replaced."""
		out, found = mask("-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----")
		self.assertEqual(out, "[MASKED:private key]")
		self.assertEqual(found, ["private key"])


class TestSearchIds(IntegrationTestCase):
	"""Search document ids are always valid for Meilisearch."""

	def test_id_is_safe(self):
		"""Names with quotes, slashes and spaces produce a safe id."""
		doc = frappe._dict(doctype="SP Term", name="Let's Encrypt / CI/CD", term="Let's Encrypt / CI/CD", short_definition="x", explanation="y")
		self.assertRegex(document_for(doc)["id"], r"^[A-Za-z0-9_-]+$")


class TestForum(IntegrationTestCase):
	"""Asking, answering, voting and accepting."""

	def setUp(self):
		"""Two members."""
		for email in ("sp-asker@example.com", "sp-helper@example.com"):
			if not frappe.db.exists("User", email):
				frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0], "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)

	def tearDown(self):
		"""Back to Administrator."""
		frappe.set_user("Administrator")

	def test_flow_and_rules(self):
		"""Only the asker accepts; no self-votes; reputation is awarded."""
		frappe.set_user("sp-asker@example.com")
		question = forum.ask("Disk full but du shows much less space used", "df says 100% but du only adds up to 40%. What is going on here?")
		frappe.set_user("sp-helper@example.com")
		answer = forum.answer(question, "A deleted log file is still open. Use lsof +L1 and restart the process.")
		with self.assertRaises(frappe.ValidationError):
			forum.vote("Answer", answer, 1)
		with self.assertRaises(frappe.PermissionError):
			forum.accept(answer)
		frappe.set_user("sp-asker@example.com")
		self.assertEqual(forum.vote("Answer", answer, 1), 1)
		forum.accept(answer)
		self.assertEqual(frappe.db.get_value("Question", question, "status"), "Answered")
		self.assertEqual(frappe.db.get_value("SP Profile", "sp-helper@example.com", "reputation"), 25)

	def test_short_title_rejected(self):
		"""A vague title is refused."""
		frappe.set_user("sp-asker@example.com")
		with self.assertRaises(frappe.ValidationError):
			forum.ask("help", "x" * 40)


class TestAIGateway(IntegrationTestCase):
	"""Provider routing, own keys and the budget cap."""

	def test_no_keys_means_unavailable(self):
		"""Without any key the gateway refuses clearly."""
		settings = frappe.get_single("AI Settings")
		settings.ai_enabled = 1
		for provider in ("anthropic", "gemini", "groq", "openai"):
			settings.set(f"{provider}_api_key", "")
		settings.save()
		frappe.clear_document_cache("AI Settings", "AI Settings")
		frappe.set_user("Administrator")
		with self.assertRaises(gateway.AIUnavailable):
			gateway.run("chat", "system", [{"role": "user", "content": "hi"}])

	def test_budget_cap_switches_to_byok(self):
		"""Reaching the monthly budget pauses site keys."""
		settings = frappe.get_single("AI Settings")
		settings.update({"ai_enabled": 1, "anthropic_api_key": "sk-ant-test-key-000000000000", "monthly_budget_usd": 0.000001, "byok_only": 0})
		settings.save()
		fake = {"text": "ok", "tokens_in": 1000, "tokens_out": 1000}
		with patch("stackpilot.sp_ai.utils.providers.complete", return_value=fake):
			gateway.run("chat", "system", [{"role": "user", "content": "hi"}], user="Administrator")
		self.assertEqual(frappe.db.get_single_value("AI Settings", "byok_only"), 1)
		frappe.clear_document_cache("AI Settings", "AI Settings")
		with self.assertRaises(gateway.AIUnavailable):
			gateway.run("chat", "system", [{"role": "user", "content": "hi"}], user="Administrator")
		settings = frappe.get_single("AI Settings")
		settings.update({"byok_only": 0, "monthly_budget_usd": 25, "month_spend_usd": 0, "anthropic_api_key": ""})
		settings.save()
		frappe.clear_document_cache("AI Settings", "AI Settings")


class TestQualityAndVisitors(IntegrationTestCase):
	"""Junk titles are refused; visitors get a small daily AI allowance."""

	def test_keyboard_mash_rejected(self):
		"""Mash and one-word titles fail; real titles pass."""
		self.assertFalse(forum.looks_like_words("sddsfsdfdssddcsd"))
		self.assertFalse(forum.looks_like_words("help help"))
		self.assertTrue(forum.looks_like_words("Pods stuck Pending on EKS after scale up"))

	def test_visitor_allowance(self):
		"""A visitor is refused after the daily per-IP allowance."""
		settings = frappe.get_single("AI Settings")
		settings.update({"ai_enabled": 1, "anthropic_api_key": "sk-ant-test-key-000000000000", "guest_daily_requests": 2, "byok_only": 0, "monthly_budget_usd": 25})
		settings.save()
		frappe.clear_document_cache("AI Settings", "AI Settings")
		frappe.local.request_ip = "203.0.113.9"
		fake = {"text": "ok", "tokens_in": 10, "tokens_out": 10}
		with patch("stackpilot.sp_ai.utils.providers.complete", return_value=fake):
			gateway.run("chat", "s", [{"role": "user", "content": "q"}], user="Guest")
			gateway.run("chat", "s", [{"role": "user", "content": "q"}], user="Guest")
			with self.assertRaises(gateway.AIUnavailable):
				gateway.run("chat", "s", [{"role": "user", "content": "q"}], user="Guest")
		settings = frappe.get_single("AI Settings")
		settings.update({"anthropic_api_key": "", "guest_daily_requests": 5, "month_spend_usd": 0})
		settings.save()
		frappe.clear_document_cache("AI Settings", "AI Settings")
