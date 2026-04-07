# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Item",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 160,
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
			"width": 140,
		},
		{
			"label": "Category Name",
			"fieldname": "category_name",
			"fieldtype": "Data",
			"width": 160,
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
			"fieldname": "balance_qty",
			"fieldtype": "Float",
			"width": 120,
		},
	]


def get_data(filters):
	where_conditions = []
	params = {}

	# Join with Item to ensure we only count active items
	# This matches the Stock Balance report logic
	where_conditions.append("i.disabled = 0")

	where_clause = " AND ".join(where_conditions)

	# Query to get sum of actual_qty from Bin table grouped by item across all warehouses
	# actual_qty from Bin should match bal_qty from Stock Balance report
	# Only include active items to match Stock Balance behavior
	having_clause = ""
	if not filters.get("include_zero_stock"):
		having_clause = "HAVING SUM(b.actual_qty) != 0"

	rows = frappe.db.sql(
		f"""
		SELECT
			b.item_code,
			i.item_name,
			i.item_group,
			i.stock_uom,
			COALESCE(i.custom_category_name, '') AS category_name,
			SUM(b.actual_qty) AS balance_qty
		FROM `tabBin` b
		INNER JOIN `tabItem` i ON i.name = b.item_code
		WHERE {where_clause}
		GROUP BY b.item_code
		{having_clause}
		ORDER BY b.item_code
		""",
		params,
		as_dict=True,
	)

	# Format the data
	for row in rows:
		row["balance_qty"] = float(row.get("balance_qty") or 0)

	return rows
