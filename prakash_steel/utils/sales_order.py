import frappe
from frappe import _


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	"""
	Override of erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice.

	Excludes Sales Order Items where custom_closed = 1 from the generated
	Sales Invoice so they are never carried forward to billing.
	"""
	from erpnext.selling.doctype.sales_order.sales_order import (
		make_sales_invoice as _make_sales_invoice,
	)

	doc = _make_sales_invoice(source_name, target_doc)

	if not (doc and doc.items):
		return doc

	original_count = len(doc.items)

	doc.items = [
		item
		for item in doc.items
		if not (
			item.get("so_detail")
			and frappe.db.get_value("Sales Order Item", item.so_detail, "custom_closed")
		)
	]

	# Re-index after filtering
	for idx, item in enumerate(doc.items, 1):
		item.idx = idx

	closed_count = original_count - len(doc.items)
	if closed_count:
		frappe.msgprint(
			_("{0} closed item(s) were excluded from the Sales Invoice.").format(closed_count),
			indicator="orange",
			alert=True,
		)

	return doc
