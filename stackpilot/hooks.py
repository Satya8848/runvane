app_name = "stackpilot"
app_title = "Runvane"
app_publisher = "Satya"
app_description = "Problem-solving platform for DevOps, DevSecOps, architects, programmers, Linux admins and DBAs: playbooks, forum, AI analysis, architecture board and builders"
app_email = "satya8848@users.noreply.github.com"
app_license = "mit"

after_install = "stackpilot.install.after_install"
after_migrate = "stackpilot.install.after_migrate"

# The single-page app answers these paths; Frappe keeps /app (Desk), /api, /login, /assets.
website_route_rules = [
	{"from_route": f"/{prefix}/<path:app_path>", "to_route": "spa"}
	for prefix in ("t", "playbooks", "guides", "q", "ask", "ai", "board", "tools", "glossary", "interview", "search", "u", "learn")
] + [
	{"from_route": f"/{prefix}", "to_route": "spa"}
	for prefix in ("playbooks", "guides", "q", "ask", "ai", "board", "tools", "glossary", "interview", "search", "learn", "join", "me")
]

scheduler_events = {"monthly": ["stackpilot.sp_ai.tasks.reset_monthly_spend"]}

_INDEXED = {"on_update": "stackpilot.utils.search.index_doc", "on_trash": "stackpilot.utils.search.index_doc"}
doc_events = {
	"User": {"after_insert": "stackpilot.sp_core.utils.members.on_user_insert"},
	"Playbook": _INDEXED,
	"Config Guide": _INDEXED,
	"Question": _INDEXED,
	"SP Term": _INDEXED,
	"Interview Item": _INDEXED,
	"Architecture Diagram": _INDEXED,
}

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "stackpilot",
# 		"logo": "/assets/stackpilot/logo.png",
# 		"title": "Runvane",
# 		"route": "/stackpilot",
# 		"has_permission": "stackpilot.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/stackpilot/css/stackpilot.css"
# app_include_js = "/assets/stackpilot/js/stackpilot.js"

# include js, css files in header of web template
# web_include_css = "/assets/stackpilot/css/stackpilot.css"
# web_include_js = "/assets/stackpilot/js/stackpilot.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "stackpilot/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "stackpilot/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "stackpilot.utils.jinja_methods",
# 	"filters": "stackpilot.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "stackpilot.install.before_install"
# after_install = "stackpilot.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "stackpilot.uninstall.before_uninstall"
# after_uninstall = "stackpilot.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "stackpilot.utils.before_app_install"
# after_app_install = "stackpilot.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "stackpilot.utils.before_app_uninstall"
# after_app_uninstall = "stackpilot.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "stackpilot.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "stackpilot.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"stackpilot.tasks.all"
# 	],
# 	"daily": [
# 		"stackpilot.tasks.daily"
# 	],
# 	"hourly": [
# 		"stackpilot.tasks.hourly"
# 	],
# 	"weekly": [
# 		"stackpilot.tasks.weekly"
# 	],
# 	"monthly": [
# 		"stackpilot.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "stackpilot.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "stackpilot.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "stackpilot.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "stackpilot.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["stackpilot.utils.before_request"]
# after_request = ["stackpilot.utils.after_request"]

# Job Events
# ----------
# before_job = ["stackpilot.utils.before_job"]
# after_job = ["stackpilot.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"stackpilot.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

