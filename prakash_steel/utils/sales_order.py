import frappe
from frappe import _


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False, args=None):
	from erpnext.selling.doctype.sales_order.sales_order import (
		make_sales_invoice as _make_sales_invoice,
	)

	doc = _make_sales_invoice(
		source_name,
		target_doc,
		ignore_permissions=ignore_permissions,
		args=args,
	)

	if not (doc and doc.items):
		return doc

	original_count = len(doc.items)

	doc.items = [
		item
		for item in doc.items
		if not (
			item.get("so_detail") and frappe.db.get_value("Sales Order Item", item.so_detail, "custom_closed")
		)
	]

	# Re-index after filtering
	for idx, item in enumerate(doc.items, 1):
		item.idx = idx

	# Populate custom_base_rate from rate so loading charges can be tracked correctly
	for item in doc.items:
		if not item.get("custom_base_rate"):
			item.custom_base_rate = item.rate

	closed_count = original_count - len(doc.items)
	if closed_count:
		frappe.msgprint(
			_("{0} closed item(s) were excluded from the Sales Invoice.").format(closed_count),
			indicator="orange",
			alert=True,
		)

	return doc
