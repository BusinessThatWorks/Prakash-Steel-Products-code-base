import frappe


@frappe.whitelist()
def get_last_purchase_invoice_rate(item_code, company=None):
    if not item_code:
        return 0

    # Fetch the latest submitted Purchase Invoice Item rate.
    # If company is provided from Material Request, keep the result company-specific.
    conditions = ["pii.item_code = %s", "pi.docstatus = 1"]
    values = [item_code]

    if company:
        conditions.append("pi.company = %s")
        values.append(company)

    result = frappe.db.sql(
        f"""
        SELECT pii.rate
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi
            ON pi.name = pii.parent
        WHERE {' AND '.join(conditions)}
        ORDER BY pi.posting_date DESC, pi.posting_time DESC, pii.creation DESC
        LIMIT 1
        """,
        values=values,
        as_dict=True,
    )

    if result and result[0].get("rate") is not None:
        return result[0]["rate"]

    # Fallback to Item master value if there is no submitted PI row.
    rate = frappe.db.get_value("Item", item_code, "last_purchase_rate")

    return rate or 0
