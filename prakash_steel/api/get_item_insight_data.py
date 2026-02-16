import json
from io import BytesIO
from typing import Any

import frappe
from frappe.utils import flt
from frappe.utils.file_manager import save_file
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def get_item_insight_data(
    from_date=None,
    to_date=None,
    item_code=None,
    item_grade=None,
    category_name=None,
    description_code=None,
    limit=50,
):
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
    # Note: use AND conditions between all filters
    item_filter: dict[str, object] = {"is_stock_item": 1}

    if item_code:
        # When specific item code is provided, prioritize it
        item_filter["name"] = item_code
        limit = None  # No limit when specific item is requested

    # Item Grade filter (custom field on Item)
    if item_grade:
        # Item.custom_grade is a Link to "Item Grade"
        item_filter["custom_grade"] = item_grade

    # Category Name filter (custom field on Item)
    if category_name:
        # Item.custom_category_name is a Link to "Item Category"
        item_filter["custom_category_name"] = category_name

    # Description Code filter (custom field on Item)
    if description_code:
        # Item.custom_desc_code is a Select field storing description code
        item_filter["custom_desc_code"] = description_code

    # Get items - limited for performance on initial load
    items = frappe.get_all(
        "Item",
        filters=item_filter,
        fields=[
            "name",
            "item_name",
            "item_code",
            "custom_grade as item_grade",
            "custom_category_name as category_name",
        ],
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

        # Include static attributes used for filtering (optional, helpful for debugging/UI)
        if getattr(item, "item_grade", None):
            item_data["item_grade"] = item.item_grade
        if getattr(item, "category_name", None):
            item_data["category_name"] = item.category_name

        # Production Data - Get last production from Hourly Production or Bright Bar Production
        production_data = get_last_production_data(item_code, from_date, to_date)
        item_data.update(production_data)

        # Sales Data
        sales_data = get_sales_data(item_code, from_date, to_date)
        item_data.update(sales_data)

        # Purchase Data
        purchase_data = get_purchase_data(item_code, from_date, to_date)
        item_data.update(purchase_data)

        # Inventory Data - Warehouse-wise stock and committed stock
        inventory_data = get_inventory_data(item_code)
        item_data["warehouse_stock"] = inventory_data

        # Calculate total stock on hand and total committed stock
        total_stock_on_hand = sum(
            flt(wh.get("stock_qty", 0), 2) for wh in inventory_data
        )
        total_committed_stock = sum(
            flt(wh.get("committed_stock", 0), 2) for wh in inventory_data
        )

        item_data["total_stock_on_hand"] = flt(total_stock_on_hand, 2)
        item_data["committed_stock"] = flt(total_committed_stock, 2)
        item_data["projected_qty"] = flt(total_stock_on_hand - total_committed_stock, 2)

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
    last_sales_date = None

    if last_sales:
        last_sales_party = last_sales[0].customer_name
        last_sales_quantity = flt(last_sales[0].qty, 2)
        last_sales_rate = flt(last_sales[0].rate, 2)
        last_sales_date = last_sales[0].posting_date

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
        "last_sales_date": last_sales_date,
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
    last_purchase_date = None

    if last_purchase:
        last_purchase_party = last_purchase[0].supplier_name
        last_purchase_quantity = flt(last_purchase[0].qty, 2)
        last_purchase_rate = flt(last_purchase[0].rate, 2)
        last_purchase_date = last_purchase[0].posting_date

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
        "last_purchase_date": last_purchase_date,
        "pending_purchase_order_qty": pending_purchase_order_qty,
    }


def get_inventory_data(item_code):
    """Get warehouse-wise stock on hand and committed stock"""

    # Exclude rejected warehouses
    excluded_warehouses = ["Rejected Warehouse"]

    warehouse_stock = frappe.db.sql(
        """
		SELECT 
			warehouse,
			SUM(actual_qty) as stock_qty,
			SUM(IFNULL(reserved_qty, 0)) as committed_stock
		FROM `tabBin`
		WHERE item_code = %s
			AND warehouse NOT IN %s
			AND (actual_qty != 0 OR IFNULL(reserved_qty, 0) != 0)
		GROUP BY warehouse
		ORDER BY warehouse
	""",
        (item_code, tuple(excluded_warehouses)),
        as_dict=True,
    )

    result = []
    for wh in warehouse_stock:
        stock_qty = flt(wh.stock_qty, 2)
        committed_stock = flt(wh.committed_stock, 2)
        projected_qty = flt(stock_qty - committed_stock, 2)
        result.append(
            {
                "warehouse": wh.warehouse,
                "stock_qty": stock_qty,
                "committed_stock": committed_stock,
                "projected_qty": projected_qty,
            }
        )

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


