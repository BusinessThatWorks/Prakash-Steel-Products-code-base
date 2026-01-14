# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import math
import frappe
from frappe import _
from frappe.utils import flt


def calculate_sku_type(buffer_flag, item_type):
	"""
	Same mapping logic as calculate_sku_type in production_order_recomendation.py
	buffer_flag: 'Buffer' or other
	item_type: 'BB', 'RB', 'BO', 'RM', 'Traded'
	"""
	if not item_type:
		return None

	is_buffer = buffer_flag == "Buffer"

	if item_type == "BB":
		return "BBMTA" if is_buffer else "BBMTO"
	elif item_type == "RB":
		return "RBMTA" if is_buffer else "RBMTO"
	elif item_type == "BO":
		return "BOTA" if is_buffer else "BOTO"
	elif item_type == "RM":
		return "PTA" if is_buffer else "PTO"
	elif item_type == "Traded":
		return "TRMTA" if is_buffer else "TRMTO"

	return None


@frappe.whitelist()
def get_sku_type_on_hand_status(filters=None):
	"""
	Get on-hand status data grouped by SKU type for buffer items
	Returns data for pie charts showing distribution by color (BLACK, RED, YELLOW, GREEN, WHITE)

	For each SKU type:
	- Count items by on_hand_colour
	- Calculate percentage: (count_of_color / total_items) * 100
	- Return data in format suitable for pie charts
	"""
	if not filters:
		filters = {}

	# Get all buffer items
	items_data = frappe.db.sql(
		"""
		SELECT
			i.name as item_code,
			i.custom_buffer_flag as buffer_flag,
			i.custom_item_type as item_type,
			i.safety_stock as tog
		FROM
			`tabItem` i
		WHERE
			i.custom_buffer_flag = 'Buffer'
		""",
		as_dict=1,
	)

	if not items_data:
		return {}

	# Get stock for all items
	item_codes = [item.item_code for item in items_data]
	if len(item_codes) == 1:
		item_codes_tuple = (item_codes[0],)
	else:
		item_codes_tuple = tuple(item_codes)

	stock_data = frappe.db.sql(
		"""
		SELECT item_code, SUM(actual_qty) as stock
		FROM `tabBin`
		WHERE item_code IN %s
		GROUP BY item_code
		""",
		(item_codes_tuple,),
		as_dict=True,
	)

	stock_map = {d.item_code: flt(d.stock) for d in stock_data}

	# Get sales order qty map (all-time, no date filter for now)
	so_qty_map = get_sales_order_qty_map({})

	# Group items by SKU type and calculate on-hand status
	sku_type_data = {}

	for item in items_data:
		item_code = item.item_code
		buffer_flag = item.get("buffer_flag") or "Non-Buffer"
		item_type = item.get("item_type")
		sku_type = calculate_sku_type(buffer_flag, item_type)

		if not sku_type:
			continue

		# Map RM buffer items to RMTA for display (even though code logic uses PTA)
		# User wants to see RMTA in the dashboard
		if sku_type == "PTA" and item_type == "RM" and buffer_flag == "Buffer":
			sku_type = "RMTA"

		# Only process BBMTA, RBMTA, BOTA, RMTA, PTA
		if sku_type not in ["BBMTA", "RBMTA", "BOTA", "RMTA", "PTA"]:
			continue

		# Initialize SKU type if not exists
		if sku_type not in sku_type_data:
			sku_type_data[sku_type] = {
				"BLACK": {"count": 0, "items": []},
				"RED": {"count": 0, "items": []},
				"YELLOW": {"count": 0, "items": []},
				"GREEN": {"count": 0, "items": []},
				"WHITE": {"count": 0, "items": []},
			}

		# Calculate on-hand status and colour
		on_hand_stock = flt(stock_map.get(item_code, 0))
		tog = flt(item.get("tog", 0))
		so_qty = flt(so_qty_map.get(item_code, 0))

		# Calculate qualify_demand for buffer items
		if tog > 0 and so_qty >= (tog * 0.5):
			qualify_demand = so_qty
		else:
			qualify_demand = 0

		# Calculate On Hand Status = (on_hand_stock / (TOG + qualify_demand)) * 100
		on_hand_status_percentage = None
		denominator = tog + qualify_demand
		if denominator > 0:
			on_hand_status_percentage = (on_hand_stock / denominator) * 100

		numeric_status = None
		if on_hand_status_percentage is not None:
			numeric_status = math.ceil(on_hand_status_percentage)

		# Derive On Hand Colour from numeric status
		# 0% → BLACK, 1-34% → RED, 35-67% → YELLOW, 68-100% → GREEN, >100% → WHITE
		if numeric_status is None:
			on_hand_colour = None
		elif numeric_status == 0:
			on_hand_colour = "BLACK"
		elif 1 <= numeric_status <= 34:
			on_hand_colour = "RED"
		elif 35 <= numeric_status <= 67:
			on_hand_colour = "YELLOW"
		elif 68 <= numeric_status <= 100:
			on_hand_colour = "GREEN"
		else:  # > 100
			on_hand_colour = "WHITE"

		# Count items by colour
		if on_hand_colour and on_hand_colour in sku_type_data[sku_type]:
			sku_type_data[sku_type][on_hand_colour]["count"] += 1
			sku_type_data[sku_type][on_hand_colour]["items"].append(item_code)

	# Calculate percentages and format data for charts
	chart_data = {}

	for sku_type, colour_data in sku_type_data.items():
		# Calculate total items
		total_items = sum(colour["count"] for colour in colour_data.values())

		if total_items == 0:
			continue

		# Prepare chart data
		chart_data[sku_type] = {"total_items": total_items, "colours": []}

		# Process each colour
		for colour_name in ["BLACK", "RED", "YELLOW", "GREEN", "WHITE"]:
			count = colour_data[colour_name]["count"]
			if count > 0:
				percentage = (count / total_items) * 100
				chart_data[sku_type]["colours"].append(
					{"name": colour_name, "count": count, "percentage": round(percentage, 2)}
				)

	return chart_data


