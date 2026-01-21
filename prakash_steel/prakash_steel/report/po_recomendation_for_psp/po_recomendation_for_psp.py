# //psp production order py jan 19 21.13


# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import math
import frappe
from frappe import _
from frappe.utils import flt
from prakash_steel.utils.lead_time import get_default_bom


def calculate_sku_type(buffer_flag, item_type):
	"""
	Same mapping logic as calculate_sku_type in item.js and open_so_analysis.py
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


def build_calculation_breakdown_po_report(
	item_code,
	buffer_flag,
	is_buffer,
	sku_type,
	tog,
	qualified_demand,
	open_so,
	stock,
	wip,
	open_po,
	mrq,
	moq,
	batch_size,
	total_parent_demand,
	final_order_rec,
	net_order_rec,
	parent_demand_details_list,
):
	"""Build detailed calculation breakdown for an item in PO Recommendation report"""
	lines = []
	lines.append(f"\n  Item: {item_code}")
	lines.append(f"  Type: {buffer_flag}")
	if sku_type and sku_type != "N/A":
		lines.append(f"  SKU Type: {sku_type}")

	if is_buffer:
		lines.append(f"  TOG: {tog}")
		lines.append(f"  Qualified Demand: {qualified_demand}")
		lines.append(f"  Stock: {stock}")
		lines.append(f"  WIP: {wip}")
		lines.append(f"  Open PO: {open_po}")
		lines.append(f"  MRQ: {mrq}")

		if sku_type in ["BOTA", "PTA"]:
			base_calc = tog + qualified_demand - stock - wip - open_po
			lines.append("  Base Calculation: TOG + Qualified Demand - Stock - WIP - Open PO")
			lines.append(f"                    = {tog} + {qualified_demand} - {stock} - {wip} - {open_po}")
			lines.append(f"                    = {base_calc}")
			lines.append(f"  After MRQ: Base - MRQ = {base_calc} - {mrq} = {final_order_rec}")
		else:
			base_calc = tog + qualified_demand - stock - wip
			lines.append("  Base Calculation: TOG + Qualified Demand - Stock - WIP")
			lines.append(f"                    = {tog} + {qualified_demand} - {stock} - {wip}")
			lines.append(f"                    = {base_calc}")
			lines.append(f"  After MRQ: Base - MRQ = {base_calc} - {mrq} = {final_order_rec}")

		# Show MOQ/Batch Size logic
		if final_order_rec <= 0:
			if moq > 0:
				lines.append(f"  MOQ: {moq} (Not applied - base order rec is {final_order_rec} <= 0)")
			elif batch_size > 0:
				lines.append(
					f"  Batch Size: {batch_size} (Not applied - base order rec is {final_order_rec} <= 0)"
				)
			else:
				lines.append("  No MOQ or Batch Size")
			lines.append(f"  Net Order Recommendation: 0 (Base order rec is {final_order_rec} <= 0)")
		elif moq > 0:
			if moq < final_order_rec:
				lines.append(f"  MOQ: {moq} (MOQ < Order Rec, using Order Rec)")
				lines.append(f"  Net Order Recommendation: {final_order_rec}")
			else:
				lines.append(f"  MOQ: {moq} (MOQ >= Order Rec, using MOQ)")
				lines.append(f"  Net Order Recommendation: {moq}")
		elif batch_size > 0:
			net_calc = math.ceil(final_order_rec / batch_size) * batch_size
			lines.append(f"  Batch Size: {batch_size}")
			lines.append(
				f"  Net Order Recommendation: ceil({final_order_rec} / {batch_size}) × {batch_size} = {net_calc}"
			)
		else:
			lines.append("  No MOQ or Batch Size")
			lines.append(f"  Net Order Recommendation: {final_order_rec}")

		lines.append("  Note: Parent demand ignored for buffer items")
	else:
		# For non-buffer items, Open SO in breakdown should be qualified_demand (Open SO with delivery_date <= today)
		# This matches the buffer items' logic where Open SO = Qualified Demand
		open_so_for_breakdown = qualified_demand  # Use qualified demand instead of all-time open_so
		lines.append(f"  Open SO: {open_so_for_breakdown}")
		lines.append(f"  Stock: {stock}")
		lines.append(f"  WIP: {wip}")
		lines.append(f"  Open PO: {open_po}")
		lines.append(f"  Total Parent Demand: {total_parent_demand}")

		if total_parent_demand > 0 and parent_demand_details_list:
			lines.append("  Parent Demands Breakdown:")
			for pd in parent_demand_details_list:
				if pd.get("applied", True):
					lines.append(
						f"    - From {pd['parent_item']} (BOM: {pd['bom_name']}): {pd['demand_qty']} {pd.get('reason', '')}"
					)
				else:
					lines.append(
						f"    - From {pd['parent_item']} (BOM: {pd['bom_name']}): {pd['demand_qty']} [IGNORED - {pd.get('reason', '')}]"
					)

		requirement = open_so_for_breakdown + total_parent_demand

		if sku_type in ["PTO", "BOTO"]:
			base_calc = requirement - stock - wip - open_po
			lines.append(
				f"  Requirement: Open SO + Parent Demand = {open_so_for_breakdown} + {total_parent_demand} = {requirement}"
			)
			lines.append("  Base Calculation: Requirement - Stock - WIP - Open PO")
			lines.append(f"                    = {requirement} - {stock} - {wip} - {open_po}")
			lines.append(f"                    = {base_calc}")
			lines.append(f"  After MRQ: Base - MRQ = {base_calc} - {mrq} = {final_order_rec}")
		else:
			base_calc = requirement - stock - wip
			lines.append(
				f"  Requirement: Open SO + Parent Demand = {open_so_for_breakdown} + {total_parent_demand} = {requirement}"
			)
			lines.append("  Base Calculation: Requirement - Stock - WIP")
			lines.append(f"                    = {requirement} - {stock} - {wip}")
			lines.append(f"                    = {base_calc}")
			lines.append(f"  After MRQ: Base - MRQ = {base_calc} - {mrq} = {final_order_rec}")

		# Show MOQ/Batch Size logic
		if final_order_rec <= 0:
			if moq > 0:
				lines.append(f"  MOQ: {moq} (Not applied - base order rec is {final_order_rec} <= 0)")
			elif batch_size > 0:
				lines.append(
					f"  Batch Size: {batch_size} (Not applied - base order rec is {final_order_rec} <= 0)"
				)
			else:
				lines.append("  No MOQ or Batch Size")
			lines.append(f"  Net Order Recommendation: 0 (Base order rec is {final_order_rec} <= 0)")
		elif moq > 0:
			if moq < final_order_rec:
				lines.append(f"  MOQ: {moq} (MOQ < Order Rec, using Order Rec)")
				lines.append(f"  Net Order Recommendation: {final_order_rec}")
			else:
				lines.append(f"  MOQ: {moq} (MOQ >= Order Rec, using MOQ)")
				lines.append(f"  Net Order Recommendation: {moq}")
		elif batch_size > 0:
			net_calc = math.ceil(final_order_rec / batch_size) * batch_size
			lines.append(f"  Batch Size: {batch_size}")
			lines.append(
				f"  Net Order Recommendation: ceil({final_order_rec} / {batch_size}) × {batch_size} = {net_calc}"
			)
		else:
			lines.append("  No MOQ or Batch Size")
			lines.append(f"  Net Order Recommendation: {final_order_rec}")

	return "\n".join(lines)


def calculate_net_order_recommendation(base_order_rec, moq, batch_size):
	"""
	Calculate net order recommendation by applying MOQ/Batch Size logic.
	Same as mrp_genaration.py.

	Logic:
	- If base_order_rec <= 0: return 0 (no order needed, ignore MOQ/Batch Size)
	- If MOQ > 0:
	  - If MOQ < base_order_rec: use base_order_rec
	  - If MOQ >= base_order_rec: use MOQ
	- Else if batch_size > 0:
	  - ceil(base_order_rec / batch_size) * batch_size
	- Else:
	  - Use base_order_rec as is
	"""
	base_order_rec = flt(base_order_rec)
	moq = flt(moq)
	batch_size = flt(batch_size)

	# If base order recommendation is 0 or negative, return 0
	# Don't apply MOQ/Batch Size for negative or zero demand
	if base_order_rec <= 0:
		return 0

	if moq > 0:
		# Use MOQ:
		# If MOQ < base_order_rec: use base_order_rec
		# If MOQ >= base_order_rec: use MOQ
		if moq < base_order_rec:
			net_order_rec = base_order_rec
		else:
			net_order_rec = moq
	elif batch_size > 0:
		# Use Batch Size: ceil(base_order_rec / batch_size) * batch_size
		net_order_rec = math.ceil(base_order_rec / batch_size) * batch_size
	else:
		# No MOQ or Batch Size, use base_order_rec as is
		net_order_rec = base_order_rec

	return max(0, flt(net_order_rec))


def calculate_initial_order_recommendation(
	item_code,
	item_buffer_map,
	item_tog_map,
	item_sku_type_map,
	stock_map,
	wip_map,
	open_so_map,
	qualified_demand_map,
	open_po_map,
):
	"""
	Calculate initial order recommendation for a single item (before BOM traversal).
	Same as mrp_genaration.py.
	- Buffer: TOG + Qualified Demand - Stock - WIP/Open PO
	  - For BOTA/PTA: TOG + Qualified Demand - Stock - WIP - Open PO
	  - For others: TOG + Qualified Demand - Stock - WIP
	- Non-buffer: Qualified Demand - Stock - WIP (use qualified_demand, not all-time open_so)
	"""
	buffer_flag = item_buffer_map.get(item_code, "Non-Buffer")
	is_buffer = buffer_flag == "Buffer"

	stock = flt(stock_map.get(item_code, 0))
	wip = flt(wip_map.get(item_code, 0))

	if is_buffer:
		# Buffer item: Order recommendation = TOG + Qualified Demand - Stock - WIP/Open PO
		tog = flt(item_tog_map.get(item_code, 0))
		qualified_demand = flt(qualified_demand_map.get(item_code, 0))
		sku_type = item_sku_type_map.get(item_code)
		open_po = flt(open_po_map.get(item_code, 0))

		if sku_type in ["BOTA", "PTA"]:
			# For BOTA/PTA: TOG + Qualified Demand - Stock - WIP - Open PO
			order_rec = max(0, tog + qualified_demand - stock - wip - open_po)
		else:
			# For other buffer items: TOG + Qualified Demand - Stock - WIP
			order_rec = max(0, tog + qualified_demand - stock - wip)
	else:
		# Non-buffer item: Order recommendation = max(0, Qualified Demand - Stock - WIP)
		# For non-buffer items, use qualified_demand (Open SO with delivery_date <= today) instead of all-time open_so
		# For PTO and BOTO (purchase items): also subtract Open PO
		qualified_demand = flt(
			qualified_demand_map.get(item_code, 0)
		)  # Use qualified demand, not all-time open_so
		sku_type = item_sku_type_map.get(item_code)
		open_po = flt(open_po_map.get(item_code, 0))

		if sku_type in ["PTO", "BOTO"]:
			# For PTO/BOTO: Qualified Demand - Stock - WIP - Open PO
			order_rec = max(0, qualified_demand - stock - wip - open_po)
		else:
			# For other non-buffer items: Qualified Demand - Stock - WIP
			order_rec = max(0, qualified_demand - stock - wip)

	return order_rec


def calculate_final_order_recommendation(
	item_code,
	item_buffer_map,
	item_tog_map,
	item_sku_type_map,
	stock_map,
	wip_map,
	open_so_map,
	qualified_demand_map,
	open_po_map,
	mrq_map,
	parent_demand_map,
):
	"""
	Calculate final order recommendation for a single item (after BOM traversal).
	Same as mrp_genaration.py.
	- Buffer: TOG + Qualified Demand - Stock - WIP/Open PO - MRQ (parent demand ignored)
	  - For BOTA/PTA: TOG + Qualified Demand - Stock - WIP - Open PO - MRQ
	  - For others: TOG + Qualified Demand - Stock - WIP - MRQ
	- Non-buffer: max(0, (Open SO + Parent Demand) - Stock - WIP - MRQ)
	  - For PTO/BOTO: max(0, (Open SO + Parent Demand) - Stock - WIP - Open PO - MRQ)
	"""
	buffer_flag = item_buffer_map.get(item_code, "Non-Buffer")
	is_buffer = buffer_flag == "Buffer"

	stock = flt(stock_map.get(item_code, 0))
	wip = flt(wip_map.get(item_code, 0))
	mrq = flt(mrq_map.get(item_code, 0))

	if is_buffer:
		# Buffer item: Order recommendation = TOG + Qualified Demand - Stock - WIP/Open PO - MRQ (parent demand ignored)
		tog = flt(item_tog_map.get(item_code, 0))
		qualified_demand = flt(qualified_demand_map.get(item_code, 0))
		sku_type = item_sku_type_map.get(item_code)
		open_po = flt(open_po_map.get(item_code, 0))

		if sku_type in ["BOTA", "PTA"]:
			# For BOTA/PTA: TOG + Qualified Demand - Stock - WIP - Open PO - MRQ
			base_order_rec = tog + qualified_demand - stock - wip - open_po
		else:
			# For other buffer items: TOG + Qualified Demand - Stock - WIP - MRQ
			base_order_rec = tog + qualified_demand - stock - wip

		# Subtract MRQ from base order recommendation
		order_rec = max(0, base_order_rec - mrq)
	else:
		# Non-buffer item: Order recommendation = max(0, Requirement - Stock - WIP - MRQ)
		# Requirement = Qualified Demand (Open SO with delivery_date <= today) + sum of all parent BOM demands
		# For non-buffer items, use qualified_demand instead of all-time open_so (same as buffer items' logic)
		# For PTO and BOTO (purchase items): also subtract Open PO
		qualified_demand = flt(
			qualified_demand_map.get(item_code, 0)
		)  # Use qualified demand, not all-time open_so
		parent_demand = flt(parent_demand_map.get(item_code, 0))
		requirement = qualified_demand + parent_demand
		sku_type = item_sku_type_map.get(item_code)
		open_po = flt(open_po_map.get(item_code, 0))

		if sku_type in ["PTO", "BOTO"]:
			# For PTO/BOTO: Requirement - Stock - WIP - Open PO - MRQ
			base_order_rec = requirement - stock - wip - open_po
		else:
			# For other non-buffer items: Requirement - Stock - WIP - MRQ
			base_order_rec = requirement - stock - wip

		# Subtract MRQ from base order recommendation
		order_rec = max(0, base_order_rec - mrq)

	return order_rec


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def save_daily_on_hand_colour():
	"""
	Scheduled job:
	- Runs PO Recommendation for PSP report logic for ALL buffer items.
	- Calls the report twice: once for purchase buffer items (PTA, BOTA, TRMTA)
	  and once for sell buffer items (BBMTA, RBMTA), then combines results.
	- For each row, saves item_code, sku_type, and on_hand_colour into
	  Item wise Daily On Hand Colour (parent) and its child table
	  On hand colour table (fieldname: item_wise_on_hand_colour).
	- Uses today's date as posting_date.
	"""
	from frappe.utils import nowdate

	posting_date = nowdate()

	# Collect data from both purchase and sell buffer items
	all_data = []
	seen_item_codes = {}  # item_code -> row (to keep first occurrence)

	# 1. Get purchase buffer items (PTA, BOTA, TRMTA)
	try:
		filters_purchase = {"purchase": 1, "buffer_flag": 1}
		_, data_purchase = execute(filters_purchase)
		if data_purchase:
			for row in data_purchase:
				item_code = row.get("item_code")
				if item_code and item_code not in seen_item_codes:
					seen_item_codes[item_code] = row
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "save_daily_on_hand_colour: execute (purchase) failed")

	# 2. Get sell buffer items (BBMTA, RBMTA)
	try:
		filters_sell = {"sell": 1, "buffer_flag": 1}
		_, data_sell = execute(filters_sell)
		if data_sell:
			for row in data_sell:
				item_code = row.get("item_code")
				if item_code and item_code not in seen_item_codes:
					seen_item_codes[item_code] = row
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "save_daily_on_hand_colour: execute (sell) failed")

	# Combine all unique items
	all_data = list(seen_item_codes.values())

	if not all_data:
		return

	try:
		# Create parent doc for the snapshot
		doc = frappe.new_doc("Item wise Daily On Hand Colour")
		doc.posting_date = posting_date

		saved_rows = 0

		for row in all_data:
			item_code = row.get("item_code")
			sku_type = row.get("sku_type")
			on_hand_colour = row.get("on_hand_colour")

			# Only save rows that have both item_code and on_hand_colour
			if not item_code or not on_hand_colour:
				continue

			child = doc.append("item_wise_on_hand_colour", {})
			child.item_code = item_code
			child.sku_type = sku_type
			child.on_hand_colour = on_hand_colour
			saved_rows += 1

		if saved_rows == 0:
			return

		doc.insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(), "save_daily_on_hand_colour: failed to create snapshot document"
		)


def get_columns(filters=None):
	if not filters:
		filters = {}

	# Check if "Sell" is selected
	sell = filters.get("sell", 0)
	if isinstance(sell, str):
		sell = 1 if sell in ("1", "true", "True") else 0
	sell = int(sell) if sell else 0

	# Check if "Buffer Flag" is selected
	buffer_flag = filters.get("buffer_flag", 0)
	if isinstance(buffer_flag, str):
		buffer_flag = 1 if buffer_flag in ("1", "true", "True") else 0
	buffer_flag = int(buffer_flag) if buffer_flag else 0

	columns = [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("SKU Type"),
			"fieldname": "sku_type",
			"fieldtype": "Data",
			"width": 100,
		},
	]

	# Add "Requirement" column for non-buffer items (after SKU Type)
	if not buffer_flag:
		columns.append(
			{
				"label": _("Requirement"),
				"fieldname": "requirement",
				"fieldtype": "Int",
				"width": 120,
			}
		)

	# Add TOG, TOY, TOR columns only for buffer items
	if buffer_flag:
		columns.extend(
			[
				{
					"label": _("TOG"),
					"fieldname": "tog",
					"fieldtype": "Int",
					"width": 100,
				},
				{
					"label": _("TOY"),
					"fieldname": "toy",
					"fieldtype": "Int",
					"width": 100,
				},
				{
					"label": _("TOR"),
					"fieldname": "tor",
					"fieldtype": "Int",
					"width": 100,
				},
			]
		)

	# Add columns based on buffer_flag
	if buffer_flag:
		# For buffer items: Open SO and Qualified Demand
		columns.extend(
			[
				{
					"label": _("Open SO"),
					"fieldname": "open_so",
					"fieldtype": "Int",
					"width": 120,
				},
				{
					"label": _("On Hand Stock"),
					"fieldname": "on_hand_stock",
					"fieldtype": "Int",
					"width": 130,
				},
				{
					"label": _("WIP/Open PO"),
					"fieldname": "wip_open_po",
					"fieldtype": "Int",
					"width": 120,
				},
				{
					"label": _("Qualified Demand"),
					"fieldname": "qualify_demand",
					"fieldtype": "Int",
					"width": 130,
				},
			]
		)
	else:
		# For non-buffer items: Open SO, Total SO, On Hand Stock, WIP/Open PO, Qualified Demand, Open SO (qualified)
		columns.extend(
			[
				{
					"label": _("Open SO"),
					"fieldname": "open_so",
					"fieldtype": "Int",
					"width": 120,
					"hidden": 1,
				},
				{
					"label": _("Total SO"),
					"fieldname": "total_so",
					"fieldtype": "Int",
					"width": 120,
				},
				{
					"label": _("Open SO"),
					"fieldname": "open_so_qualified",
					"fieldtype": "Int",
					"width": 120,
				},
				{
					"label": _("On Hand Stock"),
					"fieldname": "on_hand_stock",
					"fieldtype": "Int",
					"width": 130,
				},
				{
					"label": _("WIP/Open PO"),
					"fieldname": "wip_open_po",
					"fieldtype": "Int",
					"width": 120,
				},
				{
					"label": _("Qualified Demand"),
					"fieldname": "qualify_demand",
					"fieldtype": "Int",
					"width": 130,
					"hidden": 1,
				},
			]
		)

	# Add remaining common columns
	columns.extend(
		[
			{
				"label": _("On Hand Status"),
				"fieldname": "on_hand_status",
				"fieldtype": "Data",
				"width": 130,
			},
			{
				"label": _("On Hand Colour"),
				"fieldname": "on_hand_colour",
				"fieldtype": "Data",
				"width": 130,
			},
			{
				"label": _("Order Recommendation"),
				"fieldname": "order_recommendation",
				"fieldtype": "Int",
				"width": 180,
			},
			{
				"label": _("MRQ"),
				"fieldname": "mrq",
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"label": _("Balance Order Recommendation"),
				"fieldname": "net_po_recommendation",
				"fieldtype": "Int",
				"width": 180,
			},
			{
				"label": _("Net Order Recommendation"),
				"fieldname": "or_with_moq_batch_size",
				"fieldtype": "Int",
				"width": 180,
			},
			{
				"label": _("MOQ"),
				"fieldname": "moq",
				"fieldtype": "Int",
				"width": 120,
			},
			{
				"label": _("Order Multiple Qty"),
				"fieldname": "batch_size",
				"fieldtype": "Int",
				"width": 120,
			},
		]
	)

	# Only add child-related columns if "Sell" is selected (hide for Purchase)
	if sell:
		columns.extend(
			[
				{
					"label": _("Production qty based on child stock"),
					"fieldname": "production_qty_based_on_child_stock",
					"fieldtype": "Int",
					"width": 220,
				},
				{
					"label": _("Child Stock Full-Kit Status"),
					"fieldname": "child_full_kit_status",
					"fieldtype": "Data",
					"width": 160,
				},
				{
					"label": _("Production qty based on child stock+WIP/Open PO"),
					"fieldname": "production_qty_based_on_child_stock_wip_open_po",
					"fieldtype": "Int",
					"width": 280,
				},
				{
					"label": _("Child Stock + WIP/Open PO Full-Kit Status"),
					"fieldname": "child_wip_open_po_full_kit_status",
					"fieldtype": "Data",
					"width": 160,
				},
				{
					"label": _("Child Item Code"),
					"fieldname": "child_item_code",
					"fieldtype": "Link",
					"options": "Item",
					"width": 150,
				},
				{
					"label": _("Child Item Type"),
					"fieldname": "child_item_type",
					"fieldtype": "Data",
					"width": 130,
				},
				{
					"label": _("Child SKU Type"),
					"fieldname": "child_sku_type",
					"fieldtype": "Data",
					"width": 130,
				},
				{
					"label": _("Child Requirement"),
					"fieldname": "child_requirement",
					"fieldtype": "Int",
					"width": 150,
				},
				{
					"label": _("Child stock"),
					"fieldname": "child_stock",
					"fieldtype": "Int",
					"width": 120,
				},
				{
					"label": _("Child Stock soft Allocation qty"),
					"fieldname": "child_stock_soft_allocation_qty",
					"fieldtype": "Int",
					"width": 200,
				},
				{
					"label": _("Child Stock shortage"),
					"fieldname": "child_stock_shortage",
					"fieldtype": "Int",
					"width": 160,
				},
				{
					"label": _("Child WIP/Open PO"),
					"fieldname": "child_wip_open_po",
					"fieldtype": "Int",
					"width": 150,
				},
				{
					"label": _("Child WIP/Open PO soft allocation qty"),
					"fieldname": "child_wip_open_po_soft_allocation_qty",
					"fieldtype": "Int",
					"width": 250,
				},
				{
					"label": _("Child WIP/Open PO Shortage"),
					"fieldname": "child_wip_open_po_shortage",
					"fieldtype": "Int",
					"width": 200,
				},
			]
		)

	return columns


def get_data(filters=None):
	"""
	Get ALL buffer items (regardless of sales orders) - all-time data
	Fetch tog (safety_stock), toy (custom_top_of_yellow), tor (custom_top_of_red) from Item doctype
	Calculate on_hand_stock from tabBin (sum of actual_qty across all warehouses)
	Calculate open_so as sum of qty from all sales orders (all-time) - will be 0 if no sales orders
	Calculate PO recommendation with recursive BOM traversal (only for items with sales orders)
	"""
	if not filters:
		filters = {}

	# Validate filters: Require Purchase OR Sell + Buffer Flag
	purchase = filters.get("purchase", 0)
	sell = filters.get("sell", 0)
	buffer_flag = filters.get("buffer_flag", 0)

	# Convert to boolean/int (handle string "1"/"0" or actual 1/0)
	if isinstance(purchase, str):
		purchase = 1 if purchase in ("1", "true", "True") else 0
	if isinstance(sell, str):
		sell = 1 if sell in ("1", "true", "True") else 0
	if isinstance(buffer_flag, str):
		buffer_flag = 1 if buffer_flag in ("1", "true", "True") else 0

	purchase = int(purchase) if purchase else 0
	sell = int(sell) if sell else 0
	buffer_flag = int(buffer_flag) if buffer_flag else 0

	# If filters are not selected, return empty data
	if not (purchase or sell):
		return []

	# Determine which SKU types to filter by based on Purchase/Sell and Buffer Flag
	allowed_sku_types = []
	if purchase:
		if buffer_flag:
			# Purchase + Buffer: PTA, BOTA, TRMTA
			allowed_sku_types = ["PTA", "BOTA", "TRMTA"]
		else:
			# Purchase + Non-Buffer: PTO, BOTO, TRMTO
			allowed_sku_types = ["PTO", "BOTO", "TRMTO"]
	elif sell:
		if buffer_flag:
			# Sell + Buffer: BBMTA, RBMTA
			allowed_sku_types = ["BBMTA", "RBMTA"]
		else:
			# Sell + Non-Buffer: BBMTO, RBMTO
			allowed_sku_types = ["BBMTO", "RBMTO"]

	# Get sales order qty map (all-time data) - for ALL items
	so_qty_map = get_sales_order_qty_map(filters)

	# Get qualified demand map (Open SO with delivery_date <= today)
	qualified_demand_map = get_qualified_demand_map(filters)

	# Get items from database based on buffer_flag filter
	if buffer_flag:
		# Get buffer items
		items_query = """
			SELECT name as item_code
			FROM `tabItem`
			WHERE custom_buffer_flag = 'Buffer'
		"""
	else:
		# Get non-buffer items
		items_query = """
			SELECT name as item_code
			FROM `tabItem`
			WHERE custom_buffer_flag != 'Buffer' OR custom_buffer_flag IS NULL
		"""

	items_result = frappe.db.sql(items_query, as_dict=1)
	item_codes = set(item.item_code for item in items_result)

	# Filter sales order items to only selected items (buffer or non-buffer)
	so_qty_map = {k: v for k, v in so_qty_map.items() if k in item_codes}

	# Get WIP map (qty from Work Order)
	wip_map = get_wip_map(filters)

	# Get MRQ map (Material Request Quantity - sum of qty from Material Request Items)
	mrq_map = get_mrq_map(filters)

	# Get Open PO map (Purchase Order Quantity - sum of (qty - received_qty) from Purchase Order Items)
	open_po_map = get_open_po_map()

	# Get items with purchase orders (especially important for BOTA, PTA, BOTO, PTO items)
	# These items use open_po instead of open_so, so they need to be shown even without sales orders
	items_with_po = set(open_po_map.keys())
	# Filter to only selected items (buffer or non-buffer) that have purchase orders
	items_with_po_selected = {item for item in items_with_po if item in item_codes}

	# Use ALL selected items (buffer or non-buffer), plus any selected items with purchase orders
	# This ensures items with purchase orders are shown even if they don't have sales orders
	all_items_to_process = item_codes | items_with_po_selected

	if not all_items_to_process:
		return []

	# Get stock for all selected items (including those with purchase orders)
	initial_stock_map = get_stock_map(all_items_to_process)

	# Create remaining_stock map - tracks available stock after allocations
	# Start with initial stock, will be reduced as items are allocated
	remaining_stock = dict(initial_stock_map)

	# Calculate PO recommendations with BOM traversal
	# po_recommendations will contain ALL items (buffer and non-buffer)
	po_recommendations = {}
	item_groups_cache = {}  # Cache item_group to check for Raw Material

	# Initialize parent demand map (for non-buffer items)
	# This will accumulate parent demands from all BOMs
	parent_demand_map = {}  # item_code -> total parent demand from all BOMs

	# Process each selected item that has sales orders (for BOM traversal)
	# Sort by item_code for consistent processing order
	items_with_so = set(so_qty_map.keys())
	for item_code in sorted(items_with_so):
		so_qty = flt(so_qty_map.get(item_code, 0))
		available_stock = flt(remaining_stock.get(item_code, 0))

		# Calculate PO recommendation for this item using remaining stock
		required_qty = max(0, so_qty - available_stock)

		# Allocate stock: reduce remaining stock by what we use
		allocated = min(so_qty, available_stock)
		remaining_stock[item_code] = available_stock - allocated

		# Add to PO recommendations
		if item_code in po_recommendations:
			po_recommendations[item_code] += required_qty
		else:
			po_recommendations[item_code] = required_qty

		# If we need to produce this item, traverse BOM
		# Only traverse if stock is insufficient (required_qty > 0)
		if required_qty > 0:
			traverse_bom_for_po(
				item_code,
				required_qty,
				po_recommendations,
				remaining_stock,
				set(),
				item_groups_cache,
				level=0,
			)

	# Calculate parent demand for non-buffer items
	# Same logic as mrp_genaration.py lines 160-457
	# Step 1: Calculate initial order recommendations for all items
	# First, get all item details needed for calculation
	all_item_codes = all_items_to_process

	# Get item details maps
	if all_item_codes:
		if len(all_item_codes) == 1:
			all_items_tuple = (next(iter(all_item_codes)),)
		else:
			all_items_tuple = tuple(all_item_codes)

		items_details_all = frappe.db.sql(
			"""
			SELECT
				i.name as item_code,
				i.custom_buffer_flag as buffer_flag,
				i.custom_item_type as item_type,
				i.safety_stock as tog
			FROM
				`tabItem` i
			WHERE
				i.name IN %s
			""",
			(all_items_tuple,),
			as_dict=1,
		)

		item_buffer_map_all = {}
		item_sku_type_map_all = {}
		item_tog_map_all = {}
		for item in items_details_all:
			item_buffer_map_all[item.item_code] = item.buffer_flag or "Non-Buffer"
			item_sku_type_map_all[item.item_code] = calculate_sku_type(
				item.buffer_flag or "Non-Buffer", item.item_type
			)
			item_tog_map_all[item.item_code] = flt(item.tog or 0)
	else:
		item_buffer_map_all = {}
		item_sku_type_map_all = {}
		item_tog_map_all = {}

	# Step 1: Calculate initial order recommendations for all items
	initial_order_recommendations = {}
	for item_code in all_item_codes:
		order_rec = calculate_initial_order_recommendation(
			item_code,
			item_buffer_map_all,
			item_tog_map_all,
			item_sku_type_map_all,
			initial_stock_map,
			wip_map,
			so_qty_map,
			qualified_demand_map,
			open_po_map,
		)
		initial_order_recommendations[item_code] = order_rec

	# Step 1.5: Apply MOQ/Batch Size to initial order recommendations
	initial_net_order_recommendations = {}

	# Get MOQ and Batch Size for all items
	if all_item_codes:
		items_moq_batch_data = frappe.db.sql(
			"""
			SELECT
				i.name as item_code,
				i.min_order_qty as moq,
				i.custom_batch_size as batch_size
			FROM
				`tabItem` i
			WHERE
				i.name IN %s
			""",
			(all_items_tuple,),
			as_dict=1,
		)

		moq_map_all = {item.item_code: flt(item.moq or 0) for item in items_moq_batch_data}
		batch_size_map_all = {item.item_code: flt(item.batch_size or 0) for item in items_moq_batch_data}

		for item_code in all_item_codes:
			base_order_rec = initial_order_recommendations.get(item_code, 0)
			moq = moq_map_all.get(item_code, 0)
			batch_size = batch_size_map_all.get(item_code, 0)
			net_order_rec = calculate_net_order_recommendation(base_order_rec, moq, batch_size)
			initial_net_order_recommendations[item_code] = net_order_rec
	else:
		moq_map_all = {}
		batch_size_map_all = {}

	# Step 2: Traverse BOMs starting from items with net order recommendations > 0 (first traversal)

	# First traversal - accumulate parent demands
	items_to_process = [
		(item_code, net_order_rec)
		for item_code, net_order_rec in initial_net_order_recommendations.items()
		if net_order_rec > 0
	]
	items_to_process.sort(key=lambda x: x[0])

	for item_code, net_order_rec in items_to_process:
		traverse_bom_for_parent_demand_simple(
			item_code,
			net_order_rec,
			parent_demand_map,
			set(),
			item_groups_cache,
			item_buffer_map_all,
			level=0,
		)

	# Step 3: Calculate final order recommendations for all items (with parent demands from first traversal)
	final_order_recommendations = {}
	for item_code in all_item_codes:
		# Use qualified_demand_map instead of so_qty_map (all-time Open SO)
		# The function already uses qualified_demand_map internally for non-buffer items
		order_rec = calculate_final_order_recommendation(
			item_code,
			item_buffer_map_all,
			item_tog_map_all,
			item_sku_type_map_all,
			initial_stock_map,
			wip_map,
			qualified_demand_map,  # Pass qualified_demand_map as open_so_map (function uses qualified_demand for non-buffer items)
			qualified_demand_map,
			open_po_map,
			mrq_map,
			parent_demand_map,
		)
		final_order_recommendations[item_code] = order_rec

	# Step 4: Apply MOQ/Batch Size to get net order recommendations
	net_order_recommendations = {}
	for item_code in all_item_codes:
		base_order_rec = final_order_recommendations.get(item_code, 0)
		moq = moq_map_all.get(item_code, 0)
		batch_size = batch_size_map_all.get(item_code, 0)
		net_order_rec = calculate_net_order_recommendation(base_order_rec, moq, batch_size)
		net_order_recommendations[item_code] = net_order_rec

	# Step 5: Re-traverse BOMs using net_order_recommendations to update child requirements
	# Clear parent_demand_map and recalculate with net_order_recommendations
	parent_demand_map_net = {}  # New parent demand map using net order recommendations
	parent_demand_details = {}  # Track parent demand details for breakdown

	# Get items with net_order_recommendation > 0
	items_with_net_rec = [
		(item_code, net_rec) for item_code, net_rec in net_order_recommendations.items() if net_rec > 0
	]
	items_with_net_rec.sort(key=lambda x: x[0])

	# Use a single shared visited_items set for the entire Step 5 traversal
	global_visited_items = set()

	# Re-traverse BOMs using net_order_recommendations
	# Only traverse items that haven't been visited yet (to avoid duplicates)
	for item_code, net_rec in items_with_net_rec:
		if item_code not in global_visited_items:
			traverse_bom_for_parent_demand(
				item_code,
				net_rec,
				parent_demand_map_net,
				parent_demand_details,
				global_visited_items,
				item_groups_cache,
				qualified_demand_map,  # Use qualified_demand_map instead of so_qty_map (all-time Open SO)
				initial_stock_map,
				wip_map,
				open_po_map,
				mrq_map,
				moq_map_all,
				batch_size_map_all,
				item_buffer_map_all,
				item_sku_type_map_all,
				lambda item_code: None,  # Helper function - maps already populated above
				level=0,
			)

	# Step 6: Recalculate final order recommendations with updated parent demands
	# Then apply MOQ/Batch Size again to get final net_order_recommendations
	# Same logic as mrp_genaration.py Step 6
	final_order_recommendations_updated = {}
	net_order_recommendations_final = {}

	for item_code in all_item_codes:
		# Recalculate with updated parent demands
		# Use qualified_demand_map instead of so_qty_map (all-time Open SO)
		# This ensures non-buffer items use qualified_demand (Open SO with delivery_date <= today)
		# The function already uses qualified_demand_map internally for non-buffer items, so we can pass it as open_so_map
		order_rec = calculate_final_order_recommendation(
			item_code,
			item_buffer_map_all,
			item_tog_map_all,
			item_sku_type_map_all,
			initial_stock_map,
			wip_map,
			qualified_demand_map,  # Pass qualified_demand_map as open_so_map (function uses qualified_demand for non-buffer items)
			qualified_demand_map,
			open_po_map,
			mrq_map,
			parent_demand_map_net,  # Use updated parent demands
		)
		final_order_recommendations_updated[item_code] = order_rec

		# Apply MOQ/Batch Size again
		moq = moq_map_all.get(item_code, 0)
		batch_size = batch_size_map_all.get(item_code, 0)
		net_order_rec = calculate_net_order_recommendation(order_rec, moq, batch_size)
		net_order_recommendations_final[item_code] = net_order_rec

	# Use the final updated values for the report
	final_order_recommendations = final_order_recommendations_updated
	net_order_recommendations = net_order_recommendations_final
	parent_demand_map = parent_demand_map_net  # Use updated parent demands

	# Show ALL selected items, including those with purchase orders
	# Items like BOTA, PTA, BOTO, PTO use open_po instead of open_so, so we need to include items with purchase orders
	all_items_to_show = all_items_to_process

	# Get item details for all items to show
	if not all_items_to_show:
		return []

	# Build item codes tuple for SQL
	if len(all_items_to_show) == 1:
		item_codes_tuple = (next(iter(all_items_to_show)),)
	else:
		item_codes_tuple = tuple(all_items_to_show)

	# Get item details with TOG, TOY, TOR, Item Type, Batch Size, MOQ, and Item Name
	# Include buffer or non-buffer items based on filter
	if buffer_flag:
		items_data = frappe.db.sql(
			"""
			SELECT
				i.name as item_code,
				i.item_name,
				i.safety_stock as tog,
				i.custom_top_of_yellow as toy,
				i.custom_top_of_red as tor,
				i.custom_item_type as item_type,
				i.custom_batch_size as batch_size,
				i.min_order_qty as moq,
				i.custom_buffer_flag as buffer_flag
			FROM
				`tabItem` i
			WHERE
				i.name IN %s
				AND i.custom_buffer_flag = 'Buffer'
			""",
			(item_codes_tuple,),
			as_dict=1,
		)
	else:
		items_data = frappe.db.sql(
			"""
			SELECT
				i.name as item_code,
				i.item_name,
				i.safety_stock as tog,
				i.custom_top_of_yellow as toy,
				i.custom_top_of_red as tor,
				i.custom_item_type as item_type,
				i.custom_batch_size as batch_size,
				i.min_order_qty as moq,
				i.custom_buffer_flag as buffer_flag
			FROM
				`tabItem` i
			WHERE
				i.name IN %s
				AND (i.custom_buffer_flag != 'Buffer' OR i.custom_buffer_flag IS NULL)
			""",
			(item_codes_tuple,),
			as_dict=1,
		)

	# Create a map for quick lookup
	items_map = {item.item_code: item for item in items_data}

	# Build final data list with all items (buffer or non-buffer based on filter)
	# Track total stock for display (we'll fetch it once per child item)
	# Track total WIP/Open PO for each child item (for FIFO allocation)
	# FIFO allocation will be applied AFTER sorting, in display order
	child_stock_map = {}
	child_wip_open_po_map = {}

	data = []
	for item_code in sorted(all_items_to_show):
		item_info = items_map.get(item_code, {})

		# Skip if item is not in items_map
		if not item_info:
			continue

		# Calculate SKU Type based on buffer_flag
		item_type = item_info.get("item_type")
		item_buffer_flag = item_info.get("buffer_flag", "")
		sku_type = calculate_sku_type(item_buffer_flag, item_type)

		# Filter by allowed SKU types (based on Purchase/Sell selection)
		if sku_type not in allowed_sku_types:
			continue

		# Get stock and buffer levels
		on_hand_stock = flt(initial_stock_map.get(item_code, 0))
		tog = flt(item_info.get("tog", 0))
		toy = flt(item_info.get("toy", 0))
		tor = flt(item_info.get("tor", 0))
		# Get Qualified Demand (Open SO with delivery_date <= today)
		qualify_demand = flt(qualified_demand_map.get(item_code, 0))

		# Calculate On Hand Status = on_hand_stock / (TOG + qualify_demand) (rounded up)
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

		# Calculate On Hand Status (rounded up value with % sign)
		if numeric_status is not None:
			on_hand_status = f"{int(numeric_status)}%"
		else:
			on_hand_status = None

		# Get item name
		item_name = item_info.get("item_name", "")

		# Get WIP value
		wip = flt(wip_map.get(item_code, 0))

		# Get batch size from item
		batch_size = flt(item_info.get("batch_size", 0))

		# Get MOQ from item
		moq = flt(item_info.get("moq", 0))

		# Get MRQ from Material Requests (sum of quantities from Material Request Items)
		mrq = flt(mrq_map.get(item_code, 0))

		# Get Open PO (Purchase Order quantity - received quantity)
		open_po = flt(open_po_map.get(item_code, 0))

		# Get Open SO
		open_so = flt(so_qty_map.get(item_code, 0))

		# Get parent demand for this item
		parent_demand = flt(parent_demand_map.get(item_code, 0))
		parent_demand_details_list = parent_demand_details.get(item_code, [])

		# Use the calculated final order recommendations and net order recommendations from Steps 3-4
		# These already include parent demand and use qualified_demand for non-buffer items
		final_order_rec = flt(final_order_recommendations.get(item_code, 0))
		net_order_rec = flt(net_order_recommendations.get(item_code, 0))

		# For display in report:
		# - order_recommendation = final_order_rec (base order recommendation after MRQ)
		# - net_po_recommendation = final_order_rec (same, before MOQ/Batch Size)
		# - or_with_moq_batch_size = net_order_rec (after MOQ/Batch Size)
		order_recommendation = int(flt(final_order_rec))
		net_po_recommendation = int(flt(final_order_rec))  # Base order recommendation (before MOQ/Batch Size)
		or_with_moq_batch_size = int(flt(net_order_rec))  # Net order recommendation (after MOQ/Batch Size)

		# Combine WIP and Open PO for display
		wip_open_po = int(flt(wip) + flt(open_po))

		# Base row with parent item data
		is_item_buffer = item_buffer_flag == "Buffer"

		# Calculate final order recommendation for breakdown
		# For non-buffer items, use qualified_demand (Open SO with delivery_date <= today) instead of all-time open_so
		# This matches the buffer items' logic where Open SO = Qualified Demand
		if is_item_buffer:
			# Buffer: TOG + Qualified Demand - Stock - WIP - Open PO - MRQ
			if sku_type in ["BOTA", "PTA"]:
				base_order_rec = tog + qualify_demand - on_hand_stock - wip - open_po
			else:
				base_order_rec = tog + qualify_demand - on_hand_stock - wip
			final_order_rec = max(0, base_order_rec - mrq)
		else:
			# Non-buffer: (Qualified Demand + Parent Demand) - Stock - WIP - Open PO - MRQ
			# Use qualified_demand instead of all-time open_so for calculation
			open_so_for_calc = qualify_demand  # Use qualified demand (Open SO with delivery_date <= today)
			requirement = open_so_for_calc + parent_demand
			if sku_type in ["PTO", "BOTO"]:
				base_order_rec = requirement - on_hand_stock - wip - open_po
			else:
				base_order_rec = requirement - on_hand_stock - wip
			final_order_rec = max(0, base_order_rec - mrq)

		# Calculate net order recommendation for breakdown
		net_order_rec_breakdown = calculate_net_order_recommendation(final_order_rec, moq, batch_size)

		# Build calculation breakdown
		# For non-buffer items, pass qualified_demand as open_so parameter so breakdown shows correct value
		open_so_for_breakdown = qualify_demand if not is_item_buffer else open_so
		calculation_breakdown = build_calculation_breakdown_po_report(
			item_code,
			item_buffer_flag,
			is_item_buffer,
			sku_type,
			tog,
			qualify_demand,
			open_so_for_breakdown,  # Use qualified_demand for non-buffer items in breakdown
			on_hand_stock,
			wip,
			open_po,
			mrq,
			moq,
			batch_size,
			parent_demand,
			final_order_rec,
			net_order_rec_breakdown,
			parent_demand_details_list,
		)

		if is_item_buffer:
			# Buffer items: use standard column names
			base_row = {
				"item_code": item_code,
				"item_name": item_name,
				"sku_type": sku_type,
				"requirement": None,
				"tog": int(flt(tog)),
				"toy": int(flt(toy)),
				"tor": int(flt(tor)),
				"open_so": int(flt(open_so)),
				"on_hand_stock": int(flt(on_hand_stock)),
				"wip_open_po": int(flt(wip_open_po)),
				"qualify_demand": int(flt(qualify_demand)),
			}
		else:
			# Non-buffer items: use same column names
			# open_so = all-time open SO (same as buffer items' open_so)
			# total_so = all-time open SO (same value as open_so, for display)
			# qualify_demand = qualified demand (same as buffer items' qualify_demand)
			# open_so_qualified = qualified demand (same value as qualify_demand, for display)
			# requirement = parent demand (for non-buffer items, this is the parent demand from BOMs)
			base_row = {
				"item_code": item_code,
				"item_name": item_name,
				"sku_type": sku_type,
				"requirement": int(flt(parent_demand)),  # Parent demand only (Open SO is in separate column)
				"tog": None,
				"toy": None,
				"tor": None,
				"open_so": int(flt(open_so)),  # All-time Open SO
				"total_so": int(flt(open_so)),  # Total SO = All-time Open SO (same as buffer items' open_so)
				"on_hand_stock": int(flt(on_hand_stock)),
				"wip_open_po": int(flt(wip_open_po)),
				"qualify_demand": int(flt(qualify_demand)),  # Qualified Demand
				"open_so_qualified": int(
					flt(qualify_demand)
				),  # Open SO = Qualified Demand (same as buffer items' qualify_demand)
			}

		# Add common fields
		base_row.update(
			{
				"on_hand_status": on_hand_status,
				"on_hand_colour": on_hand_colour,
				"order_recommendation": int(flt(order_recommendation)),
				"batch_size": int(flt(batch_size)),
				"moq": int(flt(moq)),
				"or_with_moq_batch_size": int(flt(or_with_moq_batch_size)),
				"mrq": int(flt(mrq)),
				"net_po_recommendation": int(flt(net_po_recommendation)),
				"calculation_breakdown": calculation_breakdown,  # Add breakdown for console logging
				# Initialize child columns as None/0
				"batch_size_multiple": None,
				"production_qty_based_on_child_stock": None,
				"production_qty_based_on_child_stock_wip_open_po": None,
				"child_item_code": None,
				"child_item_type": None,
				"child_sku_type": None,
				"child_requirement": None,
				"child_stock": None,
				"child_stock_soft_allocation_qty": None,
				"child_stock_shortage": None,
				"child_full_kit_status": None,
				"child_wip_open_po": None,
				"child_wip_open_po_soft_allocation_qty": None,
				"child_wip_open_po_shortage": None,
				"child_wip_open_po_full_kit_status": None,
			}
		)

		# Get BOM for this item to find child items
		bom = get_default_bom(item_code)
		child_items = []

		if bom:
			try:
				bom_doc = frappe.get_doc("BOM", bom)
				# Get all child items from BOM
				for bom_item in bom_doc.items:
					child_item_code = bom_item.item_code
					child_items.append(
						{
							"item_code": child_item_code,
							"qty": flt(bom_item.qty),
						}
					)
			except Exception as e:
				frappe.log_error(
					f"Error getting BOM {bom} for item {item_code}: {str(e)}", "PO Recommendation Error"
				)

		# If item has child items, create a row for each child
		# Otherwise, create one row with empty child columns
		if child_items:
			for child_item_info in child_items:
				child_item_code = child_item_info["item_code"]

				# Fetch child item details
				child_item_type = None
				child_sku_type = None
				child_stock = 0

				try:
					child_item_doc = frappe.get_doc("Item", child_item_code)
					child_item_type = child_item_doc.get("custom_item_type")
					child_buffer_flag = child_item_doc.get("custom_buffer_flag") or "Non-Buffer"
					# Calculate child SKU type using the existing function
					child_sku_type = calculate_sku_type(child_buffer_flag, child_item_type)

					# Get child item stock from Bin table (only fetch once per child item)
					if child_item_code not in child_stock_map:
						stock_data = frappe.db.sql(
							"""
							SELECT SUM(actual_qty) as stock
							FROM `tabBin`
							WHERE item_code = %s
							""",
							(child_item_code,),
							as_dict=True,
						)
						total_stock = int(
							flt(stock_data[0].stock if stock_data and stock_data[0].stock else 0)
						)
						child_stock_map[child_item_code] = total_stock

					# Use total stock for display
					child_stock = child_stock_map.get(child_item_code, 0)
				except Exception as e:
					frappe.log_error(
						f"Error fetching child item {child_item_code}: {str(e)}", "PO Recommendation Error"
					)

				child_requirement = int(flt(or_with_moq_batch_size))

				# Get Child WIP and Open PO (same logic as parent items)
				child_wip = flt(wip_map.get(child_item_code, 0))
				child_open_po = flt(open_po_map.get(child_item_code, 0))
				# Combine WIP and Open PO for display
				child_wip_open_po = int(flt(child_wip) + flt(child_open_po))
				# Store total WIP/Open PO for this child item (for FIFO allocation)
				if child_item_code not in child_wip_open_po_map:
					child_wip_open_po_map[child_item_code] = child_wip_open_po

				# Create a copy of base_row and populate child columns
				# Note: FIFO allocation will be calculated AFTER sorting, in display order
				row = base_row.copy()
				row["child_item_code"] = child_item_code
				row["child_item_type"] = child_item_type
				row["child_sku_type"] = child_sku_type
				row["child_requirement"] = child_requirement
				row["child_stock"] = child_stock
				row["child_wip_open_po"] = child_wip_open_po
				# child_stock_soft_allocation_qty and child_stock_shortage will be calculated after sorting
				row["child_stock_soft_allocation_qty"] = None
				row["child_stock_shortage"] = None
				# Other child columns will be populated later

				data.append(row)
		else:
			# No child items, add row with empty child columns
			data.append(base_row)

	# Apply filters
	filtered_data = []
	for row in data:
		# Filter by SKU Type
		if filters.get("sku_type"):
			sku_type_filter = filters.get("sku_type")
			sku_type_list = []

			# Handle different formats that MultiSelectList can send
			if isinstance(sku_type_filter, str):
				# Try to parse as JSON first (in case it's a JSON string)
				if sku_type_filter.strip().startswith("[") or sku_type_filter.strip().startswith("{"):
					try:
						import json

						parsed = json.loads(sku_type_filter)
						if isinstance(parsed, list):
							sku_type_list = [str(s).strip() for s in parsed if s]
						else:
							sku_type_list = [str(parsed).strip()] if parsed else []
					except:
						# If JSON parsing fails, treat as comma-separated string
						sku_type_list = [s.strip() for s in sku_type_filter.split(",") if s.strip()]
				else:
					# Comma-separated string
					sku_type_list = [s.strip() for s in sku_type_filter.split(",") if s.strip()]
			elif isinstance(sku_type_filter, list):
				# Already a list
				sku_type_list = [str(s).strip() for s in sku_type_filter if s]
			else:
				# Single value
				sku_type_list = [str(sku_type_filter).strip()] if sku_type_filter else []

			# Only filter if we have valid SKU types in the filter
			if sku_type_list and row.get("sku_type") not in sku_type_list:
				continue

		# Filter by Item Code (exact match)
		if filters.get("item_code"):
			if row.get("item_code") != filters.get("item_code"):
				continue

		filtered_data.append(row)

	# Sort by On Hand Status in ascending order
	# Extract numeric value from on_hand_status (e.g., "50%" -> 50)
	# None values will be sorted last (treated as very high value)
	def get_on_hand_status_value(row):
		on_hand_status = row.get("on_hand_status")
		if on_hand_status is None:
			return float("inf")  # Put None values at the end
		# Extract number from string like "50%"
		try:
			# Remove % sign and convert to float
			numeric_value = float(on_hand_status.replace("%", "").strip())
			return numeric_value
		except (ValueError, AttributeError):
			return float("inf")  # Put invalid values at the end

	filtered_data.sort(key=get_on_hand_status_value)

	# Apply FIFO Stock Allocation and Shortage AFTER sorting (in display order)
	# Re-initialize remaining_child_stock for FIFO allocation
	remaining_child_stock_fifo = {}
	# Re-initialize remaining_child_wip_open_po for FIFO allocation
	remaining_child_wip_open_po_fifo = {}

	for row in filtered_data:
		child_item_code = row.get("child_item_code")
		if child_item_code:
			# Initialize remaining stock if not already done
			if child_item_code not in remaining_child_stock_fifo:
				# Get total stock for this child item
				if child_item_code in child_stock_map:
					remaining_child_stock_fifo[child_item_code] = child_stock_map[child_item_code]
				else:
					# Fetch stock if not in map
					try:
						stock_data = frappe.db.sql(
							"""
							SELECT SUM(actual_qty) as stock
							FROM `tabBin`
							WHERE item_code = %s
							""",
							(child_item_code,),
							as_dict=True,
						)
						total_stock = int(
							flt(stock_data[0].stock if stock_data and stock_data[0].stock else 0)
						)
						child_stock_map[child_item_code] = total_stock
						remaining_child_stock_fifo[child_item_code] = total_stock
					except Exception:
						remaining_child_stock_fifo[child_item_code] = 0

			# Initialize remaining WIP/Open PO if not already done
			if child_item_code not in remaining_child_wip_open_po_fifo:
				# Get total WIP/Open PO for this child item
				if child_item_code in child_wip_open_po_map:
					remaining_child_wip_open_po_fifo[child_item_code] = flt(
						child_wip_open_po_map[child_item_code]
					)
				else:
					# If not in map, use the value from the row (shouldn't happen, but handle it)
					remaining_child_wip_open_po_fifo[child_item_code] = flt(row.get("child_wip_open_po", 0))

			# Apply FIFO allocation for stock (same logic as open_so_analysis)
			child_requirement = flt(row.get("child_requirement", 0))
			available_stock = flt(remaining_child_stock_fifo.get(child_item_code, 0))
			stock_allocated = min(child_requirement, available_stock)
			stock_shortage = child_requirement - stock_allocated

			row["child_stock_soft_allocation_qty"] = int(stock_allocated)
			row["child_stock_shortage"] = int(stock_shortage)

			production_qty_based_on_child_stock = math.floor(flt(stock_allocated))
			row["production_qty_based_on_child_stock"] = int(production_qty_based_on_child_stock)

			# Apply FIFO allocation for WIP/Open PO against remaining requirement (after stock allocation)
			remaining_requirement_after_stock = stock_shortage
			available_wip_open_po = flt(remaining_child_wip_open_po_fifo.get(child_item_code, 0))
			wip_open_po_allocated = min(remaining_requirement_after_stock, available_wip_open_po)
			wip_open_po_shortage = remaining_requirement_after_stock - wip_open_po_allocated

			row["child_wip_open_po_soft_allocation_qty"] = int(wip_open_po_allocated)
			row["child_wip_open_po_shortage"] = int(wip_open_po_shortage)

			# Calculate Child WIP/Open PO Full-kit Status
			# IMPORTANT:
			# - If net_order_recommendation (or_with_moq_batch_size) is 0 → blank (no order to fulfill)
			# - If child_wip_open_po_shortage = 0 → "Full-kit" (regardless of allocation)
			# - If child_wip_open_po_shortage > 0 AND child_wip_open_po_soft_allocation_qty = 0 → "Pending"
			# - If child_wip_open_po_shortage > 0 AND child_wip_open_po_soft_allocation_qty > 0 → "Partial"
			net_order_recommendation = flt(row.get("or_with_moq_batch_size", 0))
			
			if flt(net_order_recommendation) == 0:
				row["child_wip_open_po_full_kit_status"] = None
			elif flt(wip_open_po_shortage) == 0:
				row["child_wip_open_po_full_kit_status"] = "Full-kit"
			elif flt(wip_open_po_allocated) == 0:
				row["child_wip_open_po_full_kit_status"] = "Pending"
			else:
				row["child_wip_open_po_full_kit_status"] = "Partial"

			# Calculate Production qty based on child stock+WIP/Open PO = (child_stock_soft_allocation_qty + child_wip_open_po_soft_allocation_qty)
			total_allocated = flt(stock_allocated) + flt(wip_open_po_allocated)
			production_qty_based_on_child_stock_wip_open_po = math.floor(total_allocated)
			row["production_qty_based_on_child_stock_wip_open_po"] = int(
				production_qty_based_on_child_stock_wip_open_po
			)

			# Calculate Child Stock Full-kit Status
			# IMPORTANT:
			# - This column is intended to reflect coverage from STOCK ONLY
			# - WIP / Open PO coverage is shown separately in child_wip_open_po_full_kit_status
			# Logic (stock based only):
			#   - If order_recommendation is 0  → blank (no order to fulfill)
			#   - If stock_shortage = 0        → "Full-kit"
			#   - If stock_shortage > 0 and stock_allocated = 0 → "Pending"
			#   - If stock_shortage > 0 and stock_allocated > 0 → "Partial"
			order_recommendation = flt(row.get("order_recommendation", 0))

			if flt(order_recommendation) == 0:
				row["child_full_kit_status"] = None
			elif flt(stock_shortage) == 0:
				row["child_full_kit_status"] = "Full-kit"
			elif flt(stock_allocated) == 0:
				row["child_full_kit_status"] = "Pending"
			else:
				row["child_full_kit_status"] = "Partial"

			# Update remaining stock for this child item (FIFO - reduce by allocated amount)
			remaining_child_stock_fifo[child_item_code] = available_stock - stock_allocated
			# Update remaining WIP/Open PO for this child item (FIFO - reduce by allocated amount)
			remaining_child_wip_open_po_fifo[child_item_code] = available_wip_open_po - wip_open_po_allocated

	return filtered_data


@frappe.whitelist()
def debug_po_calculation(item_code, filters=None):
	"""
	Debug function to show detailed PO calculation for a specific item
	Similar to debug_lead_time_calculation
	"""
	if not item_code:
		return {"error": "Item code is required"}

	if not frappe.db.exists("Item", item_code):
		return {"error": f"Item {item_code} not found"}

	# Parse filters if it's a JSON string
	if isinstance(filters, str):
		import json

		try:
			filters = json.loads(filters)
		except:
			filters = {}

	if not filters:
		filters = {}

	# Get sales order qty for this item (all-time data)
	query_params = {"item_code": item_code}

	so_data = frappe.db.sql(
		"""
		SELECT SUM(soi.qty - IFNULL(soi.delivered_qty, 0)) as so_qty
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE soi.item_code = %(item_code)s
		AND so.status NOT IN ('Stopped', 'On Hold', 'Closed', 'Cancelled', 'Completed')
		AND so.docstatus = 1
		""",
		query_params,
		as_dict=True,
	)

	so_qty = flt(so_data[0].so_qty if so_data and so_data[0].so_qty else 0)

	# For debug, simulate the FULL calculation with stock allocation
	# This ensures we see how stock is consumed by other items before this item is processed
	so_qty_map_all = get_sales_order_qty_map(filters)
	all_items_with_so = set(so_qty_map_all.keys())

	# Get initial stock for all items
	initial_stock_map = get_stock_map(all_items_with_so)

	# Create remaining_stock map - tracks available stock after allocations
	remaining_stock = dict(initial_stock_map)

	# Track which items consumed stock from our target item
	stock_consumers = []

	# Process all items in sorted order (same as main calculation)
	# BUT skip the target item - we'll process it separately at the end
	po_recommendations_all = {}
	item_groups_cache = {}

	for other_item_code in sorted(all_items_with_so):
		# Skip the target item - we'll process it separately
		if other_item_code == item_code:
			continue

		other_so_qty = flt(so_qty_map_all.get(other_item_code, 0))
		other_available_stock = flt(remaining_stock.get(other_item_code, 0))
		other_required_qty = max(0, other_so_qty - other_available_stock)

		# Allocate stock
		other_allocated = min(other_so_qty, other_available_stock)
		remaining_stock[other_item_code] = other_available_stock - other_allocated

		# Track if this item consumes stock from our target item
		if other_required_qty > 0:
			# Check if this item's BOM uses our target item
			bom = get_default_bom(other_item_code)
			if bom:
				try:
					bom_doc = frappe.get_doc("BOM", bom)
					for bom_item in bom_doc.items:
						if bom_item.item_code == item_code:
							consumed_qty = other_required_qty * flt(bom_item.qty)
							stock_consumers.append(
								{
									"item_code": other_item_code,
									"consumed_qty": consumed_qty,
									"bom_qty": flt(bom_item.qty),
								}
							)
							break
				except:
					pass

		# If we need to produce this item, traverse BOM (this will allocate stock from child items)
		if other_required_qty > 0:
			traverse_bom_for_po(
				other_item_code,
				other_required_qty,
				po_recommendations_all,
				remaining_stock,
				set(),
				item_groups_cache,
				level=0,
			)

	# Now calculate for our target item using remaining stock (after all other items have been processed)
	available_stock = flt(remaining_stock.get(item_code, 0))
	required_qty = max(0, so_qty - available_stock)

	# Allocate stock
	allocated = min(so_qty, available_stock)
	remaining_stock[item_code] = available_stock - allocated

	# Get item details
	item_doc = frappe.get_doc("Item", item_code)
	item_group = item_doc.get("item_group")

	initial_stock = flt(initial_stock_map.get(item_code, 0))

	debug_info = {
		"item_code": item_code,
		"item_name": item_doc.get("item_name"),
		"item_group": item_group,
		"is_raw_material": item_group == "Raw Material",
		"sales_order_qty": so_qty,
		"initial_stock": initial_stock,
		"available_stock": available_stock,
		"allocated_stock": allocated,
		"remaining_stock_after_allocation": remaining_stock[item_code],
		"po_recommendation": required_qty,
		"calculation": f"max(0, {so_qty} - {available_stock}) = {required_qty}",
		"stock_consumers": stock_consumers,
		"stock_consumed_by_others": sum(c["consumed_qty"] for c in stock_consumers),
		"bom_traversal": [],
	}

	# If we need to produce this item, traverse BOM
	if required_qty > 0:
		po_recommendations = {item_code: required_qty}
		item_groups_cache = {item_code: item_group}

		debug_info["bom_traversal"] = traverse_bom_for_debug(
			item_code, required_qty, po_recommendations, remaining_stock, set(), item_groups_cache, level=0
		)
		debug_info["all_po_recommendations"] = po_recommendations

	return debug_info


@frappe.whitelist()
def create_material_request(item_code, qty):
	"""
	Create and submit a Material Request for the given item_code and quantity
	"""
	if not item_code:
		return {"error": "Item code is required"}

	if not qty or flt(qty) <= 0:
		return {"error": "Quantity must be greater than 0"}

	# Get item details
	if not frappe.db.exists("Item", item_code):
		return {"error": f"Item {item_code} not found"}

	item_doc = frappe.get_doc("Item", item_code)

	# Get UOM from item
	uom = item_doc.get("uom")
	if not uom:
		# If uom is not set, use stock_uom
		uom = item_doc.get("stock_uom")

	if not uom:
		return {"error": f"UOM not found for item {item_code}"}

	# Get stock_uom from item
	stock_uom = item_doc.get("stock_uom")
	if not stock_uom:
		return {"error": f"Stock UOM not found for item {item_code}"}

	# Get UOM conversion factor from item
	conversion_factor = 1.0
	if uom != stock_uom:
		# Try to get conversion factor from UOM Conversion Detail child table
		for uom_detail in item_doc.get("uoms", []):
			if uom_detail.uom == uom:
				conversion_factor = flt(uom_detail.conversion_factor)
				break

		# If not found in child table, check if item has uom_conversion_factor field
		if conversion_factor == 1.0 and hasattr(item_doc, "uom_conversion_factor"):
			conversion_factor = flt(item_doc.get("uom_conversion_factor", 1.0))

	# Calculate schedule_date (7 days from now)
	from frappe.utils import add_days, today

	schedule_date = add_days(today(), 7)

	# Set company name
	company = "Prakash Steel Products Pvt Ltd"

	# Verify company exists
	if not frappe.db.exists("Company", company):
		return {"error": f"Company '{company}' not found in the system."}

	try:
		# Set warehouse
		warehouse = "Bright Bar Unit - PSPL"

		# Verify warehouse exists
		if not frappe.db.exists("Warehouse", warehouse):
			return {"error": f"Warehouse '{warehouse}' not found in the system."}

		# Create Material Request
		mr_doc = frappe.get_doc(
			{
				"doctype": "Material Request",
				"company": company,
				"transaction_date": today(),
				"schedule_date": schedule_date,
				"material_request_type": "Purchase",
				"items": [
					{
						"item_code": item_code,
						"qty": flt(qty),
						"uom": uom,
						"stock_uom": stock_uom,
						"conversion_factor": conversion_factor,
						"warehouse": warehouse,
					}
				],
			}
		)

		mr_doc.insert()
		mr_doc.submit()

		return {
			"material_request": mr_doc.name,
			"message": f"Material Request {mr_doc.name} created and submitted successfully",
		}
	except Exception as e:
		frappe.log_error(f"Error creating Material Request: {str(e)}", "Create Material Request Error")
		return {"error": f"Error creating Material Request: {str(e)}"}


@frappe.whitelist()
def create_material_requests_automatically(filters=None):
	"""
	Create Material Requests automatically for all items with net_po_recommendation > 0
	"""
	# Parse filters if it's a JSON string
	if isinstance(filters, str):
		import json

		try:
			filters = json.loads(filters)
		except:
			filters = {}

	if not filters:
		filters = {}

	# Get report data
	_, data = execute(filters)

	if not data:
		return {
			"success_count": 0,
			"error_count": 0,
			"material_requests": [],
			"message": "No data found in report",
		}

	# Filter items with net_po_recommendation > 0
	items_to_process = [
		row
		for row in data
		if row.get("net_po_recommendation") and flt(row.get("net_po_recommendation", 0)) > 0
	]

	if not items_to_process:
		return {
			"success_count": 0,
			"error_count": 0,
			"material_requests": [],
			"message": "No items with Net PO Recommendation > 0 found",
		}

	success_count = 0
	error_count = 0
	material_requests = []
	errors = []

	# Create Material Request for each item
	for row in items_to_process:
		item_code = row.get("item_code")
		qty = flt(row.get("net_po_recommendation", 0))

		if not item_code or qty <= 0:
			error_count += 1
			errors.append(f"{item_code}: Invalid quantity")
			continue

		try:
			result = create_material_request(item_code, qty)
			if result.get("error"):
				error_count += 1
				errors.append(f"{item_code}: {result.get('error')}")
			else:
				success_count += 1
				material_requests.append(result.get("material_request"))
		except Exception as e:
			error_count += 1
			errors.append(f"{item_code}: {str(e)}")
			frappe.log_error(
				f"Error creating Material Request for {item_code}: {str(e)}",
				"Create Material Requests Automatically Error",
			)

	return {
		"success_count": success_count,
		"error_count": error_count,
		"material_requests": material_requests,
		"errors": errors[:10] if len(errors) > 10 else errors,  # Limit errors to first 10
		"message": f"Created {success_count} Material Request(s), {error_count} failed",
	}


def traverse_bom_for_debug(
	item_code, required_qty, po_recommendations, remaining_stock, visited_items, item_groups_cache, level=0
):
	"""Traverse BOM and return debug details for console display - uses remaining_stock"""
	if item_code in visited_items:
		return []

	visited_items.add(item_code)

	# Check item_group
	item_group = item_groups_cache.get(item_code)
	if not item_group:
		try:
			item_doc = frappe.get_doc("Item", item_code)
			item_group = item_doc.get("item_group")
			item_groups_cache[item_code] = item_group
		except:
			item_group = None

	# If Raw Material, stop
	if item_group == "Raw Material":
		return []

	bom = get_default_bom(item_code)
	if not bom:
		return []

	details = []
	try:
		bom_doc = frappe.get_doc("BOM", bom)

		for bom_item in bom_doc.items:
			child_item_code = bom_item.item_code
			bom_qty = flt(bom_item.qty)
			child_required_qty = required_qty * bom_qty

			# Get remaining available stock
			child_available_stock = flt(remaining_stock.get(child_item_code, 0))
			if child_item_code not in remaining_stock:
				stock_data = frappe.db.sql(
					"SELECT SUM(actual_qty) as stock FROM `tabBin` WHERE item_code = %s",
					(child_item_code,),
					as_dict=True,
				)
				child_available_stock = flt(stock_data[0].stock if stock_data else 0)
				remaining_stock[child_item_code] = child_available_stock

			# Allocate stock
			allocated = min(child_required_qty, child_available_stock)
			remaining_stock[child_item_code] = child_available_stock - allocated
			child_po = max(0, child_required_qty - allocated)

			# Get child item group
			child_item_group = item_groups_cache.get(child_item_code)
			if not child_item_group:
				try:
					child_item_doc = frappe.get_doc("Item", child_item_code)
					child_item_group = child_item_doc.get("item_group")
					item_groups_cache[child_item_code] = child_item_group
				except:
					child_item_group = None

			if child_item_code in po_recommendations:
				po_recommendations[child_item_code] += child_po
			else:
				po_recommendations[child_item_code] = child_po

			child_detail = {
				"level": level,
				"item_code": child_item_code,
				"item_name": frappe.db.get_value("Item", child_item_code, "item_name"),
				"item_group": child_item_group,
				"is_raw_material": child_item_group == "Raw Material",
				"bom_qty": bom_qty,
				"parent_required_qty": required_qty,
				"child_required_qty": child_required_qty,
				"calculation": f"{required_qty} (parent) × {bom_qty} (BOM qty) = {child_required_qty}",
				"available_stock": child_available_stock,
				"allocated_stock": allocated,
				"remaining_stock_after_allocation": remaining_stock[child_item_code],
				"po_recommendation": child_po,
				"po_calculation": f"max(0, {child_required_qty} - {allocated}) = {child_po}",
				"children": [],
			}

			if child_po > 0 and child_item_group != "Raw Material":
				child_detail["children"] = traverse_bom_for_debug(
					child_item_code,
					child_po,
					po_recommendations,
					remaining_stock,
					visited_items.copy(),
					item_groups_cache,
					level + 1,
				)

			details.append(child_detail)
	except Exception as e:
		frappe.log_error(f"Error in BOM traversal for {item_code}: {str(e)}", "PO Recommendation Debug Error")

	return details


def get_stock_map(item_codes):
	"""Get stock map for all items"""
	if not item_codes:
		return {}

	if len(item_codes) == 1:
		item_codes_tuple = (next(iter(item_codes)),)
	else:
		item_codes_tuple = tuple(item_codes)

	bin_rows = frappe.db.sql(
		"""
		SELECT item_code, SUM(actual_qty) as stock
		FROM `tabBin`
		WHERE item_code IN %s
		GROUP BY item_code
		""",
		(item_codes_tuple,),
		as_dict=True,
	)

	return {d.item_code: flt(d.stock) for d in bin_rows}


def get_sales_order_qty_map(filters):
	"""Get sales order qty map for ALL items
	Open SO = qty - delivered_qty (quantity left to deliver)
	Includes ALL sales orders with the item, regardless of date range
	"""
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


def get_qualified_demand_map(filters):
	"""Get qualified demand map for ALL items
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


