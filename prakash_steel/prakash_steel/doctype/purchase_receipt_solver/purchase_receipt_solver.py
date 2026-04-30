# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PurchasereceiptSolver(Document):
	pass


@frappe.whitelist()
def fix_total_party_billing_qty():
	"""
	For every submitted Purchase Receipt where custom_total_party_billing_qty
	is wrong (0 or doesn't match the sum of child items), update it directly
	in the DB to bypass the submit-validation check.
	"""
	results = []

	# Get all submitted Purchase Receipts
	pr_names = frappe.get_all("Purchase Receipt", filters={"docstatus": 1}, pluck="name")

	for pr_name in pr_names:
		# Sum custom_party_billing_qty from all child items
		total = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(custom_party_billing_qty), 0)
			FROM `tabPurchase Receipt Item`
			WHERE parent = %s
			""",
			pr_name,
		)[0][0] or 0

		current = frappe.db.get_value("Purchase Receipt", pr_name, "custom_total_party_billing_qty") or 0

		if total != current:
			frappe.db.set_value(
				"Purchase Receipt",
				pr_name,
				"custom_total_party_billing_qty",
				total,
				update_modified=False,
			)
			results.append({"pr": pr_name, "old": current, "new": total})

	frappe.db.commit()

	return {
		"fixed": len(results),
		"details": results,
	}
