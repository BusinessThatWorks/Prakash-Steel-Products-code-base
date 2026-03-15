import frappe


def update_jwo_on_sales_invoice_submit(doc, method):
	"""On Sales Invoice submit: update actual_transferred_qty and status on linked JWO."""
	jwo_name = doc.get("custom_job_work_order")
	if not jwo_name:
		return

	jwo = frappe.get_doc("JOB Work Order", jwo_name)
	if jwo.job_work_type != "Sale-Purchase":
		return

	_update_transferred_qty(jwo, "Sales Invoice", "Sales Invoice Item")
	_set_transfer_status(jwo)
	_update_loss_per(jwo)


def update_jwo_on_delivery_note_submit(doc, method):
	"""On Delivery Note submit: update actual_received_qty and status on linked JWO."""
	jwo_name = doc.get("custom_job_work_order")
	if not jwo_name:
		return

	jwo = frappe.get_doc("JOB Work Order", jwo_name)
	if jwo.job_work_type != "Subcontracting":
		return

	_update_transferred_qty(jwo, "Delivery Note", "Delivery Note Item")
	_set_transfer_status(jwo)
	_update_loss_per(jwo)


def update_jwo_on_purchase_receipt_submit(doc, method):
	"""On Purchase Receipt submit: update actual_received_qty and status on linked JWO."""
	jwo_name = doc.get("custom_job_work_order")
	if not jwo_name:
		return

	jwo = frappe.get_doc("JOB Work Order", jwo_name)

	for row in jwo.work_item_table:
		if not row.fg_item:
			continue

		total = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(pri.qty), 0)
			FROM `tabPurchase Receipt Item` pri
			JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
			WHERE pr.custom_job_work_order = %s
			  AND pr.docstatus = 1
			  AND pri.item_code = %s
			""",
			(jwo.name, row.fg_item),
		)[0][0] or 0

		frappe.db.set_value("JOB Work Item table", row.name, "actual_received_qty", total)

	jwo.reload()
	rows = [r for r in jwo.work_item_table if r.fg_item]
	if not rows:
		return

	fully_done = all((r.actual_received_qty or 0) >= (r.fg_production_qty or 0) for r in rows)
	any_started = any((r.actual_received_qty or 0) > 0 for r in rows)

	if fully_done:
		new_status = "Completed"
	elif any_started:
		new_status = "Partially Received"
	else:
		new_status = "Pending"

	frappe.db.set_value("JOB Work Order", jwo.name, "status", new_status)
	_update_loss_per(jwo)


def _update_transferred_qty(jwo, parent_doctype, child_doctype):
	"""Sum submitted docs and update actual_transferred_qty per child row by raw_material."""
	for row in jwo.work_item_table:
		if not row.raw_material:
			continue

		total = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(ci.qty), 0)
			FROM `tab{child}` ci
			JOIN `tab{parent}` p ON p.name = ci.parent
			WHERE p.custom_job_work_order = %s
			  AND p.docstatus = 1
			  AND ci.item_code = %s
			""".format(child=child_doctype, parent=parent_doctype),
			(jwo.name, row.raw_material),
		)[0][0] or 0

		frappe.db.set_value("JOB Work Item table", row.name, "actual_transferred_qty", total)


def _update_received_qty(jwo, parent_doctype, child_doctype):
	"""Sum submitted docs and update actual_received_qty per child row by raw_material."""
	for row in jwo.work_item_table:
		if not row.raw_material:
			continue

		total = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(ci.qty), 0)
			FROM `tab{child}` ci
			JOIN `tab{parent}` p ON p.name = ci.parent
			WHERE p.custom_job_work_order = %s
			  AND p.docstatus = 1
			  AND ci.item_code = %s
			""".format(child=child_doctype, parent=parent_doctype),
			(jwo.name, row.raw_material),
		)[0][0] or 0

		frappe.db.set_value("JOB Work Item table", row.name, "actual_received_qty", total)


def _set_transfer_status(jwo):
	"""Pending → In-Process → Material Transferred based on actual_transferred_qty vs rm_qty_required."""
	jwo.reload()
	rows = [r for r in jwo.work_item_table if r.raw_material]
	if not rows:
		return

	fully_done = all((r.actual_transferred_qty or 0) >= (r.rm_qty_required or 0) for r in rows)
	any_started = any((r.actual_transferred_qty or 0) > 0 for r in rows)

	if fully_done:
		new_status = "Material Transferred"
	elif any_started:
		new_status = "In-Process"
	else:
		new_status = "Pending"

	frappe.db.set_value("JOB Work Order", jwo.name, "status", new_status)


def _set_received_status(jwo):
	"""Pending → Partially Received → Completed based on actual_received_qty vs rm_qty_required."""
	jwo.reload()
	rows = [r for r in jwo.work_item_table if r.raw_material]
	if not rows:
		return

	fully_done = all((r.actual_received_qty or 0) >= (r.rm_qty_required or 0) for r in rows)
	any_started = any((r.actual_received_qty or 0) > 0 for r in rows)

	if fully_done:
		new_status = "Completed"
	elif any_started:
		new_status = "Partially Received"
	else:
		new_status = "Pending"

	frappe.db.set_value("JOB Work Order", jwo.name, "status", new_status)


def _update_loss_per(jwo):
	"""Calculate loss_per = (actual_transferred_qty - actual_received_qty) / actual_transferred_qty * 100.
	Minimum 0. Reload jwo first to get latest values."""
	jwo.reload()
	for row in jwo.work_item_table:
		transferred = row.actual_transferred_qty or 0
		received = row.actual_received_qty or 0

		if transferred > 0:
			loss = (transferred - received) / transferred * 100
			loss_per = max(loss, 0)
		else:
			loss_per = 0

		frappe.db.set_value("JOB Work Item table", row.name, "loss_per", round(loss_per, 2))