def get_sales_order_qty_map(filters):
	"""Get sales order qty map - all-time data for buffer items"""
	so_rows = frappe.db.sql(
		"""
		SELECT
			soi.item_code,
			SUM(soi.qty - IFNULL(soi.delivered_qty, 0)) as so_qty
		FROM
			`tabSales Order` so
		INNER JOIN
			`tabSales Order Item` soi ON soi.parent = so.name
		WHERE
			so.status NOT IN ('Stopped', 'On Hold', 'Closed', 'Cancelled', 'Completed')
			AND so.docstatus = 1
		GROUP BY
			soi.item_code
		""",
		as_dict=True,
	)

	return {d.item_code: flt(d.so_qty) for d in so_rows}


@frappe.whitelist()
def get_pending_so_status():
	"""
	Summary for Pending SO pie chart.
	All sales orders with status = 'To Deliver and Bill' till today.
	We calculate order_status using the same buffer logic as open_so_analysis
	(but at SO header level).
	"""
	from frappe.utils import date_diff, today

	so_data = frappe.db.sql(
		"""
		SELECT
			so.name as sales_order,
			so.transaction_date as date,
			MIN(soi.delivery_date) as delivery_date
		FROM
			`tabSales Order` so
		INNER JOIN
			`tabSales Order Item` soi ON soi.parent = so.name
		WHERE
			so.status = 'To Deliver and Bill'
			AND so.status NOT IN ('Stopped', 'On Hold', 'Closed', 'Cancelled')
			AND so.docstatus = 1
			AND (soi.qty - IFNULL(soi.delivered_qty, 0)) > 0
			AND so.transaction_date <= %s
		GROUP BY
			so.name, so.transaction_date
		""",
		(today(),),
		as_dict=1,
	)

	if not so_data:
		return {"total_orders": 0, "colours": []}

	status_counts = {"BLACK": 0, "RED": 0, "YELLOW": 0, "GREEN": 0, "WHITE": 0}

	for so in so_data:
		delivery_date = so.get("delivery_date")
		transaction_date = so.get("date")

		if not delivery_date or not transaction_date:
			status_counts["BLACK"] += 1
			continue

		delay_days = date_diff(today(), delivery_date)
		remaining_days = -flt(delay_days)
		lead_time = date_diff(delivery_date, transaction_date)

		buffer_status = None
		if remaining_days is not None:
			if flt(remaining_days) == 0:
				buffer_status = 0
			elif lead_time and lead_time > 0:
				buffer_status = (flt(remaining_days) / flt(lead_time)) * 100
			else:
				buffer_status = flt(remaining_days) * 100

		numeric_status = None
		if buffer_status is not None:
			numeric_status = math.ceil(buffer_status)

		if numeric_status is None:
			order_status = "BLACK"
		elif numeric_status < 0:
			order_status = "BLACK"
		elif numeric_status == 0:
			order_status = "RED"
		elif 1 <= numeric_status <= 34:
			order_status = "RED"
		elif 35 <= numeric_status <= 67:
			order_status = "YELLOW"
		elif 68 <= numeric_status <= 100:
			order_status = "GREEN"
		else:
			order_status = "WHITE"

		if order_status in status_counts:
			status_counts[order_status] += 1

	total_orders = sum(status_counts.values())
	if total_orders == 0:
		return {"total_orders": 0, "colours": []}

	colours = []
	for colour in ["BLACK", "RED", "YELLOW", "GREEN", "WHITE"]:
		count = status_counts[colour]
		if count:
			percentage = (count / total_orders) * 100
			colours.append(
				{
					"name": colour,
					"count": count,
					"percentage": round(percentage, 2),
				}
			)

	return {"total_orders": total_orders, "colours": colours}


@frappe.whitelist()
def get_open_po_status():
	"""
	Placeholder for Open PO pie chart.
	For now: single black slice = 100%.
	"""
	return {
		"total_orders": 1,
		"colours": [
			{
				"name": "BLACK",
				"count": 1,
				"percentage": 100.0,
			}
		],
	}
