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
			"label": "Warehouse Name",
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 300,
		},
		{
			"label": "Stock Qty",
			"fieldname": "stock_qty",
			"fieldtype": "Float",
			"width": 150,
		},
	]


def get_data(filters):
	where_conditions = []
	params = {}

	# Apply warehouse filter if provided
	if filters.get("warehouse"):
		where_conditions.append("b.warehouse = %(warehouse)s")
		params["warehouse"] = filters.get("warehouse")

	where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

	# Query to get sum of actual_qty from Bin table grouped by warehouse
	# actual_qty is the current stock quantity in the Bin table
	# Shows all warehouses that have items, even if stock is zero
	rows = frappe.db.sql(
		f"""
		SELECT
			b.warehouse,
			COALESCE(SUM(b.actual_qty), 0) AS stock_qty
		FROM `tabBin` b
		WHERE {where_clause}
		GROUP BY b.warehouse
		ORDER BY b.warehouse
		""",
		params,
		as_dict=True,
	)

	# Format the data
	for row in rows:
		row["stock_qty"] = float(row.get("stock_qty") or 0)

	return rows
