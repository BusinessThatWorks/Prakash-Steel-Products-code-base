import math

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


def _calculate_item_adu(item_code: str) -> int:
    """Calculate Average Daily Usage for a single item (ceiled to whole number)."""
    if not item_code:
        return 0

    days = _get_horizon_days()
    if days <= 0:
        return 0

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
        return 0

    # Ceil to whole number so 2132.143 → 2133
    adu_raw = total_qty / days if days > 0 else 0
    adu_ceiled = int(math.ceil(adu_raw)) if adu_raw > 0 else 0
    return adu_ceiled


def _update_item_adu(item_code: str) -> int:
    """Internal helper to calculate and write ADU back to the Item."""
    adu = _calculate_item_adu(item_code)

    # Only attempt to update if the Item exists
    if frappe.db.exists("Item", item_code):
        # custom_adu is expected to be a Float custom field on Item
        frappe.db.set_value("Item", item_code, "custom_adu", adu)

    return adu


@frappe.whitelist()
def update_item_adu(item_code: str) -> int:
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


@frappe.whitelist()
def recalculate_adu_for_all_items() -> None:
    """
    Recalculate ADU for all stock items so that Item.custom_adu matches
    the same horizon logic used in reports.

    Intended to be called from a daily scheduler event.
    """
    days = _get_horizon_days()
    if days <= 0:
        return

    end_date = today()
    start_date = add_days(end_date, -(days - 1))

    # Get total sales qty per item in the horizon
    rows = frappe.db.sql(
        """
        SELECT
            sii.item_code,
            COALESCE(SUM(sii.qty), 0) AS total_qty
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        INNER JOIN `tabItem` i ON i.name = sii.item_code
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND i.is_stock_item = 1
        GROUP BY sii.item_code
        """,
        (start_date, end_date),
        as_dict=True,
    )

    sales_map = {row.item_code: flt(row.total_qty) for row in rows}

    # Get all stock items so we also reset ADU to 0 when there is no sales in horizon
    all_items = frappe.get_all(
        "Item",
        filters={"is_stock_item": 1},
        pluck="name",
    )

    for item_code in all_items:
        total_qty = sales_map.get(item_code, 0.0)
        if days > 0 and total_qty > 0:
            adu_raw = total_qty / days
            adu_ceiled = int(math.ceil(adu_raw))
        else:
            adu_ceiled = 0

        frappe.db.set_value("Item", item_code, "custom_adu", adu_ceiled)






