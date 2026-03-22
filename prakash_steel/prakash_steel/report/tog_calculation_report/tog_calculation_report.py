import math
from collections import defaultdict

import frappe
from frappe.utils import cint, flt, today, add_days

from prakash_steel.utils.lead_time import get_default_bom


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
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": "Parent Sell",
			"fieldname": "parent_sell",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": "Consumption",
			"fieldname": "consumption",
			"fieldtype": "Int",
			"width": 110,
			"hidden": 1,  # Not shown by default since it's not used in ADU calculation for all items; can be toggled on if needed
		},
		{
			"label": "ADU",
			"fieldname": "custom_adu",
			"fieldtype": "Int",
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
	# Number of days in horizon (based on ADU Horizon)
	days = _get_horizon_days()
	# Map of item_code -> total sales qty in horizon
	sales_qty_map = _get_sales_qty_by_item()
	# Map of item_code -> total consumption (filtered by same date range as sales)
	consumption_map = _get_consumption_by_item(days)

	parent_sell_map = _compute_parent_sell_map(sales_qty_map)

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

		# 1) Sell: live total sales qty in current horizon (integer)
		sell_qty = flt(sales_qty_map.get(item_code, 0.0))
		item["sell"] = int(sell_qty) if sell_qty else 0

		# 1b) Parent sell: demand on this item from exploding other items' sales through BOMs (ceiled int)
		ps = flt(parent_sell_map.get(item_code, 0.0))
		item["parent_sell"] = int(math.ceil(ps)) if ps > 0 else 0

		# 2) Consumption: live total consumption (integer)
		consumption_qty = flt(consumption_map.get(item_code, 0.0))
		item["consumption"] = int(consumption_qty) if consumption_qty else 0

		# 3) ADU: always recalculate from (Sell + Consumption) / days (ceiled to whole number)
		total_usage = sell_qty + consumption_qty
		if days > 0 and total_usage > 0:
			adu_raw = total_usage / days
			item["custom_adu"] = math.ceil(adu_raw)
		else:
			# If horizon not configured or no sales/consumption, set ADU to 0
			item["custom_adu"] = 0

		# 4) SD / COV placeholders (not yet implemented)
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


def _compute_parent_sell_map(sales_qty_map: dict[str, float]) -> dict[str, float]:
	"""
	For each invoiced item with sell qty > 0, explode through default BOMs.

	Per BOM row: child_need = incoming_qty * (bom.quantity / bom_item.qty).

	Parent sell for a component is the *cumulative* demand along the path from the
	sold item: sum of child_need at each hop (sold → … → this item). Multiple
	sales or multiple paths add together.

	Stop traversing when custom_item_type is 'rm' (case-insensitive); the RM line
	still receives the cumulative total for that path.

	Stored as floats; the report column uses ceil.
	"""
	acc = defaultdict(float)
	bom_doc_cache: dict[str, object] = {}
	default_bom_cache: dict[str, str | None] = {}
	rm_cache: dict[str, bool] = {}

	def _is_rm_stop(item_code: str) -> bool:
		if item_code not in rm_cache:
			raw = frappe.db.get_value("Item", item_code, "custom_item_type")
			rm_cache[item_code] = bool(raw and str(raw).strip().lower() == "rm")
		return rm_cache[item_code]

	def _get_bom_doc(bom_name: str):
		if bom_name not in bom_doc_cache:
			bom_doc_cache[bom_name] = frappe.get_doc("BOM", bom_name)
		return bom_doc_cache[bom_name]

	def _propagate(
		item_code: str, incoming_qty: float, visited: frozenset[str], path_cumulative: float
	) -> None:
		"""
		path_cumulative: sum of child_need for each hop from the sold root up to
		and including demand landing on item_code (incoming_qty is that landing qty).
		"""
		if not incoming_qty or item_code in visited:
			return
		if _is_rm_stop(item_code):
			return

		if item_code not in default_bom_cache:
			default_bom_cache[item_code] = get_default_bom(item_code)
		bom_name = default_bom_cache[item_code]
		if not bom_name:
			return

		bom_doc = _get_bom_doc(bom_name)
		fg_qty = flt(bom_doc.quantity)
		if fg_qty <= 0:
			return

		next_visited = visited | {item_code}

		for bom_item in bom_doc.items:
			child_code = bom_item.item_code
			child_line_qty = flt(bom_item.qty)
			if not child_code or child_line_qty <= 0:
				continue
			child_need = incoming_qty * (fg_qty / child_line_qty)
			path_total = path_cumulative + child_need
			acc[child_code] += path_total
			if _is_rm_stop(child_code):
				continue
			_propagate(child_code, child_need, next_visited, path_total)

	for sold_item, sell_qty in sales_qty_map.items():
		sq = flt(sell_qty)
		if sq <= 0:
			continue
		_propagate(sold_item, sq, frozenset(), 0.0)

	return dict(acc)


def _get_consumption_by_item(days: int) -> dict[str, float]:
	"""
	Return a mapping of item_code -> total consumption within the ADU horizon.

	Logic:
	- For items with item_type = "rb" or "bo": sum actual_rm_consumption from Bright Bar Production doctype
	- For items with item_type = "rm" or "traded": sum billet_weight from Billet Cutting doctype
	- Filtered by the same date range as sales (ADU horizon)
	"""
	consumption_map = {}

	if days <= 0:
		return consumption_map

	end_date = today()
	# Include "days" number of days including today
	start_date = add_days(end_date, -(days - 1))

	# Get consumption from Bright Bar Production for items with item_type = "rb" or "bo"

	bright_bar_rows = frappe.db.sql(
		"""
		SELECT
			bbp.raw_material AS item_code,
			COALESCE(SUM(bbp.actual_rm_consumption), 0) AS total_rm_consumption
		FROM `tabBright Bar Production` bbp
		INNER JOIN `tabItem` i ON i.name = bbp.raw_material
		WHERE
			bbp.docstatus = 1
			AND LOWER(i.custom_item_type) IN ('rb', 'bo')
			AND bbp.production_date BETWEEN %s AND %s
		GROUP BY bbp.raw_material
		""",
		(start_date, end_date),
		as_dict=True,
	)

	for row in bright_bar_rows:
		item_code = row.get("item_code")
		if item_code:
			consumption_map[item_code] = flt(row.get("total_rm_consumption", 0.0))

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
			AND LOWER(i.custom_item_type) IN ('rm', 'traded')
			AND bc.posting_date BETWEEN %s AND %s
		GROUP BY bc.billet_size
		""",
		(start_date, end_date),
		as_dict=True,
	)

	for row in billet_cutting_rows:
		item_code = row.get("item_code")
		if item_code:
			# If item already has consumption from Bright Bar Production, add to it
			# Otherwise, set it
			current_consumption = consumption_map.get(item_code, 0.0)
			consumption_map[item_code] = current_consumption + flt(row.get("total_billet_weight", 0.0))

	return consumption_map
