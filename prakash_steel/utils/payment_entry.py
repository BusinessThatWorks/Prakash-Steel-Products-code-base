import frappe
from frappe.utils import nowtime


def set_submitted_time(doc, method=None):
	"""Store submit time in custom_submitted_time on submit."""
	if doc.get("custom_submitted_time"):
		return

	# If fixture is not yet migrated, avoid blocking submission.
	if not frappe.db.has_column(doc.doctype, "custom_submitted_time"):
		return

	doc.db_set("custom_submitted_time", nowtime(), update_modified=False)
