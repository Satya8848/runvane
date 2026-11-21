// Copyright (c) 2026, Satya and contributors. For license information, please see license.txt
// Turn the built index.html into the Frappe page www/spa.html with the CSRF token and boot data.
import fs from "fs";
import path from "path";

const root = path.resolve(import.meta.dirname, "..");
const html = fs
	.readFileSync(path.join(root, "../stackpilot/public/spa/index.html"), "utf8")
	.replace("<head>", "<head>\n    <script>window.csrf_token = '{{ frappe.session.csrf_token }}'; window.sp_boot = {{ boot | tojson }};</script>\n    <title>{{ meta_title }}</title>\n    <meta name=\"description\" content=\"{{ meta_description }}\">\n    <meta property=\"og:title\" content=\"{{ meta_title }}\">\n    <meta property=\"og:description\" content=\"{{ meta_description }}\">")
	.replace(/<title>[^<]*<\/title>\s*(?=<link)/, "");
fs.writeFileSync(path.join(root, "../stackpilot/www/spa.html"), html);
console.log("wrote www/spa.html");
