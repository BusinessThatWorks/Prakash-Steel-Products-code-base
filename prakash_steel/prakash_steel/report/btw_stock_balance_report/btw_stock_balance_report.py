# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)

	# If user selected a "color filter", apply it here
	if filters.get("color_filter"):
		data = [
			row for row in data if row.get("colour", "").lower() == filters.get("color_filter", "").lower()
		]

	return columns, data


def get_columns():
	"""Define report columns - BTW Item Name is added before Item Name"""
	return [
		{
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{
			"label": "BTW Item Name",
			"fieldname": "btw_item_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": "Colour",
			"fieldname": "colour",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": "Item Group",
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 120,
		},
		{
			"label": "Warehouse",
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120,
		},
		{
			"label": "Stock UOM",
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 100,
		},
		{
			"label": "Balance Qty",
			"fieldname": "bal_qty",
			"fieldtype": "Float",
			"width": 100,
			"precision": 2,
		},
		{
			"label": "Valuation Rate",
			"fieldname": "valuation_rate",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency",
		},
		{
			"label": "Stock Value",
			"fieldname": "stock_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency",
		},
		{
			"label": "Buffer",
			"fieldname": "buffer",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": "SKU Type",
			"fieldname": "sku_type",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Recommendation",
			"fieldname": "purchase_order_recommendation",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": "Top of Green",
			"fieldname": "top_of_green",
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Top of Yellow",
			"fieldname": "top_of_yellow",
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Top of Red",
			"fieldname": "top_of_red",
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Lead Time",
			"fieldname": "lead_time",
			"fieldtype": "Float",
			"width": 100,
			"precision": 2,
		},
		{
			"label": "Replenishment Lead Time",
			"fieldname": "replenishment_lead_time",
			"fieldtype": "Float",
			"width": 150,
			"precision": 2,
		},
	]


def calculate_colour(row):
	"""Calculate colour based on buffer status and balance quantity"""
	buffer = row.get("buffer")
	bal_qty = flt(row.get("bal_qty") or 0)

	# Check if item is non-buffer
	buffer_str = str(buffer).strip() if buffer else ""
	if not buffer or buffer_str.lower() == "non buffer" or buffer_str == "":
		return "normal"

	# Item is buffer - check balance quantity against thresholds
	top_of_green = flt(row.get("top_of_green") or 0)
	top_of_yellow = flt(row.get("top_of_yellow") or 0)
	top_of_red = flt(row.get("top_of_red") or 0)

	if bal_qty == 0:
		return "black"
	elif bal_qty > top_of_green:
		return "white"
	elif bal_qty > top_of_yellow and bal_qty <= top_of_green:
		return "green"
	elif bal_qty > top_of_red and bal_qty <= top_of_yellow:
		return "yellow"
	elif bal_qty >= 1 and bal_qty <= top_of_red:
		return "red"
	else:
		return "normal"


def get_data(filters):
	"""Get stock balance data with BTW Item Name from BTW Item Properties doctype"""
	where_conditions = []
	params = {}

	# Apply filters
	if filters.get("btw_item_code"):
		# Filter by BTW Item Properties document name
		where_conditions.append("btw.name = %(btw_item_code)s")
		params["btw_item_code"] = filters.get("btw_item_code")

	if filters.get("item_code"):
		where_conditions.append("b.item_code = %(item_code)s")
		params["item_code"] = filters.get("item_code")

	if filters.get("item_group"):
		where_conditions.append("i.item_group = %(item_group)s")
		params["item_group"] = filters.get("item_group")

	if filters.get("warehouse"):
		where_conditions.append("b.warehouse = %(warehouse)s")
		params["warehouse"] = filters.get("warehouse")

	if filters.get("company"):
		where_conditions.append("w.company = %(company)s")
		params["company"] = filters.get("company")

	# Only show active items
	where_conditions.append("i.disabled = 0")

	where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

	# Check if include_zero_stock is set
	having_clause = ""
	if not filters.get("include_zero_stock"):
		having_clause = "HAVING SUM(b.actual_qty) != 0"

	# Query to get stock balance with BTW Item Name
	# Join with BTW Item Properties to get btw_item_name
	rows = frappe.db.sql(
		f"""
		SELECT
			b.item_code,
			COALESCE(btw.btw_item_name, '') AS btw_item_name,
			i.item_name,
			i.item_group,
			b.warehouse,
			i.stock_uom,
			SUM(b.actual_qty) AS bal_qty,
			AVG(b.valuation_rate) AS valuation_rate,
			SUM(b.actual_qty * b.valuation_rate) AS stock_value,
			btw.buffer,
			btw.top_of_green,
			btw.top_of_yellow,
			btw.top_of_red,
			btw.lead_time,
			btw.replenishment_lead_time,
			btw.sku_type,
			btw.purchase_order_recommendation,
		FROM `tabBin` b
		INNER JOIN `tabItem` i ON i.name = b.item_code
		LEFT JOIN `tabWarehouse` w ON w.name = b.warehouse
		LEFT JOIN `tabBTW Item Properties` btw ON btw.erp_item_name = b.item_code
		WHERE {where_clause}
		GROUP BY b.item_code, b.warehouse
		{having_clause}
		ORDER BY b.item_code, b.warehouse
		""",
		params,
		as_dict=True,
	)

	# Format the data
	for row in rows:
		row["bal_qty"] = flt(row.get("bal_qty") or 0)
		row["valuation_rate"] = flt(row.get("valuation_rate") or 0)
		row["stock_value"] = flt(row.get("stock_value") or 0)
		row["btw_item_name"] = row.get("btw_item_name") or ""
		row["buffer"] = row.get("buffer")  # Keep as is to check for "non buffer" string
		row["top_of_green"] = flt(row.get("top_of_green") or 0)
		row["top_of_yellow"] = flt(row.get("top_of_yellow") or 0)
		row["top_of_red"] = flt(row.get("top_of_red") or 0)
		row["lead_time"] = flt(row.get("lead_time") or 0)
		row["replenishment_lead_time"] = flt(row.get("replenishment_lead_time") or 0)

		# Calculate colour
		row["colour"] = calculate_colour(row)

	return rows
