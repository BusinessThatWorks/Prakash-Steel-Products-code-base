import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_item_insight_data(from_date=None, to_date=None, item_code=None, limit=50):
    """
    Fetch comprehensive item insight data including:
    - Item details
    - Production data (last production date and quantity)
    - Sales data (last sales party, quantity, rate, pending SO qty)
    - Purchase data (last purchase party, quantity, rate, pending PO qty)
    - Inventory data (warehouse-wise stock on hand)

    Note: Limits to 50 items by default for performance
    """

    # Build item filter
    item_filter = {"is_stock_item": 1}
    if item_code:
        item_filter["name"] = item_code
        limit = None  # No limit when specific item is requested

    # Get items - limited for performance on initial load
    items = frappe.get_all(
        "Item",
        filters=item_filter,
        fields=["name", "item_name", "item_code"],
        order_by="item_code",
        limit_page_length=int(limit) if limit else None,
    )

    if not items:
        return []

    result = []

    for item in items:
        item_code = item.name

        # Item Details
        item_data = {
            "item_code": item.item_code,
            "item_name": item.item_name or item.item_code,
        }

        # Production Data - Get last production from Hourly Production or Bright Bar Production
        production_data = get_last_production_data(item_code, from_date, to_date)
        item_data.update(production_data)

        # Sales Data
        sales_data = get_sales_data(item_code, from_date, to_date)
        item_data.update(sales_data)

        # Purchase Data
        purchase_data = get_purchase_data(item_code, from_date, to_date)
        item_data.update(purchase_data)

        # Inventory Data - Warehouse-wise stock
        inventory_data = get_inventory_data(item_code)
        item_data["warehouse_stock"] = inventory_data

        result.append(item_data)

    return result


def get_last_production_data(item_code, from_date, to_date):
    """Get last production date and quantity from Hourly Production or Bright Bar Production"""

    # Try Hourly Production first
    if from_date and to_date:
        hourly_prod = frappe.db.sql(
            """
			SELECT 
				production_date,
				finish_item_pcs as quantity
			FROM `tabHourly Production`
			WHERE finish_item = %s
				AND docstatus = 1
				AND production_date BETWEEN %s AND %s
			ORDER BY production_date DESC, creation DESC
			LIMIT 1
		""",
            (item_code, from_date, to_date),
            as_dict=True,
        )
    else:
        hourly_prod = frappe.db.sql(
            """
			SELECT 
				production_date,
				finish_item_pcs as quantity
			FROM `tabHourly Production`
			WHERE finish_item = %s
				AND docstatus = 1
			ORDER BY production_date DESC, creation DESC
			LIMIT 1
		""",
            (item_code,),
            as_dict=True,
        )

    if hourly_prod:
        return {
            "last_production_date": hourly_prod[0].production_date,
            "last_production_quantity": flt(hourly_prod[0].quantity, 2),
        }

    # Try Bright Bar Production (fields are on main table, not child table)
    if from_date and to_date:
        bright_bar_prod = frappe.db.sql(
            """
			SELECT 
				production_date,
				SUM(fg_weight) as quantity
			FROM `tabBright Bar Production`
			WHERE finished_good = %s
				AND docstatus = 1
				AND production_date BETWEEN %s AND %s
			GROUP BY production_date
			ORDER BY production_date DESC
			LIMIT 1
		""",
            (item_code, from_date, to_date),
            as_dict=True,
        )
    else:
        bright_bar_prod = frappe.db.sql(
            """
			SELECT 
				production_date,
				SUM(fg_weight) as quantity
			FROM `tabBright Bar Production`
			WHERE finished_good = %s
				AND docstatus = 1
			GROUP BY production_date
			ORDER BY production_date DESC
			LIMIT 1
		""",
            (item_code,),
            as_dict=True,
        )

    if bright_bar_prod:
        return {
            "last_production_date": bright_bar_prod[0].production_date,
            "last_production_quantity": flt(bright_bar_prod[0].quantity, 2),
        }

    return {"last_production_date": None, "last_production_quantity": 0}


def get_sales_data(item_code, from_date, to_date):
    """Get last sales party, quantity, rate and pending sales order quantity"""

    # Last Sales Invoice data
    if from_date and to_date:
        last_sales = frappe.db.sql(
            """
			SELECT 
				si.customer_name,
				sii.qty,
				sii.rate,
				si.posting_date
			FROM `tabSales Invoice Item` sii
			INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
			WHERE sii.item_code = %s
				AND si.docstatus = 1
				AND si.posting_date BETWEEN %s AND %s
			ORDER BY si.posting_date DESC, si.posting_time DESC, si.creation DESC
			LIMIT 1
		""",
            (item_code, from_date, to_date),
            as_dict=True,
        )
    else:
        last_sales = frappe.db.sql(
            """
			SELECT 
				si.customer_name,
				sii.qty,
				sii.rate,
				si.posting_date
			FROM `tabSales Invoice Item` sii
			INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
			WHERE sii.item_code = %s
				AND si.docstatus = 1
			ORDER BY si.posting_date DESC, si.posting_time DESC, si.creation DESC
			LIMIT 1
		""",
            (item_code,),
            as_dict=True,
        )

    last_sales_party = None
    last_sales_quantity = 0
    last_sales_rate = 0

    if last_sales:
        last_sales_party = last_sales[0].customer_name
        last_sales_quantity = flt(last_sales[0].qty, 2)
        last_sales_rate = flt(last_sales[0].rate, 2)

    # Pending Sales Order Quantity
    pending_so_qty = frappe.db.sql(
        """
		SELECT 
			SUM(soi.qty - IFNULL(soi.delivered_qty, 0)) as pending_qty
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE soi.item_code = %s
			AND so.status NOT IN ('Stopped', 'On Hold', 'Closed', 'Cancelled', 'Completed')
			AND so.docstatus = 1
			AND (soi.qty - IFNULL(soi.delivered_qty, 0)) > 0
	""",
        (item_code,),
        as_dict=True,
    )

    pending_sales_order_qty = (
        flt(pending_so_qty[0].pending_qty, 2)
        if pending_so_qty and pending_so_qty[0].pending_qty
        else 0
    )

    return {
        "last_sales_party": last_sales_party,
        "last_sales_quantity": last_sales_quantity,
        "last_sales_rate": last_sales_rate,
        "pending_sales_order_qty": pending_sales_order_qty,
    }