def get_wip_map(filters):
	"""Get WIP (Work In Progress) map - sum of (qty - produced_qty) from Work Order (where status is not Completed or Cancelled)
	for ALL items (all-time data)

	Note: We use only Work Order WIP to avoid double-counting, as work_order_qty in Sales Order Items
	typically reflects the same Work Order quantity. We calculate remaining quantity as qty - produced_qty.

	This function now checks Production Plan Settings to determine which method to use:
	- If "from_work_order" is checked: uses Work Order based calculation (existing logic)
	- If "from_production_plan" is checked: uses Production Plan based calculation (new logic)
	"""
	# Get Production Plan Settings
	try:
		settings = frappe.get_single("Production planning settings")
	except Exception:
		# If settings don't exist, default to work order method
		settings = frappe._dict({"from_work_order": 1, "from_production_plan": 0})

	wip_map = {}

	# Check which method is selected
	if settings.get("from_work_order"):
		# Existing logic: Get WIP from Work Order (qty - produced_qty) - only for Work Orders that are not Completed or Cancelled
		wip_rows_wo = frappe.db.sql(
			"""
			SELECT
				wo.production_item as item_code,
				SUM(GREATEST(0, IFNULL(wo.qty, 0) - IFNULL(wo.produced_qty, 0))) as wip_qty
			FROM
				`tabWork Order` wo
			WHERE
				wo.status NOT IN ('Completed', 'Cancelled')
				AND wo.docstatus = 1
			GROUP BY
				wo.production_item
			""",
			as_dict=True,
		)

		# Build WIP map from Work Orders only
		for row in wip_rows_wo:
			item_code = row.item_code
			wip_map[item_code] = flt(row.wip_qty)

	elif settings.get("from_production_plan"):
		# New logic: Get WIP from Production Plan
		# Get all Production Plans
		production_plans = frappe.get_all("Production Plan", filters={"docstatus": 1}, fields=["name"])

		for pp in production_plans:
			pp_name = pp.name

			# Get Production Plan document to access po_items child table
			try:
				pp_doc = frappe.get_doc("Production Plan", pp_name)

				# Check if po_items child table exists
				if hasattr(pp_doc, "po_items") and pp_doc.po_items:
					# Iterate through each item in po_items
					for po_item in pp_doc.po_items:
						item_code = po_item.item_code
						planned_qty = flt(po_item.planned_qty) if po_item.planned_qty else 0

						if not item_code:
							continue

						# Get all submitted Finished Weight documents linked to this Production Plan
						# Sum all finish_weight values
						finished_weight_sum = frappe.db.sql(
							"""
							SELECT COALESCE(SUM(finish_weight), 0) as total_finish_weight
							FROM `tabFinish Weight`
							WHERE production_plan = %s
							AND docstatus = 1
							AND item_code = %s
							""",
							(pp_name, item_code),
							as_dict=True,
						)

						total_finished = (
							flt(finished_weight_sum[0].total_finish_weight) if finished_weight_sum else 0
						)

						# Calculate WIP: planned_qty - sum of all finish_weight
						wip_qty = max(0, planned_qty - total_finished)  # Ensure non-negative

						# Add to wip_map (sum if item_code already exists from another production plan)
						if item_code in wip_map:
							wip_map[item_code] += wip_qty
						else:
							wip_map[item_code] = wip_qty

			except Exception as e:
				frappe.log_error(
					f"Error processing Production Plan {pp_name} in get_wip_map: {str(e)}",
					"PO Recommendation WIP Calculation Error",
				)
				continue

	return wip_map


