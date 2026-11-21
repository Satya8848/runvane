# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AIProviderKey(Document):
	"""A member's own API key for one provider (used instead of the site's)."""

	pass