def get_purchase_data(item_code, from_date, to_date):
    """Get last purchase party, quantity, rate and pending purchase order quantity"""

    # Last Purchase Invoice data
    if from_date and to_date:
        last_purchase = frappe.db.sql(
            """
			SELECT 
				pi.supplier_name,
				pii.qty,
				pii.rate,
				pi.posting_date
			FROM `tabPurchase Invoice Item` pii
			INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
			WHERE pii.item_code = %s
				AND pi.docstatus = 1
				AND pi.posting_date BETWEEN %s AND %s
			ORDER BY pi.posting_date DESC, pi.posting_time DESC, pi.creation DESC
			LIMIT 1
		""",
            (item_code, from_date, to_date),
            as_dict=True,
        )
    else:
        last_purchase = frappe.db.sql(
            """
			SELECT 
				pi.supplier_name,
				pii.qty,
				pii.rate,
				pi.posting_date
			FROM `tabPurchase Invoice Item` pii
			INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
			WHERE pii.item_code = %s
				AND pi.docstatus = 1
			ORDER BY pi.posting_date DESC, pi.posting_time DESC, pi.creation DESC
			LIMIT 1
		""",
            (item_code,),
            as_dict=True,
        )

    last_purchase_party = None
    last_purchase_quantity = 0
    last_purchase_rate = 0

    if last_purchase:
        last_purchase_party = last_purchase[0].supplier_name
        last_purchase_quantity = flt(last_purchase[0].qty, 2)
        last_purchase_rate = flt(last_purchase[0].rate, 2)

    # Pending Purchase Order Quantity
    pending_po_qty = frappe.db.sql(
        """
		SELECT 
			SUM(poi.qty - IFNULL(poi.received_qty, 0)) as pending_qty
		FROM `tabPurchase Order Item` poi
		INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
		WHERE poi.item_code = %s
			AND po.status NOT IN ('Stopped', 'On Hold', 'Closed', 'Cancelled', 'Completed')
			AND po.docstatus = 1
			AND (poi.qty - IFNULL(poi.received_qty, 0)) > 0
	""",
        (item_code,),
        as_dict=True,
    )

    pending_purchase_order_qty = (
        flt(pending_po_qty[0].pending_qty, 2)
        if pending_po_qty and pending_po_qty[0].pending_qty
        else 0
    )

    return {
        "last_purchase_party": last_purchase_party,
        "last_purchase_quantity": last_purchase_quantity,
        "last_purchase_rate": last_purchase_rate,
        "pending_purchase_order_qty": pending_purchase_order_qty,
    }


def get_inventory_data(item_code):
    """Get warehouse-wise stock on hand"""

    # Exclude rejected warehouses
    excluded_warehouses = ["Rejected Warehouse"]

    warehouse_stock = frappe.db.sql(
        """
		SELECT 
			warehouse,
			SUM(actual_qty) as stock_qty
		FROM `tabBin`
		WHERE item_code = %s
			AND warehouse NOT IN %s
			AND actual_qty != 0
		GROUP BY warehouse
		ORDER BY warehouse
	""",
        (item_code, tuple(excluded_warehouses)),
        as_dict=True,
    )

    result = []
    for wh in warehouse_stock:
        result.append({"warehouse": wh.warehouse, "stock_qty": flt(wh.stock_qty, 2)})

    return result


@frappe.whitelist()
def search_items(query, limit=20):
    """
    Search for items by item code or item name
    Returns items with their name, item_name, and item_group
    """
    limit = int(limit)

    # If no query, return top items
    if not query or query.strip() == "":
        items = frappe.db.sql(
            """
			SELECT 
				name,
				item_name,
				item_group
			FROM `tabItem`
			WHERE is_stock_item = 1
			ORDER BY name
			LIMIT %(limit)s
		""",
            {"limit": limit},
            as_dict=True,
        )
    else:
        # Search by item code or item name
        items = frappe.db.sql(
            """
			SELECT 
				name,
				item_name,
				item_group
			FROM `tabItem`
			WHERE is_stock_item = 1
				AND (
					name LIKE %(query)s
					OR item_name LIKE %(query)s
				)
			ORDER BY 
				CASE 
					WHEN name LIKE %(exact_query)s THEN 1
					WHEN item_name LIKE %(exact_query)s THEN 2
					ELSE 3
				END,
				name
			LIMIT %(limit)s
		""",
            {"query": f"%{query}%", "exact_query": f"{query}%", "limit": limit},
            as_dict=True,
        )

    return items
