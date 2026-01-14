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
	print("[PLANNING DASHBOARD] ====== SKU TYPE CHART CALCULATION STARTING ======")
	
	if not filters:
		filters = {}

	# Get ALL buffer items - same as po_recomendation_for_psp report
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

	print(f"[PLANNING DASHBOARD] Found {len(items_data)} buffer items")

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
	print(f"[PLANNING DASHBOARD] Stock map loaded for {len(stock_map)} items")

	# Get qualified demand map (Open SO with delivery_date <= today) - same as po_recomendation_for_psp report
	qualified_demand_map = get_qualified_demand_map({})
	print(f"[PLANNING DASHBOARD] Qualified demand map loaded for {len(qualified_demand_map)} items")

	# Calculate SKU type for ALL items first (same as report does)
	# Then filter to only the SKU types we want for charts
	items_with_sku_type = []
	sku_type_counts = {}  # Count items by SKU type for debugging

	for item in items_data:
		item_code = item.item_code
		buffer_flag = item.get("buffer_flag") or "Non-Buffer"
		item_type = item.get("item_type")
		
		# Calculate SKU type exactly as report does (all items are buffer, so use "Buffer" flag)
		sku_type = calculate_sku_type("Buffer", item_type)
		
		# Count by SKU type
		if sku_type:
			sku_type_counts[sku_type] = sku_type_counts.get(sku_type, 0) + 1
		
		# Store item with its calculated SKU type
		items_with_sku_type.append({
			"item_code": item_code,
			"buffer_flag": buffer_flag,
			"item_type": item_type,
			"tog": item.get("tog", 0),
			"sku_type": sku_type
		})

	print(f"[PLANNING DASHBOARD] Items by SKU type: {sku_type_counts}")

	# Now filter to only the SKU types we want for charts: BBMTA, RBMTA, BOTA, RMTA, PTA
	# But handle RM buffer items: they calculate as PTA but should display as RMTA
	target_sku_types = ["BBMTA", "RBMTA", "BOTA", "RMTA", "PTA"]
	
	# Group items by SKU type and calculate on-hand status
	sku_type_data = {}
	item_calc_log = []  # Store calculation details for logging

	for item in items_with_sku_type:
		item_code = item["item_code"]
		buffer_flag = item["buffer_flag"]
		item_type = item["item_type"]
		sku_type = item["sku_type"]

		# Skip items without SKU type
		if not sku_type:
			continue

		# Map RM buffer items to RMTA for display (even though code logic uses PTA)
		# User wants to see RMTA in the dashboard
		display_sku_type = sku_type
		if sku_type == "PTA" and item_type == "RM" and buffer_flag == "Buffer":
			display_sku_type = "RMTA"

		# Only process target SKU types
		if display_sku_type not in target_sku_types:
			continue

		# Initialize SKU type if not exists
		if display_sku_type not in sku_type_data:
			sku_type_data[display_sku_type] = {
				"BLACK": {"count": 0, "items": []},
				"RED": {"count": 0, "items": []},
				"YELLOW": {"count": 0, "items": []},
				"GREEN": {"count": 0, "items": []},
				"WHITE": {"count": 0, "items": []},
			}

		# Calculate on-hand status and colour - EXACTLY as in po_recomendation_for_psp report
		on_hand_stock = flt(stock_map.get(item_code, 0))
		tog = flt(item["tog"])
		# Use qualified_demand directly (Open SO with delivery_date <= today) - same as po_recomendation_for_psp report
		qualify_demand = flt(qualified_demand_map.get(item_code, 0))

		# Calculate On Hand Status = on_hand_stock / (TOG + qualify_demand) (as ratio, then rounded up)
		# This matches the report exactly
		on_hand_status_value = None
		denominator = flt(tog) + flt(qualify_demand)
		if denominator > 0:
			on_hand_status_value = flt(on_hand_stock) / denominator
		else:
			# If denominator is 0, set to None (cannot calculate)
			on_hand_status_value = None

		numeric_status = None
		if on_hand_status_value is not None:
			numeric_status = math.ceil(on_hand_status_value)

		# Derive On Hand Colour from numeric status - EXACTLY as in report
		# 0% → BLACK, 1-34% → RED, 35-67% → YELLOW, 68-100% → GREEN, >100% → WHITE
		if numeric_status is None:
			on_hand_colour = None  # Report sets this to None, but we'll count as BLACK
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

		# Log calculation for this item
		calc_detail = (
			f"Item: {item_code} | SKU: {display_sku_type} (calc: {sku_type}) | "
			f"Stock: {on_hand_stock} | TOG: {tog} | Qualify_Demand: {qualify_demand} | "
			f"Denominator: {denominator} | On_Hand_Value: {on_hand_status_value} | "
			f"Numeric_Status: {numeric_status} | Colour: {on_hand_colour or 'BLACK (None)'}"
		)
		item_calc_log.append(calc_detail)

		# Count items by colour - ALWAYS count every item
		# If on_hand_colour is None (numeric_status is None), count as BLACK
		final_colour = on_hand_colour if on_hand_colour else "BLACK"
		if final_colour in sku_type_data[display_sku_type]:
			sku_type_data[display_sku_type][final_colour]["count"] += 1
			sku_type_data[display_sku_type][final_colour]["items"].append(item_code)


	# Count items by colour for each SKU type for debugging
	for sku_type, colour_data in sku_type_data.items():
		colour_counts = {colour: data["count"] for colour, data in colour_data.items()}
		print(f"[PLANNING DASHBOARD] {sku_type} colour counts: {colour_counts}")
		
		# Print all BLACK items for BBMTA
		if sku_type == "BBMTA" and "BLACK" in colour_data:
			black_items = colour_data["BLACK"]["items"]
			print(f"[PLANNING DASHBOARD] ====== BBMTA BLACK Items ({len(black_items)} total) ======")
			for idx, item_code in enumerate(black_items, 1):
				print(f"[PLANNING DASHBOARD] {idx}. {item_code}")
			print(f"[PLANNING DASHBOARD] ====== End BBMTA BLACK Items ======")
	
	# Log first 20 item calculations (to avoid too much logging)
	if item_calc_log:
		print(f"[PLANNING DASHBOARD] Sample item calculations (first 20):")
		for calc in item_calc_log[:20]:
			print(f"  {calc}")
		if len(item_calc_log) > 20:
			print(f"[PLANNING DASHBOARD] ... and {len(item_calc_log) - 20} more items")

	# Calculate percentages and format data for charts
	chart_data = {}

	for sku_type, colour_data in sku_type_data.items():
		# Calculate total items
		total_items = sum(colour["count"] for colour in colour_data.values())

		if total_items == 0:
			print(f"[PLANNING DASHBOARD] SKU {sku_type}: No items found")
			continue

		# Prepare chart data
		chart_data[sku_type] = {"total_items": total_items, "colours": []}

		# Process each colour
		colour_summary = []
		for colour_name in ["BLACK", "RED", "YELLOW", "GREEN", "WHITE"]:
			count = colour_data[colour_name]["count"]
			if count > 0:
				percentage = (count / total_items) * 100
				chart_data[sku_type]["colours"].append(
					{"name": colour_name, "count": count, "percentage": round(percentage)}
				)
				colour_summary.append(f"{colour_name}: {count} items ({round(percentage)}%)")

		print(f"[PLANNING DASHBOARD] SKU {sku_type}: Total={total_items} | " + " | ".join(colour_summary))

	print(f"[PLANNING DASHBOARD] Final chart_data keys: {list(chart_data.keys())}")
	return chart_data


