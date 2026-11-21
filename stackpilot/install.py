# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Install and migrate hooks: roles, website settings and seed content.
Seeding only inserts missing records, so edits made on the site are kept."""

import json
import os

import frappe

from stackpilot.sp_core.utils.members import create_roles

SEED = os.path.join(os.path.dirname(__file__), "seed")

TEMPLATES = [
	("3-tier web app on AWS", "AWS", "Multi-AZ web tier behind an ALB with RDS and ElastiCache.",
	 "flowchart LR\n  U[Users] --> R53[Route 53] --> CF[CloudFront + WAF] --> ALB[ALB]\n  subgraph VPC\n    ALB --> A1[App AZ-a] & A2[App AZ-b]\n    A1 & A2 --> C[(ElastiCache)]\n    A1 & A2 --> DB[(RDS Multi-AZ)]\n  end\n  A1 & A2 --> S3[(S3)]"),
	("Microservices on AKS", "Azure", "Front Door, AKS with ingress, Service Bus and Azure SQL.",
	 "flowchart LR\n  U[Users] --> FD[Front Door + WAF] --> AG[App Gateway Ingress]\n  subgraph AKS\n    AG --> S1[orders] & S2[payments] & S3[catalog]\n  end\n  S1 --> SB[[Service Bus]] --> S2\n  S1 & S2 --> SQL[(Azure SQL)]\n  S3 --> RC[(Redis Cache)]\n  KV[(Key Vault)] -.-> AKS"),
	("Event-driven serverless", "Serverless", "API Gateway, Lambda, EventBridge, SQS and DynamoDB.",
	 "flowchart LR\n  API[API Gateway] --> L1[Lambda create]\n  L1 --> DDB[(DynamoDB)]\n  L1 --> EB[EventBridge] --> Q[[SQS]] --> L2[Lambda worker]\n  Q -.failures.-> DLQ[[DLQ]]\n  DDB -->|stream| L3[Lambda notify]"),
	("Multi-region disaster recovery", "Reliability", "Warm standby with DNS failover and cross-region replication.",
	 "flowchart LR\n  DNS[Route 53 failover] --> P[Primary region: app + DB]\n  DNS -.on failure.-> D[DR region: scaled-down app]\n  P -.async replication.-> DR[(DB replica)]\n  D --> DR\n  P --> B[(Backups cross-account)]"),
	("CI/CD with GitOps", "Delivery", "Pipeline builds and scans, Argo CD deploys from Git.",
	 "flowchart LR\n  Dev[Developer] --> PR[Pull request] --> CI[CI: test + scan + build]\n  CI --> REG[(Registry)]\n  CI -->|bump tag| GIT[(Env repo)]\n  ARGO[Argo CD] -->|sync| K8S[Kubernetes]\n  ARGO --> GIT\n  REG --> K8S"),
	("Data pipeline", "Data", "Ingest, stream, transform and analyse.",
	 "flowchart LR\n  SRC[Apps / IoT] --> K[[Kafka / Kinesis]] --> P[Stream processor]\n  P --> L[(Data lake S3)] --> W[(Warehouse)] --> BI[Dashboards]\n  P --> RT[(Real-time store)] --> API[API]"),
]
BADGES = [
	("First question", "Bronze", "first_question", "Asked a first question."),
	("First answer", "Bronze", "first_answer", "Posted a first answer."),
	("Accepted", "Silver", "first_accepted", "Had an answer accepted."),
	("Architect", "Silver", "five_diagrams", "Saved five architecture boards."),
	("Builder", "Bronze", "first_build", "Generated a first Ansible or setup file."),
	("Helper", "Gold", "ten_accepted", "Ten accepted answers."),
]


def after_install():
	"""
	Hook target for `after_install`.

	Returns:
		None
	"""
	seed()


def after_migrate():
	"""
	Hook target for `after_migrate`: add seed content shipped in a new version.

	Returns:
		None
	"""
	seed()


def seed():
	"""
	Create roles, open sign-up and insert missing seed content.
	`bench --site <site> execute stackpilot.install.seed`

	Returns:
		dict: Counts of inserted records.
	"""
	create_roles()
	settings = frappe.get_single("Website Settings")
	if settings.disable_signup or settings.home_page != "spa" or settings.app_name != "Runvane":
		settings.disable_signup = 0
		settings.home_page = "spa"
		settings.app_name = "Runvane"
		settings.brand_html = "Runvane"
		settings.save(ignore_permissions=True)
	frappe.db.set_single_value("System Settings", "app_name", "Runvane")
	counts = {
		"roles": _seed_roles(), "playbooks": _seed_playbooks(), "guides": _seed_guides(),
		"terms": _seed_terms(), "templates": _seed_templates(), "badges": _seed_badges(),
	}
	frappe.db.commit()
	return counts


def _load(name):
	"""
	Read one seed JSON file.

	Parameters:
		name (str, required): File name in seed/.

	Returns:
		dict | list: Parsed JSON.
	"""
	with open(os.path.join(SEED, name)) as handle:
		return json.load(handle)


def _insert_missing(doctype, key_field, rows):
	"""
	Insert rows whose key does not exist yet.

	Parameters:
		doctype (str, required): DocType.
		key_field (str, required): Field that identifies a row.
		rows (list[dict], required): Records.

	Returns:
		int: Inserted count.
	"""
	existing = set(frappe.get_all(doctype, pluck=key_field))
	inserted = 0
	for row in rows:
		if row[key_field] in existing:
			continue
		frappe.get_doc({"doctype": doctype, **row}).insert(ignore_permissions=True)
		inserted += 1
	return inserted


def _seed_roles():
	"""Insert the role tracks. Returns: int."""
	return _insert_missing("Role Track", "slug", _load("playbooks.json")["roles"])


def _seed_playbooks():
	"""Insert the playbooks. Returns: int."""
	return _insert_missing("Playbook", "slug", _load("playbooks.json")["playbooks"])


def _seed_guides():
	"""
	Insert configuration guides and interview items, and refresh seeded guides
	whose shipped text changed. A guide last edited by someone other than
	Administrator is left alone, so editors' changes are never overwritten.

	Returns:
		int: Inserted or refreshed count.
	"""
	data = _load("guides.json")
	count = _insert_missing("Config Guide", "slug", data["guides"])
	for row in data["guides"]:
		current = frappe.db.get_value("Config Guide", row["slug"], ["modified_by", "body", "intro"], as_dict=True)
		if current and current.modified_by == "Administrator" and (current.body != row["body"] or current.intro != row["intro"]):
			doc = frappe.get_doc("Config Guide", row["slug"])
			doc.update({k: row[k] for k in ("title", "category", "intro", "body", "diagram")})
			doc.save(ignore_permissions=True)
			count += 1
	return count + _insert_missing("Interview Item", "question", data["interview"])


def _seed_terms():
	"""Insert glossary terms. Returns: int."""
	rows = [{k: t[k] for k in ("term", "category", "short_definition", "explanation", "related_terms")} for t in _load("terms.json")["terms"]]
	return _insert_missing("SP Term", "term", rows)


def _seed_templates():
	"""Insert diagram templates. Returns: int."""
	return _insert_missing("Diagram Template", "title", [{"title": t, "category": c, "description": d, "mermaid": m} for t, c, d, m in TEMPLATES])


def _seed_badges():
	"""Insert badges. Returns: int."""
	return _insert_missing("Badge", "badge_name", [{"badge_name": n, "level": l, "criteria_key": k, "description": d} for n, l, k, d in BADGES])
