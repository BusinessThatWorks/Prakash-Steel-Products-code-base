import frappe


@frappe.whitelist()
def get_last_purchase_invoice_rate(item_code):
	result = frappe.db.sql(
		"""
        SELECT pii.rate
        FROM `tabPurchase Invoice Item` pii
        JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pii.item_code = %s
          AND pi.docstatus = 1
        ORDER BY pi.posting_date DESC, pi.posting_time DESC
        LIMIT 1
    """,
		(item_code),
		as_dict=True,
	)

	if result:
		return result[0].rate
	else:
		return 0