def get_mrq_map(filters):
	"""Get MRQ (Material Request Quantity) map - sum of remaining qty from Material Request Items
	for all items (Material Requests with status 'Pending' or 'Partially Ordered')
	Remaining qty = qty - ordered_qty (to get the quantity that still needs to be ordered)
	"""
	# Get Material Requests with status 'Pending' or 'Partially Ordered'
	mrq_rows = frappe.db.sql(
		"""
		SELECT
			mri.item_code,
			SUM(GREATEST(0, mri.qty - IFNULL(mri.ordered_qty, 0))) as mrq_qty
		FROM
			`tabMaterial Request` mr
		INNER JOIN
			`tabMaterial Request Item` mri ON mri.parent = mr.name
		WHERE
			mr.docstatus = 1
			AND mr.status IN ('Pending', 'Partially Ordered')
		GROUP BY
			mri.item_code
		""",
		as_dict=True,
	)

	return {d.item_code: flt(d.mrq_qty) for d in mrq_rows}


def get_open_po_map():
	"""Get Open PO (Purchase Order) map - sum of (qty - received_qty) from Purchase Order Items
	for all items. If (qty - received_qty) is negative for a particular PO, treat it as 0.
	Only includes submitted Purchase Orders that are not cancelled.
	"""
	# Get all Purchase Order Items with their qty and received_qty
	po_rows = frappe.db.sql(
		"""
		SELECT
			poi.item_code,
			poi.qty,
			IFNULL(poi.received_qty, 0) as received_qty
		FROM
			`tabPurchase Order` po
		INNER JOIN
			`tabPurchase Order Item` poi ON poi.parent = po.name
		WHERE
			po.docstatus = 1
			AND po.status NOT IN ('Cancelled', 'Closed')
		""",
		as_dict=True,
	)

	# Calculate open_po for each item
	# For each PO item: if (qty - received_qty) < 0, treat as 0, otherwise use (qty - received_qty)
	open_po_map = {}
	for row in po_rows:
		item_code = row.item_code
		qty = flt(row.qty)
		received_qty = flt(row.received_qty)
		open_qty = max(0, qty - received_qty)  # If negative, treat as 0

		if item_code in open_po_map:
			open_po_map[item_code] += open_qty
		else:
			open_po_map[item_code] = open_qty

	return open_po_map