@frappe.whitelist()
def search_item_categories(
    doctype: str,
    txt: str,
    searchfield: str,
    start: int,
    page_len: int,
    filters: dict[str, Any] | None = None,
):
    """
    Link field query: return Item Categories restricted to Items having the given grade.

    This is used to populate the Category Name suggestions based on the selected Item Grade.
    """
    filters = filters or {}
    item_grade = filters.get("item_grade")

    if not item_grade:
        # If no grade selected, fall back to standard Item Category search
        return frappe.db.sql(
            """
			SELECT 
				name,
				category_name
			FROM `tabItem Category`
			WHERE
				(name LIKE %(txt)s OR category_name LIKE %(txt)s)
			ORDER BY name
			LIMIT %(page_len)s OFFSET %(start)s
		""",
            {
                "txt": f"%{txt}%",
                "page_len": page_len,
                "start": start,
            },
        )

    return frappe.db.sql(
        """
		SELECT DISTINCT
			ic.name,
			ic.category_name
		FROM `tabItem Category` ic
		INNER JOIN `tabItem` i ON i.custom_category_name = ic.name
		WHERE
			i.custom_grade = %(item_grade)s
			AND (
				ic.name LIKE %(txt)s
				OR ic.category_name LIKE %(txt)s
			)
		ORDER BY ic.name
		LIMIT %(page_len)s OFFSET %(start)s
	""",
        {
            "item_grade": item_grade,
            "txt": f"%{txt}%",
            "page_len": page_len,
            "start": start,
        },
    )


@frappe.whitelist()
def export_item_insight_excel(filters: str | None = None) -> dict[str, Any]:
    """Export item insight data to Excel and return file URL."""

    filters_dict: dict[str, Any] = {}
    if filters:
        try:
            filters_dict = json.loads(filters)
        except Exception:
            frappe.throw("Invalid filters JSON")

    data = get_item_insight_data(**filters_dict)

    if not data:
        frappe.throw("No data to export")

    # Define column headers
    column_labels = [
        "Item Code",
        "Item Name",
        "Item Grade",
        "Category Name",
        "Last Production Date",
        "Last Production Qty",
        "Last Sales Party",
        "Last Sales Date",
        "Last Sales Qty",
        "Last Sales Rate",
        "Pending SO Qty",
        "Last Purchase Party",
        "Last Purchase Date",
        "Last Purchase Qty",
        "Last Purchase Rate",
        "Pending PO Qty",
        "Warehouse",
        "Stock Qty",
        "Committed Stock",
        "Projected Qty",
        "Total Stock On Hand",
    ]

    # Flatten data to include warehouse rows
    rows = []
    for item in data:
        warehouse_stock = item.get("warehouse_stock", [])

        if warehouse_stock:
            # Create a row for each warehouse
            for wh in warehouse_stock:
                row = [
                    item.get("item_code", ""),
                    item.get("item_name", ""),
                    item.get("item_grade", ""),
                    item.get("category_name", ""),
                    (
                        frappe.format(
                            item.get("last_production_date"), {"fieldtype": "Date"}
                        )
                        if item.get("last_production_date")
                        else ""
                    ),
                    flt(item.get("last_production_quantity", 0), 2),
                    item.get("last_sales_party", ""),
                    (
                        frappe.format(
                            item.get("last_sales_date"), {"fieldtype": "Date"}
                        )
                        if item.get("last_sales_date")
                        else ""
                    ),
                    flt(item.get("last_sales_quantity", 0), 2),
                    flt(item.get("last_sales_rate", 0), 2),
                    flt(item.get("pending_sales_order_qty", 0), 2),
                    item.get("last_purchase_party", ""),
                    (
                        frappe.format(
                            item.get("last_purchase_date"), {"fieldtype": "Date"}
                        )
                        if item.get("last_purchase_date")
                        else ""
                    ),
                    flt(item.get("last_purchase_quantity", 0), 2),
                    flt(item.get("last_purchase_rate", 0), 2),
                    flt(item.get("pending_purchase_order_qty", 0), 2),
                    wh.get("warehouse", ""),
                    flt(wh.get("stock_qty", 0), 2),
                    flt(wh.get("committed_stock", 0), 2),
                    flt(wh.get("projected_qty", 0), 2),
                    flt(item.get("total_stock_on_hand", 0), 2),
                ]
                rows.append(row)
        else:
            # No warehouses, create single row with empty warehouse fields
            row = [
                item.get("item_code", ""),
                item.get("item_name", ""),
                item.get("item_grade", ""),
                item.get("category_name", ""),
                (
                    frappe.format(
                        item.get("last_production_date"), {"fieldtype": "Date"}
                    )
                    if item.get("last_production_date")
                    else ""
                ),
                flt(item.get("last_production_quantity", 0), 2),
                item.get("last_sales_party", ""),
                (
                    frappe.format(item.get("last_sales_date"), {"fieldtype": "Date"})
                    if item.get("last_sales_date")
                    else ""
                ),
                flt(item.get("last_sales_quantity", 0), 2),
                flt(item.get("last_sales_rate", 0), 2),
                flt(item.get("pending_sales_order_qty", 0), 2),
                item.get("last_purchase_party", ""),
                (
                    frappe.format(item.get("last_purchase_date"), {"fieldtype": "Date"})
                    if item.get("last_purchase_date")
                    else ""
                ),
                flt(item.get("last_purchase_quantity", 0), 2),
                flt(item.get("last_purchase_rate", 0), 2),
                flt(item.get("pending_purchase_order_qty", 0), 2),
                "",  # warehouse
                "",  # stock_qty
                "",  # committed_stock
                "",  # projected_qty
                flt(item.get("total_stock_on_hand", 0), 2),
            ]
            rows.append(row)

    # Build the xlsx file with header row + data rows using openpyxl (built-in Frappe dep)
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Item Insight"

    # Header style
    header_font = Font(bold=True)
    header_fill = PatternFill(
        start_color="D7E4BC", end_color="D7E4BC", fill_type="solid"
    )
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Write headers
    for col_num, header in enumerate(column_labels, start=1):
        cell = worksheet.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

    # Write data rows
    for row_num, row_data in enumerate(rows, start=2):
        for col_num, cell_value in enumerate(row_data, start=1):
            worksheet.cell(row=row_num, column=col_num, value=cell_value)

    xlsx_buffer = BytesIO()
    workbook.save(xlsx_buffer)
    xlsx_buffer.seek(0)

    file_name = "Item Insight Dashboard.xlsx"
    saved_file = save_file(
        fname=file_name,
        content=xlsx_buffer.getvalue(),
        dt=None,
        dn=None,
        is_private=1,
    )

    return {"file_url": saved_file.file_url}


