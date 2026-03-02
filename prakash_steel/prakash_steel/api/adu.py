import frappe
from frappe.utils import cint, flt, today, add_days


def _get_horizon_days() -> int:
    """Return number of days to look back based on ADU Horizon.single DocType."""
    horizon = frappe.get_single("ADU Horizon")
    weeks_raw = getattr(horizon, "week", None) or 0
    weeks = cint(weeks_raw) or 0
    if weeks <= 0:
        return 0
    return weeks * 7


def _calculate_item_adu(item_code: str) -> float:
    """Calculate Average Daily Usage for a single item."""
    if not item_code:
        return 0.0

    days = _get_horizon_days()
    if days <= 0:
        return 0.0

    end_date = today()
    # Include "days" number of days including today
    start_date = add_days(end_date, -(days - 1))

    row = frappe.db.sql(
        """
        SELECT COALESCE(SUM(sii.qty), 0) AS total_qty
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE
            sii.item_code = %s
            AND si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
        """,
        (item_code, start_date, end_date),
        as_dict=True,
    )

    total_qty = flt(row[0].get("total_qty") if row else 0.0)
    if days <= 0:
        return 0.0

    adu = flt(total_qty / days, 3)
    return adu


def _update_item_adu(item_code: str) -> float:
    """Internal helper to calculate and write ADU back to the Item."""
    adu = _calculate_item_adu(item_code)

    # Only attempt to update if the Item exists
    if frappe.db.exists("Item", item_code):
        # custom_adu is expected to be a Float custom field on Item
        frappe.db.set_value("Item", item_code, "custom_adu", adu)

    return adu


@frappe.whitelist()
def update_item_adu(item_code: str) -> float:
    """
    Public/whitelisted API to recalculate ADU for a single Item.

    Usage (Python):
        from prakash_steel.api.adu import update_item_adu
        update_item_adu("ITEM-0001")

    Usage (JS):
        frappe.call('prakash_steel.api.adu.update_item_adu', { item_code: 'ITEM-0001' })
    """
    if not item_code:
        frappe.throw("Item Code is required to update ADU.")

    return _update_item_adu(item_code)


def update_adu_for_sales_invoice(doc) -> None:
    """
    Convenience helper to be called from Sales Invoice hooks/overrides.
    Recalculates ADU for all unique items present in the given Sales Invoice doc.
    """
    if not getattr(doc, "items", None):
        return

    processed: set[str] = set()
    for row in doc.items:
        item_code = getattr(row, "item_code", None)
        if not item_code or item_code in processed:
            continue
        processed.add(item_code)
        try:
            _update_item_adu(item_code)
        except Exception:
            frappe.log_error(
                title="Failed to update ADU for Item {0}".format(item_code),
                message=frappe.get_traceback(),
            )





