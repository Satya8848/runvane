# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt

"""Add or refresh the cloud-services guides in stackpilot/seed/guides.json."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cloud_services import GUIDES  # noqa: E402

PATH = os.path.join(os.path.dirname(__file__), "..", "stackpilot", "seed", "guides.json")
data = json.load(open(PATH))
slugs = {g["slug"] for g in GUIDES}
data["guides"] = [g for g in data["guides"] if g["slug"] not in slugs] + GUIDES
json.dump(data, open(PATH, "w"), indent=1, ensure_ascii=False)
print(len(GUIDES), "cloud guides;", len(data["guides"]), "guides in total")
