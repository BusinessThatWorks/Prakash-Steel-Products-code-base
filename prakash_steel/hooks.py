app_name = "prakash_steel"
app_title = "Prakash Steel"
app_publisher = "beetashoke chakraborty"
app_description = "Prakash Steel"
app_email = "beetashoke.chakraborty@clapgrow.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "prakash_steel",
# 		"logo": "/assets/prakash_steel/logo.png",
# 		"title": "Prakash Steel",
# 		"route": "/prakash_steel",
# 		"has_permission": "prakash_steel.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/prakash_steel/css/prakash_steel.css"
# app_include_js = "/assets/prakash_steel/js/prakash_steel.js"

# include js, css files in header of web template
# web_include_css = "/assets/prakash_steel/css/prakash_steel.css"
# web_include_js = "/assets/prakash_steel/js/prakash_steel.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "prakash_steel/public/scss/website"

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
# app_include_icons = "prakash_steel/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "prakash_steel.utils.jinja_methods",
# 	"filters": "prakash_steel.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "prakash_steel.install.before_install"
# after_install = "prakash_steel.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "prakash_steel.uninstall.before_uninstall"
# after_uninstall = "prakash_steel.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "prakash_steel.utils.before_app_install"
# after_app_install = "prakash_steel.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "prakash_steel.utils.before_app_uninstall"
# after_app_uninstall = "prakash_steel.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "prakash_steel.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # 	# "Stock Entry": {
    # 	# 	"validate": "prakash_steel.utils.stock_entry.validate_vehicle_no_for_material_transfer",
    # 	# 	"on_submit": "prakash_steel.utils.stock_entry.update_decoupled_lead_time_on_stock_entry_submit",
    # 	# },
    "Item": {
        "validate": "prakash_steel.utils.item.validate_min_order_qty_and_batch_size",
        "on_update": "prakash_steel.utils.item.update_decoupled_lead_time_on_item_save",
    },
    "BOM": {
        "on_submit": "prakash_steel.utils.item.update_decoupled_lead_time_on_bom_save",
        "on_update_after_submit": "prakash_steel.utils.item.update_decoupled_lead_time_on_bom_save",
    },
    "Purchase Receipt": {
        "on_submit": "prakash_steel.utils.purchase_receipt.validate_purchase_receipt_quantity",
    },
    "Sales Invoice": {
        "validate": "prakash_steel.utils.sales_invoice.validate_sales_order_items_required",
        "on_submit": "prakash_steel.utils.sales_invoice.create_stock_entries_on_submit",
    },
    # Note: Finish Weight on_submit is handled in the Document class itself
    # No need to register here as class methods are automatically called
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"prakash_steel.tasks.all"
# 	],
# 	"daily": [
# 		"prakash_steel.tasks.daily"
# 	],
# 	"hourly": [
# 		"prakash_steel.tasks.hourly"
# 	],
# 	"weekly": [
# 		"prakash_steel.tasks.weekly"
# 	],
# 	"monthly": [
# 		"prakash_steel.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "prakash_steel.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "prakash_steel.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "prakash_steel.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["prakash_steel.utils.before_request"]
# after_request = ["prakash_steel.utils.after_request"]

# Job Events
# ----------
# before_job = ["prakash_steel.utils.before_job"]
# after_job = ["prakash_steel.utils.after_job"]

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
# 	"prakash_steel.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {"doctype": "Custom Field", "filters": {"module": "Prakash Steel"}},
]

doctype_js = {
    "Material Request": "public/js/material_request.js",
    "Sales Order": "public/js/sales_order.js",
    "Item": "public/js/item.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
}

# Page JS
page_js = {
    "procurement-tracker-dashboard": "prakash_steel/page/procurement_tracker_dashboard/procurement_tracker_dashboard.js",
    "sales-summary-dashboard": "prakash_steel/page/sales_summary_dashboard/sales_summary_dashboard.js",
}
app_include_js = ["/assets/prakash_steel/js/number_cards_uom.js"]

# Scheduled Tasks
# ---------------

scheduler_events = {
    # Cron job to capture daily on hand colour snapshot from
    # "PO Recommendation for PSP" report into
    # "Item wise Daily On Hand Colour" doctype.
    "cron": {
        # Runs every day at 14:31 server time
        "52 14 * * *": [
            "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.save_daily_on_hand_colour"
        ]
    },
    # Generic 'all' scheduler hook that runs frequently; wrapper
    # function ensures we only snapshot once per day after 14:31.
    # "all": [
    # 	"prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.run_daily_on_hand_colour_snapshot"
    # ],
}