def traverse_bom_for_parent_demand_simple(
	parent_item_code,
	parent_net_order_qty,
	parent_demand_map,
	visited_items,
	item_groups_cache,
	item_buffer_map,
	level=0,
):
	"""
	Simple BOM traversal for first pass - just accumulates parent demands.
	Same logic as mrp_genaration.py traverse_bom_for_mrp (first traversal).
	"""
	if parent_item_code in visited_items:
		return

	visited_items.add(parent_item_code)

	# Check item_group - if Raw Material, stop BOM traversal
	item_group = item_groups_cache.get(parent_item_code)
	if not item_group:
		try:
			item_doc = frappe.get_doc("Item", parent_item_code)
			item_group = item_doc.get("item_group")
			item_groups_cache[parent_item_code] = item_group
		except:
			item_group = None

	if item_group == "Raw Material":
		return

	# Get BOM for this item
	bom = get_default_bom(parent_item_code)
	if not bom:
		return

	try:
		bom_doc = frappe.get_doc("BOM", bom)
		bom_quantity = flt(bom_doc.quantity)
		if bom_quantity <= 0:
			bom_quantity = 1.0

		for bom_item in bom_doc.items:
			child_item_code = bom_item.item_code
			bom_item_qty = flt(bom_item.qty)

			normalized_bom_qty = bom_item_qty / bom_quantity
			child_required_qty = parent_net_order_qty * normalized_bom_qty

			# Check if child is buffer or non-buffer
			child_buffer_flag = item_buffer_map.get(child_item_code, "Non-Buffer")
			is_child_buffer = child_buffer_flag == "Buffer"

			if not is_child_buffer:
				# Non-buffer child: Add parent demand
				if child_item_code in parent_demand_map:
					parent_demand_map[child_item_code] += child_required_qty
				else:
					parent_demand_map[child_item_code] = child_required_qty

			# Recursively traverse child's BOM
			if child_item_code not in visited_items:
				traverse_bom_for_parent_demand_simple(
					child_item_code,
					child_required_qty,
					parent_demand_map,
					visited_items.copy(),
					item_groups_cache,
					item_buffer_map,
					level + 1,
				)
	except Exception as e:
		frappe.log_error(f"Error traversing BOM for {parent_item_code}: {str(e)}", "PO Recommendation Error")


