# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JOBWorkOrder(Document):
	def on_submit(self):
		self.db_set("status", "Pending")


@frappe.whitelist()
def make_sales_invoice(source_name):
	source = frappe.get_doc("JOB Work Order", source_name)

	si = frappe.new_doc("Sales Invoice")
	si.company = "Prakash Steel Products Pvt Ltd"
	si.customer = source.customer
	si.posting_date = source.job_work_date
	si.custom_job_work_order = source_name

	# Group rm_qty_required by raw_material
	rm_qty_map = {}
	for row in source.work_item_table:
		if row.raw_material and row.rm_qty_required:
			rm_qty_map[row.raw_material] = rm_qty_map.get(row.raw_material, 0) + (row.rm_qty_required or 0)

	for raw_material, total_required in rm_qty_map.items():
		already = (
			frappe.db.sql(
				"""
			SELECT COALESCE(SUM(sii.qty), 0)
			FROM `tabSales Invoice Item` sii
			JOIN `tabSales Invoice` si ON si.name = sii.parent
			WHERE si.custom_job_work_order = %s
			  AND si.docstatus = 1
			  AND sii.item_code = %s
			""",
				(source_name, raw_material),
			)[0][0]
			or 0
		)
		pending_qty = total_required - already
		if pending_qty <= 0:
			continue
		si.append("items", {"item_code": raw_material, "qty": pending_qty})

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

	# Group rm_qty_required by raw_material
	rm_qty_map = {}
	for row in source.work_item_table:
		if row.raw_material and row.rm_qty_required:
			rm_qty_map[row.raw_material] = rm_qty_map.get(row.raw_material, 0) + (row.rm_qty_required or 0)

	for raw_material, total_required in rm_qty_map.items():
		already = (
			frappe.db.sql(
				"""
			SELECT COALESCE(SUM(dni.qty), 0)
			FROM `tabDelivery Note Item` dni
			JOIN `tabDelivery Note` dn ON dn.name = dni.parent
			WHERE dn.custom_job_work_order = %s
			  AND dn.docstatus = 1
			  AND dni.item_code = %s
			""",
				(source_name, raw_material),
			)[0][0]
			or 0
		)
		pending_qty = total_required - already
		if pending_qty <= 0:
			continue
		dn.append("items", {"item_code": raw_material, "qty": pending_qty})

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
			pending_qty = (row.fg_production_qty or 0) - (row.actual_received_qty or 0)
			if pending_qty <= 0:
				continue
			pr.append(
				"items",
				{
					"item_code": row.fg_item,
					"qty": pending_qty,
				},
			)

	pr.run_method("set_missing_values")
	pr.run_method("calculate_taxes_and_totals")
	return pr
