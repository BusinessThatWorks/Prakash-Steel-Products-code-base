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
	si.company = "Prakash Steel Products Pvt Ltd"
	si.customer = source.customer
	si.posting_date = source.job_work_date
	si.custom_job_work_order = source_name

	for row in source.work_item_table:
		if row.raw_material and row.rm_qty_required:
			si.append("items", {
				"item_code": row.raw_material,
				"qty": row.rm_qty_required,
			})

	si.run_method("set_missing_values")
	si.run_method("calculate_taxes_and_totals")
	return si


@frappe.whitelist()
def make_delivery_note(source_name):
	source = frappe.get_doc("JOB Work Order", source_name)

	dn = frappe.new_doc("Delivery Note")
	dn.company = "Prakash Steel Products Pvt Ltd"
	dn.posting_date = source.job_work_date
	dn.customer = source.customer
	dn.custom_job_work_order = source_name

	company_currency = frappe.get_cached_value("Company", dn.company, "default_currency") or "INR"
	dn.currency = company_currency
	dn.conversion_rate = 1

	for row in source.work_item_table:
		if row.raw_material and row.rm_qty_required:
			dn.append("items", {
				"item_code": row.raw_material,
				"qty": row.rm_qty_required,
			})

	dn.run_method("set_missing_values")
	dn.run_method("calculate_taxes_and_totals")
	return dn


@frappe.whitelist()
def make_purchase_receipt(source_name):
	source = frappe.get_doc("JOB Work Order", source_name)

	pr = frappe.new_doc("Purchase Receipt")
	pr.company = "Prakash Steel Products Pvt Ltd"
	pr.posting_date = source.job_work_date
	pr.custom_job_work_order = source_name

	company_currency = frappe.get_cached_value("Company", pr.company, "default_currency") or "INR"
	pr.currency = company_currency
	pr.conversion_rate = 1

	for row in source.work_item_table:
		if row.fg_item and row.fg_production_qty:
			pr.append("items", {
				"item_code": row.fg_item,
				"qty": row.fg_production_qty,
			})

	pr.run_method("set_missing_values")
	pr.run_method("calculate_taxes_and_totals")
	return pr
