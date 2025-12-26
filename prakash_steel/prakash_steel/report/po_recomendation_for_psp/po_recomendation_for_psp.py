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


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
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
		{
			"label": _("TOG"),
			"fieldname": "tog",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("TOY"),
			"fieldname": "toy",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("TOR"),
			"fieldname": "tor",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Open SO"),
			"fieldname": "open_so",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Open PO"),
			"fieldname": "open_po",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("On Hand Stock"),
			"fieldname": "on_hand_stock",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("WIP"),
			"fieldname": "wip",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Qualify Demand"),
			"fieldname": "qualify_demand",
			"fieldtype": "Float",
			"width": 130,
		},
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
			"label": _("Production Order Recommendation"),
			"fieldname": "po_recommendation",
			"fieldtype": "Float",
			"width": 180,
		},
		{
			"label": _("Purchase Order Recommendation"),
			"fieldname": "purchase_order_recommendation",
			"fieldtype": "Float",
			"width": 180,
		},
		{
			"label": _("OR with Batch Size"),
			"fieldname": "or_with_batch_size",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Batch Size"),
			"fieldname": "batch_size",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("MOQ"),
			"fieldname": "moq",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("OR with MOQ"),
			"fieldname": "or_with_moq",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("MRQ"),
			"fieldname": "mrq",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Net PO Recommendation"),
			"fieldname": "net_po_recommendation",
			"fieldtype": "Float",
			"width": 180,
		},
	]
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

	# Get sales order qty map (for date range) - for ALL items
	so_qty_map = get_sales_order_qty_map(filters)

	# Filter to only buffer items that have sales orders
	# Get buffer items from database
	buffer_items = frappe.db.sql(
		"""
		SELECT name as item_code
		FROM `tabItem`
		WHERE custom_buffer_flag = 'Buffer'
		""",
		as_dict=1,
	)
	buffer_item_codes = set(item.item_code for item in buffer_items)

	# Filter sales order items to only buffer items
	so_qty_map = {k: v for k, v in so_qty_map.items() if k in buffer_item_codes}

	# Get WIP map (work_order_qty from sales order items)
	wip_map = get_wip_map(filters)

	# Get MRQ map (Material Request Quantity - sum of qty from Material Request Items)
	mrq_map = get_mrq_map(filters)

	# Get Open PO map (Purchase Order Quantity - sum of (qty - received_qty) from Purchase Order Items)
	open_po_map = get_open_po_map()

	# Get items with purchase orders (especially important for BOTA and PTA items)
	# BOTA and PTA items use open_po instead of open_so, so they need to be shown even without sales orders
	items_with_po = set(open_po_map.keys())
	# Filter to only buffer items that have purchase orders
	items_with_po_buffer = {item for item in items_with_po if item in buffer_item_codes}

	# Use ALL buffer items, plus any buffer items with purchase orders
	# This ensures BOTA and PTA items with purchase orders are shown even if they don't have sales orders
	all_items_to_process = buffer_item_codes | items_with_po_buffer

	if not all_items_to_process:
		return []

	# Get stock for all buffer items (including those with purchase orders)
	initial_stock_map = get_stock_map(all_items_to_process)

	# Create remaining_stock map - tracks available stock after allocations
	# Start with initial stock, will be reduced as items are allocated
	remaining_stock = dict(initial_stock_map)

	# Calculate PO recommendations with BOM traversal
	# po_recommendations will contain ALL items (buffer and non-buffer)
	po_recommendations = {}
	item_groups_cache = {}  # Cache item_group to check for Raw Material

	# Process each buffer item that has sales orders (for BOM traversal)
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

	# Show ALL buffer items, including those with purchase orders (especially BOTA and PTA)
	# BOTA and PTA items use open_po instead of open_so, so we need to include items with purchase orders
	# Since all_items_to_process already includes all buffer items, this ensures items with purchase orders are definitely included
	all_items_to_show = all_items_to_process

	# Get item details for all items to show
	if not all_items_to_show:
		return []

	# Build item codes tuple for SQL
	if len(all_items_to_show) == 1:
		item_codes_tuple = (list(all_items_to_show)[0],)
	else:
		item_codes_tuple = tuple(all_items_to_show)

	# Get item details with TOG, TOY, TOR, Item Type, Batch Size, MOQ, and Item Name (only buffer items)
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
			i.min_order_qty as moq
		FROM
			`tabItem` i
		WHERE
			i.name IN %s
			AND i.custom_buffer_flag = 'Buffer'
		""",
		(item_codes_tuple,),
		as_dict=1,
	)

	# Create a map for quick lookup
	items_map = {item.item_code: item for item in items_data}

	# Build final data list with all items (only buffer items)
	data = []
	for item_code in sorted(all_items_to_show):
		item_info = items_map.get(item_code, {})

		# Skip if item is not in items_map (i.e., not a buffer item)
		if not item_info:
			continue

		# Calculate SKU Type (all items are buffer, so use "Buffer" flag)
		item_type = item_info.get("item_type")
		sku_type = calculate_sku_type("Buffer", item_type)

		# Get stock and buffer levels
		on_hand_stock = flt(initial_stock_map.get(item_code, 0))
		tog = flt(item_info.get("tog", 0))
		toy = flt(item_info.get("toy", 0))
		tor = flt(item_info.get("tor", 0))
		qualify_demand = 0  # Calculation will be done later

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

		# Calculate PO Recommendation
		# For BOTA and PTA: use open_po instead of open_so in the formula
		# For others: use the standard formula (qualify_demand + tog - wip - on_hand_stock)
		if sku_type in ["BOTA", "PTA"]:
			# For BOTA/PTA: qualify_demand + tog - wip - on_hand_stock - open_po
			# (subtract open_po because it's already on order)
			po_recommendation = max(
				0, flt(qualify_demand) + flt(tog) - flt(wip) - flt(on_hand_stock) - flt(open_po)
			)
			purchase_order_recommendation = po_recommendation
			production_order_recommendation = 0
			# For BOTA and PTA, use purchase_order_recommendation for calculations
			base_qty_for_calc = purchase_order_recommendation
		else:
			# For others: qualify_demand + tog - wip - on_hand_stock
			po_recommendation = max(0, flt(qualify_demand) + flt(tog) - flt(wip) - flt(on_hand_stock))
			purchase_order_recommendation = 0
			production_order_recommendation = po_recommendation
			# For others, use production_order_recommendation for calculations
			base_qty_for_calc = production_order_recommendation

		# Calculate OR with Batch Size = ceil(base_qty / batch_size) * batch_size
		if batch_size > 0:
			or_with_batch_size = math.ceil(flt(base_qty_for_calc) / flt(batch_size)) * flt(batch_size)
		else:
			or_with_batch_size = base_qty_for_calc

		# Calculate OR with MOQ = ceil(base_qty / moq) * moq
		if moq > 0:
			or_with_moq = math.ceil(flt(base_qty_for_calc) / flt(moq)) * flt(moq)
		else:
			or_with_moq = base_qty_for_calc

		# Calculate Net PO Recommendation = base_qty - mrq
		net_po_recommendation = max(0, flt(base_qty_for_calc) - flt(mrq))

		row = {
			"item_code": item_code,
			"item_name": item_name,
			"sku_type": sku_type,
			"tog": tog,
			"toy": toy,
			"tor": tor,
			"open_so": flt(so_qty_map.get(item_code, 0)),
			"open_po": open_po,
			"on_hand_stock": on_hand_stock,
			"wip": wip,
			"qualify_demand": 0,
			"on_hand_status": on_hand_status,
			"on_hand_colour": on_hand_colour,
			"po_recommendation": production_order_recommendation,
			"purchase_order_recommendation": purchase_order_recommendation,
			"or_with_batch_size": or_with_batch_size,
			"batch_size": batch_size,
			"moq": moq,
			"or_with_moq": or_with_moq,
			"mrq": mrq,
			"net_po_recommendation": net_po_recommendation,
		}
		data.append(row)

	# Apply filters
	filtered_data = []
	for row in data:
		# Filter by SKU Type
		if filters.get("sku_type"):
			sku_type_filter = filters.get("sku_type")
			# Handle both list and comma-separated string
			if isinstance(sku_type_filter, str):
				sku_type_list = [s.strip() for s in sku_type_filter.split(",") if s.strip()]
			else:
				sku_type_list = sku_type_filter if isinstance(sku_type_filter, list) else [sku_type_filter]

			if row.get("sku_type") not in sku_type_list:
				continue

		# Filter by Item Code (exact match)
		if filters.get("item_code"):
			if row.get("item_code") != filters.get("item_code"):
				continue

		filtered_data.append(row)

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
		"date_range": f"{filters.get('from_date', 'N/A')} to {filters.get('to_date', 'N/A')}",
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
	columns, data = execute(filters)

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


@frappe.whitelist()
def get_calculation_details(filters=None):
	"""Get calculation details for browser console - similar to debug_lead_time_calculation"""
	if not filters:
		filters = {}

	# Re-run the calculation and collect details
	calculation_details = {
		"filters": filters,
		"items": [],
		"date_range": f"{filters.get('from_date', 'N/A')} to {filters.get('to_date', 'N/A')}",
	}

	# Get buffer items
	data = frappe.db.sql(
		"""
		SELECT DISTINCT i.name as item_code
		FROM `tabItem` i
		WHERE i.custom_buffer_flag = 'Buffer'
		ORDER BY i.name
		""",
		as_dict=1,
	)

	# Get stock map
	item_codes = [row.item_code for row in data]
	stock_map = get_stock_map(set(item_codes))

	# Get sales order qty map
	so_qty_map = get_sales_order_qty_map(filters)

	# Calculate PO recommendations
	po_recommendations = {}

	for row in data:
		item_code = row.item_code
		so_qty = flt(so_qty_map.get(item_code, 0))
		stock = flt(stock_map.get(item_code, 0))
		required_qty = max(0, so_qty - stock)
		po_recommendations[item_code] = required_qty

		item_detail = {
			"item_code": item_code,
			"sales_order_qty": so_qty,
			"stock": stock,
			"po_recommendation": required_qty,
			"bom_traversal": [],
		}

		# Traverse BOM if needed
		if required_qty > 0:
			item_detail["bom_traversal"] = traverse_bom_for_details(
				item_code, required_qty, po_recommendations, stock_map, set(), level=0
			)

		calculation_details["items"].append(item_detail)

	return calculation_details


def traverse_bom_for_details(item_code, required_qty, po_recommendations, stock_map, visited_items, level=0):
	"""Traverse BOM and return details for console display"""
	if item_code in visited_items:
		return []

	visited_items.add(item_code)
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

			child_stock = flt(stock_map.get(child_item_code, 0))
			if child_item_code not in stock_map:
				stock_data = frappe.db.sql(
					"SELECT SUM(actual_qty) as stock FROM `tabBin` WHERE item_code = %s",
					(child_item_code,),
					as_dict=True,
				)
				child_stock = flt(stock_data[0].stock if stock_data else 0)
				stock_map[child_item_code] = child_stock

			child_po = max(0, child_required_qty - child_stock)

			if child_item_code in po_recommendations:
				po_recommendations[child_item_code] += child_po
			else:
				po_recommendations[child_item_code] = child_po

			child_detail = {
				"level": level,
				"item_code": child_item_code,
				"bom_qty": bom_qty,
				"required_qty": child_required_qty,
				"stock": child_stock,
				"po_recommendation": child_po,
				"children": [],
			}

			if child_po > 0:
				child_detail["children"] = traverse_bom_for_details(
					child_item_code, child_po, po_recommendations, stock_map, visited_items.copy(), level + 1
				)

			details.append(child_detail)
	except Exception as e:
		frappe.log_error(f"Error in BOM traversal for {item_code}: {str(e)}", "PO Recommendation Error")

	return details


def get_stock_map(item_codes):
	"""Get stock map for all items"""
	if not item_codes:
		return {}

	if len(item_codes) == 1:
		item_codes_tuple = (list(item_codes)[0],)
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


def get_wip_map(filters):
	"""Get WIP (Work In Progress) map - sum of work_order_qty from sales order items
	and qty from Work Order (where status is not Completed or Cancelled)
	for ALL items (all-time data)
	"""
	# Get WIP from Sales Order items (work_order_qty) - all-time data
	wip_rows_so = frappe.db.sql(
		"""
		SELECT
			soi.item_code,
			SUM(IFNULL(soi.work_order_qty, 0)) as wip_qty
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

	# Get WIP from Work Order (qty field) - only for Work Orders that are not Completed or Cancelled
	wip_rows_wo = frappe.db.sql(
		"""
		SELECT
			wo.production_item as item_code,
			SUM(IFNULL(wo.qty, 0)) as wip_qty
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

	# Combine both sources
	wip_map = {}

	# Add Sales Order WIP
	for row in wip_rows_so:
		item_code = row.item_code
		wip_map[item_code] = flt(row.wip_qty)

	# Add Work Order WIP (sum if item already exists)
	for row in wip_rows_wo:
		item_code = row.item_code
		if item_code in wip_map:
			wip_map[item_code] += flt(row.wip_qty)
		else:
			wip_map[item_code] = flt(row.wip_qty)

	return wip_map


def get_mrq_map(filters):
	"""Get MRQ (Material Request Quantity) map - sum of qty from Material Request Items
	for all items (only Material Requests with status 'Pending')
	"""
	# Get only Material Requests with status 'Pending'
	mrq_rows = frappe.db.sql(
		"""
		SELECT
			mri.item_code,
			SUM(mri.qty) as mrq_qty
		FROM
			`tabMaterial Request` mr
		INNER JOIN
			`tabMaterial Request Item` mri ON mri.parent = mr.name
		WHERE
			mr.docstatus = 1
			AND mr.status = 'Pending'
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
