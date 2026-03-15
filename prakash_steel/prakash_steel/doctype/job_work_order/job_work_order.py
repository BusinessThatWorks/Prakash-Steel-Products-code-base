# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JOBWorkOrder(Document):
	pass


@frappe.whitelist()
def make_sales_invoice(source_name):
	source = frappe.get_doc("JOB Work Order", source_name)

	si = frappe.new_doc("Sales Invoice")
	si.company = frappe.db.get_default("company")
	si.customer = source.customer
	si.posting_date = source.job_work_date

	for row in source.work_item_table:
		if row.raw_material and row.rm_qty_required:
			si.append("items", {
				"item_code": row.raw_material,
				"qty": row.rm_qty_required,
			})

	return si


@frappe.whitelist()
def make_purchase_receipt(source_name):
	source = frappe.get_doc("JOB Work Order", source_name)

	pr = frappe.new_doc("Purchase Receipt")
	pr.company = frappe.db.get_default("company")
	pr.posting_date = source.job_work_date

	company_currency = frappe.get_cached_value("Company", pr.company, "default_currency") or "INR"
	pr.currency = company_currency
	pr.conversion_rate = 1

	for row in source.work_item_table:
		if row.fg_item and row.fg_production_qty:
			pr.append("items", {
				"item_code": row.fg_item,
				"qty": row.fg_production_qty,
			})

	return pr