@frappe.whitelist()
def export_item_insight_pdf(filters: str | None = None) -> dict[str, Any]:
    """Export item insight data to PDF and return file URL."""

    filters_dict: dict[str, Any] = {}
    if filters:
        try:
            filters_dict = json.loads(filters)
        except Exception:
            frappe.throw("Invalid filters JSON")

    data = get_item_insight_data(**filters_dict)

    if not data:
        frappe.throw("No data to export")

    # Build simple HTML table for PDF
    columns = [
        ("item_code", "Item Code"),
        ("item_name", "Item Name"),
        ("item_grade", "Item Grade"),
        ("category_name", "Category Name"),
        ("last_production_date", "Last Production Date"),
        ("last_production_quantity", "Last Production Qty"),
        ("last_sales_party", "Last Sales Party"),
        ("last_sales_date", "Last Sales Date"),
        ("last_sales_quantity", "Last Sales Qty"),
        ("last_sales_rate", "Last Sales Rate"),
        ("pending_sales_order_qty", "Pending SO Qty"),
        ("last_purchase_party", "Last Purchase Party"),
        ("last_purchase_date", "Last Purchase Date"),
        ("last_purchase_quantity", "Last Purchase Qty"),
        ("last_purchase_rate", "Last Purchase Rate"),
        ("pending_purchase_order_qty", "Pending PO Qty"),
        ("committed_stock", "Committed Stock"),
        ("projected_qty", "Projected Qty"),
        ("total_stock_on_hand", "Total Stock On Hand"),
    ]

    header_html = "".join(f"<th>{frappe._(label)}</th>" for _field, label in columns)

    body_rows = []
    for row in data:
        cells = []
        for field, _label in columns:
            value = row.get(field)
            cells.append(f"<td>{frappe.format(value)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    html = f"""
        <h3 style="text-align:center;">Item Insight Dashboard</h3>
        <table class="table table-bordered" style="width:100%;border-collapse:collapse;font-size:9pt;">
            <thead>
                <tr>{header_html}</tr>
            </thead>
            <tbody>
                {''.join(body_rows)}
            </tbody>
        </table>
    """

    pdf_content = get_pdf(html)

    file_name = "Item Insight Dashboard.pdf"
    saved_file = save_file(
        fname=file_name,
        content=pdf_content,
        dt=None,
        dn=None,
        is_private=1,
    )

    return {"file_url": saved_file.file_url}
