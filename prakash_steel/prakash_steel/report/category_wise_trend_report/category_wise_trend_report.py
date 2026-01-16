# Copyright (c) 2026, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, date_diff, add_days


def calculate_sku_type(buffer_flag, item_type):
	"""
	Calculate SKU type based on buffer_flag and item_type
	buffer_flag: 'Buffer' or 'Non-Buffer'
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
	if not filters:
		filters = {}
	
	# Return empty result if filters are not provided (initial load)
	if not filters.get("from_date") or not filters.get("to_date") or not filters.get("sku_type"):
		sku_type = filters.get("sku_type", "")
		label = f"{sku_type} Availability" if sku_type else "SKU Type Availability"
		return [{"fieldname": "category", "label": _(label), "fieldtype": "Data", "width": 200}], []
	
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	sku_type = filters.get("sku_type")
	
	if from_date > to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))
	
	# Generate date columns dynamically
	columns = get_columns(from_date, to_date, sku_type)
	
	# Get data
	data = get_data(from_date, to_date, sku_type)
	
	return columns, data


def get_columns(from_date, to_date, sku_type):
	"""Generate columns: {SKU Type} Availability, then one column for each date in range"""
	label = f"{sku_type} Availability"
	columns = [
		{
			"fieldname": "category",
			"label": _(label),
			"fieldtype": "Data",
			"width": 200
		}
	]
	
	# Add a column for each date in the range
	current_date = from_date
	while current_date <= to_date:
		date_str = current_date.strftime("%d %b %Y")
		fieldname = f"date_{current_date.strftime('%Y_%m_%d')}"
		
		columns.append({
			"fieldname": fieldname,
			"label": date_str,
			"fieldtype": "Data",
			"width": 120
		})
		
		current_date = add_days(current_date, 1)
	
	return columns


def get_data(from_date, to_date, sku_type):
	"""Query Item wise Daily On Hand Colour and build report data for categories"""
	
	# Get all dates in range
	date_list = []
	current_date = from_date
	while current_date <= to_date:
		date_list.append(current_date)
		current_date = add_days(current_date, 1)
	
	# Query Item wise Daily On Hand Colour for the date range
	parent_docs = frappe.db.sql("""
		SELECT name, posting_date
		FROM `tabItem wise Daily On Hand Colour`
		WHERE posting_date BETWEEN %s AND %s
		ORDER BY posting_date
	""", (from_date, to_date), as_dict=True)
	
	# Build a map: {date: {item_code: on_hand_colour}}
	date_item_colour_map = {}
	for date in date_list:
		date_item_colour_map[date] = {}
	
	# Process each parent document
	for parent_doc in parent_docs:
		posting_date = getdate(parent_doc.posting_date)
		
		# Get child table data for this parent
		child_data = frappe.db.sql("""
			SELECT item_code, on_hand_colour
			FROM `tabOn hand colour table`
			WHERE parent = %s AND sku_type = %s
		""", (parent_doc.name, sku_type), as_dict=True)
		
		# Store the on_hand_colour for each item on this date
		if posting_date in date_item_colour_map:
			for child in child_data:
				item_code = child.item_code
				on_hand_colour = child.on_hand_colour
				if item_code:
					date_item_colour_map[posting_date][item_code] = on_hand_colour or ""
	
	# Get all unique items across all dates for the selected SKU type
	all_items = set()
	for date in date_list:
		all_items.update(date_item_colour_map[date].keys())
	
	# Get current buffer status and item type for all items
	# Only include items that are currently buffer items with the selected SKU type
	valid_items = set()
	if all_items:
		items_data = frappe.db.sql("""
			SELECT name, item_name, custom_buffer_flag, custom_item_type
			FROM `tabItem`
			WHERE name IN ({})
		""".format(','.join(['%s'] * len(all_items))), tuple(all_items), as_dict=True)
		
		for item in items_data:
			buffer_flag = item.get("custom_buffer_flag") or "Non-Buffer"
			item_type = item.get("custom_item_type")
			current_sku_type = calculate_sku_type(buffer_flag, item_type)
			
			# Only include items that currently have the selected SKU type
			if current_sku_type == sku_type:
				valid_items.add(item.name)
	
	# Define the 5 categories
	categories = ["Black", "Red", "Yellow", "Green", "White"]
	
	# Build report data rows - one row for each category
	data = []
	for category in categories:
		row = {
			"category": category
		}
		
		# For each date, count items with this category's colour
		for date in date_list:
			fieldname = f"date_{date.strftime('%Y_%m_%d')}"
			count = 0
			
			# Count items that have this category's colour on this date
			for item_code in valid_items:
				on_hand_colour = date_item_colour_map[date].get(item_code, "")
				if on_hand_colour and on_hand_colour.strip().upper() == category.upper():
					count += 1
			
			row[fieldname] = count
		
		data.append(row)
	
	return data