def get_qualified_demand_map(filters):
	"""Get qualified demand map - same as po_recomendation_for_psp report
	Qualified Demand = Open SO quantity where delivery_date <= today
	Open SO = qty - delivered_qty (quantity left to deliver)
	"""
	from frappe.utils import today

	today_date = today()

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
			AND IFNULL(soi.delivery_date, '1900-01-01') <= %s
		GROUP BY
			soi.item_code
		""",
		(today_date,),
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

	print(f"[PLANNING DASHBOARD] ====== PENDING SO CHART CALCULATION STARTING (today: {today()}) ======")

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

	print(f"[PLANNING DASHBOARD] Found {len(so_data)} sales orders")

	if not so_data:
		return {"total_orders": 0, "colours": []}

	status_counts = {"BLACK": 0, "RED": 0, "YELLOW": 0, "GREEN": 0, "WHITE": 0}
	so_calc_log = []  # Store calculation details for logging

	for so in so_data:
		delivery_date = so.get("delivery_date")
		transaction_date = so.get("date")
		so_name = so.get("sales_order")

		if not delivery_date or not transaction_date:
			status_counts["BLACK"] += 1
			so_calc_log.append(f"SO: {so_name} | Missing dates → BLACK")
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

		# Log calculation for this SO
		calc_detail = (
			f"SO: {so_name} | Transaction: {transaction_date} | Delivery: {delivery_date} | "
			f"Delay_Days: {delay_days} | Remaining_Days: {remaining_days} | Lead_Time: {lead_time} | "
			f"Buffer_Status: {buffer_status} | Numeric_Status: {numeric_status} | Order_Status: {order_status}"
		)
		so_calc_log.append(calc_detail)

		if order_status in status_counts:
			status_counts[order_status] += 1

	# Log first 20 SO calculations
	if so_calc_log:
		print(f"[PLANNING DASHBOARD] Sample SO calculations (first 20):")
		for calc in so_calc_log[:20]:
			print(f"  {calc}")
		if len(so_calc_log) > 20:
			print(f"[PLANNING DASHBOARD] ... and {len(so_calc_log) - 20} more SOs")

	total_orders = sum(status_counts.values())
	if total_orders == 0:
		print(f"[PLANNING DASHBOARD] No orders found after processing")
		return {"total_orders": 0, "colours": []}

	colours = []
	status_summary = []
	for colour in ["BLACK", "RED", "YELLOW", "GREEN", "WHITE"]:
		count = status_counts[colour]
		if count:
			percentage = (count / total_orders) * 100
			colours.append(
				{
					"name": colour,
					"count": count,
					"percentage": round(percentage),
				}
			)
			status_summary.append(f"{colour}: {count} orders ({round(percentage)}%)")

	print(f"[PLANNING DASHBOARD] Pending SO Summary: Total={total_orders} | " + " | ".join(status_summary))

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
