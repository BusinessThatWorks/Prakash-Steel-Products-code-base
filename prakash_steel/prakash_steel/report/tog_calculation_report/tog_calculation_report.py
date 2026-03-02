import frappe
from frappe.utils import cint, flt, today, add_days


def execute(filters=None):
	"""
	Tog Calculation Report

	Columns required:
	- Item Code
	- Category Name (Item.custom_catagory_name)
	- Item Type (Item.custom_item_type)
	- Sell
	- Consumption
	- ADU (Item.custom_adu)
	- SD
	- COV

	Right now, only values coming from Item are populated.
	Other measure fields (sell, consumption, sd, cov) are left empty.
	"""

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	"""Report column definitions."""
	return [
		{
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{
			"label": "Category Name",
			"fieldname": "custom_category_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": "Item Type",
			"fieldname": "custom_item_type",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Sell",
			"fieldname": "sell",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": "Consumption",
			"fieldname": "consumption",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": "ADU",
			"fieldname": "custom_adu",
			"fieldtype": "Float",
			"width": 90,
		},
		{
			"label": "SD",
			"fieldname": "sd",
			"fieldtype": "Float",
			"width": 90,
		},
		{
			"label": "COV",
			"fieldname": "cov",
			"fieldtype": "Float",
			"width": 90,
		},
	]


def get_data(filters=None):
	"""
	Get data from Item doctype.

	Populates:
	- item_code (from Item.name)
	- custom_category_name
	- custom_item_type
	- custom_adu

	Leaves other fields (consumption, sd, cov) empty.
	"""
	# Map of item_code -> total sales qty in horizon
	sales_qty_map = _get_sales_qty_by_item()
	# Map of item_code -> total consumption
	consumption_map = _get_consumption_by_item()

	items = frappe.db.get_all(
		"Item",
		fields=[
			"name as item_code",
			"custom_category_name",
			"custom_item_type",
			"custom_adu",
		],
		# Adjust filters if you want to limit which items appear
		# Example: only stock items, not disabled
		# filters={"is_stock_item": 1, "disabled": 0},
	)

	# Populate measure columns
	for item in items:
		item_code = item.get("item_code")
		item["sell"] = flt(sales_qty_map.get(item_code, 0.0))
		item["consumption"] = flt(consumption_map.get(item_code, 0.0))
		item.setdefault("sd", None)
		item.setdefault("cov", None)

	return items


def _get_horizon_days() -> int:
	"""Return number of days to look back based on ADU Horizon single DocType."""
	horizon = frappe.get_single("ADU Horizon")
	weeks_raw = getattr(horizon, "week", None) or 0
	weeks = cint(weeks_raw) or 0
	if weeks <= 0:
		return 0
	return weeks * 7


def _get_sales_qty_by_item() -> dict[str, float]:
	"""
	Return a mapping of item_code -> total sales quantity
	within the ADU horizon (same range used in ADU calculation),
	but WITHOUT dividing by days/weeks.
	"""
	days = _get_horizon_days()
	if days <= 0:
		return {}

	end_date = today()
	# Include "days" number of days including today
	start_date = add_days(end_date, -(days - 1))

	rows = frappe.db.sql(
		"""
		SELECT
			sii.item_code,
			COALESCE(SUM(sii.qty), 0) AS total_qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %s AND %s
		GROUP BY sii.item_code
		""",
		(start_date, end_date),
		as_dict=True,
	)

	return {row["item_code"]: flt(row.get("total_qty", 0.0)) for row in rows}


def _get_consumption_by_item() -> dict[str, float]:
	"""
	Return a mapping of item_code -> total consumption.

	Logic:
	- For items with item_type = "rb": sum finish_weight from Finish Weight doctype
	- For items with item_type = "rm" or "traded": sum billet_weight from Billet Cutting doctype
	"""
	consumption_map = {}

	# Get consumption from Finish Weight for items with item_type = "rb"
	finish_weight_rows = frappe.db.sql(
		"""
		SELECT
			fw.item_code,
			COALESCE(SUM(fw.finish_weight), 0) AS total_finish_weight
		FROM `tabFinish Weight` fw
		INNER JOIN `tabItem` i ON i.name = fw.item_code
		WHERE
			fw.docstatus = 1
			AND i.custom_item_type = 'rb'
		GROUP BY fw.item_code
		""",
		as_dict=True,
	)

	for row in finish_weight_rows:
		item_code = row.get("item_code")
		if item_code:
			consumption_map[item_code] = flt(row.get("total_finish_weight", 0.0))

	# Get consumption from Billet Cutting for items with item_type = "rm" or "traded"
	billet_cutting_rows = frappe.db.sql(
		"""
		SELECT
			bc.billet_size AS item_code,
			COALESCE(SUM(bc.billet_weight), 0) AS total_billet_weight
		FROM `tabBillet Cutting` bc
		INNER JOIN `tabItem` i ON i.name = bc.billet_size
		WHERE
			bc.docstatus = 1
			AND i.custom_item_type IN ('rm', 'traded')
		GROUP BY bc.billet_size
		""",
		as_dict=True,
	)

	for row in billet_cutting_rows:
		item_code = row.get("item_code")
		if item_code:
			# If item already has consumption from Finish Weight, add to it
			# Otherwise, set it
			current_consumption = consumption_map.get(item_code, 0.0)
			consumption_map[item_code] = current_consumption + flt(row.get("total_billet_weight", 0.0))

	return consumption_map