def traverse_bom_for_parent_demand(
	parent_item_code,
	parent_net_order_qty,
	parent_demand_map,
	parent_demand_details,
	visited_items,
	item_groups_cache,
	open_so_map,
	stock_map,
	wip_map,
	open_po_map,
	mrq_map,
	moq_map,
	batch_size_map,
	item_buffer_map,
	item_sku_type_map,
	get_item_details_func,
	level=0,
):
	"""
	Recursively traverse BOM using net_order_recommendations (after MOQ/Batch Size).
	Same logic as mrp_genaration.py traverse_bom_for_mrp_with_net_rec.
	This ensures children get the adjusted values from their parents.

	Args:
		parent_item_code: Item code of parent item
		parent_net_order_qty: Net order recommendation for parent item (after MOQ/Batch Size)
		parent_demand_map: Dict to accumulate parent demands (item_code -> total parent demand)
		parent_demand_details: Dict to track parent demand details
		visited_items: Set of visited items to prevent circular references
		item_groups_cache: Dict to cache item_group lookups
		open_so_map: Map of item_code -> open SO quantity
		stock_map: Map of item_code -> stock quantity
		wip_map: Map of item_code -> WIP quantity
		open_po_map: Map of item_code -> open PO quantity
		mrq_map: Map of item_code -> MRQ quantity
		moq_map: Map of item_code -> MOQ
		batch_size_map: Map of item_code -> Batch Size
		item_buffer_map: Map of item_code -> buffer flag
		item_sku_type_map: Map of item_code -> SKU type
		get_item_details_func: Function to get item details
		level: Recursion depth
	"""
	if parent_item_code in visited_items:
		return

	visited_items.add(parent_item_code)

	# Check item_group - if Raw Material, stop BOM traversal
	item_group = item_groups_cache.get(parent_item_code)
	if not item_group:
		try:
			item_doc = frappe.get_doc("Item", parent_item_code)
			item_group = item_doc.get("item_group")
			item_groups_cache[parent_item_code] = item_group
		except:
			item_group = None

	# If it's a Raw Material, stop BOM traversal (end of branch)
	if item_group == "Raw Material":
		return

	# Get BOM for this item
	bom = get_default_bom(parent_item_code)
	if not bom:
		return

	try:
		bom_doc = frappe.get_doc("BOM", bom)
		bom_quantity = flt(bom_doc.quantity)  # Quantity of parent item produced by this BOM
		if bom_quantity <= 0:
			bom_quantity = 1.0  # Default to 1 if BOM quantity is 0 or negative

		# Process each child item in BOM
		for bom_item in bom_doc.items:
			child_item_code = bom_item.item_code
			bom_item_qty = flt(bom_item.qty)  # Quantity of child item needed in BOM

			# Calculate required qty for child: parent_net_order_qty * (bom_item_qty / bom_quantity)
			# This normalizes the BOM item quantity to "per unit of parent item produced"
			# This uses the net_order_recommendation (after MOQ/Batch Size) of parent
			normalized_bom_qty = bom_item_qty / bom_quantity
			child_required_qty = parent_net_order_qty * normalized_bom_qty

			# Get child item details (populate maps if needed)
			get_item_details_func(child_item_code)
			child_buffer_flag = item_buffer_map.get(child_item_code, "Non-Buffer")
			is_child_buffer = child_buffer_flag == "Buffer"

			if is_child_buffer:
				# Buffer child: Don't add parent demand (they use TOG + Qualified Demand calculation)
				# But record it for logging
				if child_item_code not in parent_demand_details:
					parent_demand_details[child_item_code] = []
				parent_demand_details[child_item_code].append(
					{
						"parent_item": parent_item_code,
						"bom_name": bom_doc.name,
						"demand_qty": child_required_qty,
						"applied": False,
						"reason": f"Buffer item - parent demand ignored (from net_order_rec: {parent_net_order_qty})",
					}
				)
			else:
				# Non-buffer child: Add parent demand to requirement
				# Record parent demand
				if child_item_code not in parent_demand_details:
					parent_demand_details[child_item_code] = []
				parent_demand_details[child_item_code].append(
					{
						"parent_item": parent_item_code,
						"bom_name": bom_doc.name,
						"demand_qty": child_required_qty,
						"applied": True,
						"reason": f"From parent {parent_item_code} (Net Order Qty: {parent_net_order_qty}) × (BOM Item Qty: {bom_item_qty} / BOM Qty: {bom_quantity}) = {normalized_bom_qty:.4f}",
					}
				)

				# Accumulate parent demand (same item can appear in multiple BOMs)
				if child_item_code in parent_demand_map:
					parent_demand_map[child_item_code] += child_required_qty
				else:
					parent_demand_map[child_item_code] = child_required_qty

				# Calculate order recommendation for child item (with parent demand)
				# For non-buffer items, use qualified_demand (Open SO with delivery_date <= today) instead of all-time open_so
				# Note: open_so_map parameter is actually qualified_demand_map when called from Step 5
				child_qualified_demand = flt(
					open_so_map.get(child_item_code, 0)
				)  # This is qualified_demand_map
				child_parent_demand = flt(parent_demand_map.get(child_item_code, 0))
				child_requirement = child_qualified_demand + child_parent_demand
				child_stock = flt(stock_map.get(child_item_code, 0))
				child_wip = flt(wip_map.get(child_item_code, 0))
				child_sku_type = item_sku_type_map.get(child_item_code)
				child_open_po = flt(open_po_map.get(child_item_code, 0))
				child_mrq = flt(mrq_map.get(child_item_code, 0))

				if child_sku_type in ["PTO", "BOTO"]:
					base_child_order_rec = child_requirement - child_stock - child_wip - child_open_po
				else:
					base_child_order_rec = child_requirement - child_stock - child_wip

				# Subtract MRQ from base order recommendation
				child_base_order_rec = max(0, base_child_order_rec - child_mrq)

				# Apply MOQ/Batch Size to get net_order_recommendation
				child_moq = flt(moq_map.get(child_item_code, 0))
				child_batch_size = flt(batch_size_map.get(child_item_code, 0))
				child_net_order_rec = calculate_net_order_recommendation(
					child_base_order_rec, child_moq, child_batch_size
				)

				# If child has net_order_recommendation > 0, traverse its BOM recursively
				if child_net_order_rec > 0 and child_item_code not in visited_items:
					traverse_bom_for_parent_demand(
						child_item_code,
						child_net_order_rec,
						parent_demand_map,
						parent_demand_details,
						visited_items.copy(),
						item_groups_cache,
						open_so_map,
						stock_map,
						wip_map,
						open_po_map,
						mrq_map,
						moq_map,
						batch_size_map,
						item_buffer_map,
						item_sku_type_map,
						get_item_details_func,
						level + 1,
					)

	except Exception as e:
		frappe.log_error(
			f"Error traversing BOM for parent demand for item {parent_item_code}: {str(e)}",
			"PO Recommendation Error",
		)


