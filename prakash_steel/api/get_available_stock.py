import frappe

@frappe.whitelist()
def get_available_stock(item_code):
    """
    Fetch total available stock from Bin table excluding rejected warehouses.
    Returns available quantity in KG
    """
    try:
        # Replace with your actual warehouse names to exclude
        excluded_warehouses = ["Rejected Warehouse"]

        total_qty = frappe.db.sql(
            """
            SELECT SUM(actual_qty) 
            FROM `tabBin`
            WHERE item_code=%s AND warehouse NOT IN %s
        """,
            (item_code, tuple(excluded_warehouses)),
            as_dict=True,
        )

        available_qty = total_qty[0]["SUM(actual_qty)"] or 0
        return available_qty

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_available_stock_error")
        return 0


@frappe.whitelist()
def get_available_stock_for_warehouse(item_code, warehouse):
    """
    Fetch available stock for an Item in a specific Warehouse from Bin table.
    Returns available quantity in KG.
    """
    try:
        if not item_code or not warehouse:
            return 0

        # Exclude any special/rejected warehouses if needed
        excluded_warehouses = ["Rejected Warehouse"]

        total_qty = frappe.db.sql(
            """
            SELECT SUM(actual_qty) AS qty
            FROM `tabBin`
            WHERE item_code=%s
              AND warehouse=%s
              AND warehouse NOT IN %s
        """,
            (item_code, warehouse, tuple(excluded_warehouses)),
            as_dict=True,
        )

        available_qty = (total_qty[0].get("qty") if total_qty and total_qty[0] else 0) or 0
        return available_qty

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_available_stock_for_warehouse_error")
        return 0