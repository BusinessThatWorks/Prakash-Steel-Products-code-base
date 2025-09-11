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

        total_qty = frappe.db.sql("""
            SELECT SUM(actual_qty) 
            FROM `tabBin`
            WHERE item_code=%s AND warehouse NOT IN %s
        """, (item_code, tuple(excluded_warehouses)), as_dict=True)

        available_qty = total_qty[0]['SUM(actual_qty)'] or 0
        return available_qty

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_available_stock_error")
        return 0