def traverse_bom_for_po(
	item_code, required_qty, po_recommendations, remaining_stock, visited_items, item_groups_cache, level=0
):
	"""
	Recursively traverse BOM to calculate PO recommendations for child items
	Uses remaining_stock which tracks available stock after allocations

	Args:
		item_code: Item code to process
		required_qty: Quantity needed of this item
		po_recommendations: Dict to store PO recommendations (item_code -> qty)
		remaining_stock: Dict of remaining available stock (item_code -> stock) - will be reduced as items are allocated
		visited_items: Set of visited items to prevent circular references
		item_groups_cache: Dict to cache item_group lookups
		level: Recursion depth
	"""
	if item_code in visited_items:
		return

	visited_items.add(item_code)

	# Check item_group - if Raw Material, stop BOM traversal
	item_group = item_groups_cache.get(item_code)
	if not item_group:
		try:
			item_doc = frappe.get_doc("Item", item_code)
			item_group = item_doc.get("item_group")
			item_groups_cache[item_code] = item_group
		except:
			item_group = None

	# If it's a Raw Material, stop BOM traversal (end of branch)
	if item_group == "Raw Material":
		return

	# Get BOM for this item
	bom = get_default_bom(item_code)
	if not bom:
		return

	try:
		bom_doc = frappe.get_doc("BOM", bom)

		# Process each child item in BOM
		for bom_item in bom_doc.items:
			child_item_code = bom_item.item_code
			bom_qty = flt(bom_item.qty)

			# Calculate required qty for child: required_qty of parent * bom_qty
			child_required_qty = required_qty * bom_qty

			# Get remaining available stock for child item
			child_available_stock = flt(remaining_stock.get(child_item_code, 0))

			# If stock not in map, fetch initial stock
			if child_item_code not in remaining_stock:
				stock_data = frappe.db.sql(
					"""
					SELECT SUM(actual_qty) as stock
					FROM `tabBin`
					WHERE item_code = %s
					""",
					(child_item_code,),
					as_dict=True,
				)
				child_available_stock = flt(stock_data[0].stock if stock_data else 0)
				remaining_stock[child_item_code] = child_available_stock

			# Allocate stock: use what we can from remaining stock
			allocated = min(child_required_qty, child_available_stock)
			remaining_stock[child_item_code] = child_available_stock - allocated

			# Calculate PO recommendation for child (what we still need after allocation)
			child_po = max(0, child_required_qty - allocated)

			# Add to PO recommendations (sum if already exists - same item may appear in multiple BOMs or have its own SO)
			if child_item_code in po_recommendations:
				po_recommendations[child_item_code] += child_po
			else:
				po_recommendations[child_item_code] = child_po

			# If we need to produce this child item, traverse its BOM recursively
			# Only traverse if stock is insufficient (child_po > 0)
			if child_po > 0:
				traverse_bom_for_po(
					child_item_code,
					child_po,
					po_recommendations,
					remaining_stock,
					visited_items.copy(),
					item_groups_cache,
					level + 1,
				)

	except Exception as e:
		frappe.log_error(f"Error traversing BOM for item {item_code}: {str(e)}", "PO Recommendation Error")
