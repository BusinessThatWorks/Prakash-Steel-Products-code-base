# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from prakash_steel.utils.lead_time import calculate_decoupled_lead_time


@frappe.whitelist()
def check_custom_field_exists():
	"""API method to check if custom_decoupled_lead_time field exists in database"""
	try:
		db_name = frappe.conf.db_name
		result = frappe.db.sql(
			"""
			SELECT COUNT(*) as count
			FROM information_schema.COLUMNS 
			WHERE TABLE_SCHEMA = %s 
			AND TABLE_NAME = 'tabItem' 
			AND COLUMN_NAME = 'custom_decoupled_lead_time'
			""",
			(db_name,),
			as_dict=True,
		)

		column_exists = result and result[0]["count"] > 0

		response = {
			"column_exists": column_exists,
			"message": "Column exists" if column_exists else "Column does not exist",
		}

		if column_exists:
			# Get sample data
			sample = frappe.db.sql(
				"""
				SELECT name, custom_decoupled_lead_time 
				FROM `tabItem` 
				WHERE custom_decoupled_lead_time IS NOT NULL 
				AND custom_decoupled_lead_time != 0
				LIMIT 5
				""",
				as_dict=True,
			)
			response["sample_items"] = sample

			# Get counts
			total = frappe.db.sql("SELECT COUNT(*) as count FROM `tabItem`", as_dict=True)[0]["count"]
			with_values = frappe.db.sql(
				"SELECT COUNT(*) as count FROM `tabItem` WHERE custom_decoupled_lead_time IS NOT NULL AND custom_decoupled_lead_time != 0",
				as_dict=True,
			)[0]["count"]
			response["total_items"] = total
			response["items_with_values"] = with_values

		return response
	except Exception as e:
		return {"error": str(e), "traceback": frappe.get_traceback()}


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "item_code",
			"label": "Item Code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data", "width": 200},
		{"fieldname": "lead_time_days", "label": "Lead Time", "fieldtype": "Float", "width": 120},
		{
			"fieldname": "custom_decoupled_lead_time",
			"label": "Replenish Time",
			"fieldtype": "Float",
			"width": 150,
		},
		{"fieldname": "custom_buffer_flag", "label": "Buffer Flag", "fieldtype": "Data", "width": 120},
	]


def _check_column_exists():
	"""Check if custom_decoupled_lead_time column exists in database"""
	try:
		db_name = frappe.conf.db_name
		result = frappe.db.sql(
			"""
			SELECT COUNT(*) 
			FROM information_schema.COLUMNS 
			WHERE TABLE_SCHEMA = %s 
			AND TABLE_NAME = 'tabItem' 
			AND COLUMN_NAME = 'custom_decoupled_lead_time'
			""",
			(db_name,),
		)
		return result and result[0][0] > 0
	except Exception:
		return False


def get_data(filters):
	"""Get report data based on filters"""
	data = []

	if not filters or not filters.get("bom"):
		return data

	bom_name = filters.get("bom")

	try:
		# Check if column exists
		column_exists = _check_column_exists()
		if not column_exists:
			frappe.msgprint(
				"Warning: custom_decoupled_lead_time column not found in database. "
				"You may need to run: bench migrate",
				indicator="orange",
			)

		# Get BOM document
		bom_doc = frappe.get_doc("BOM", bom_name)

		# Collect all item codes from BOM
		item_codes = [bom_item.item_code for bom_item in bom_doc.items]

		if not item_codes:
			return data

		# Query all items at once using SQL for better performance and reliability
		# Handle single item case for tuple
		if len(item_codes) == 1:
			item_codes_tuple = (item_codes[0],)
		else:
			item_codes_tuple = tuple(item_codes)

		# Build SQL query - include custom_decoupled_lead_time only if column exists
		if column_exists:
			items_data = frappe.db.sql(
				"""
				SELECT 
					name as item_code,
					item_name,
					lead_time_days,
					custom_decoupled_lead_time,
					custom_buffer_flag
				FROM `tabItem`
				WHERE name IN %s
				""",
				(item_codes_tuple,),
				as_dict=True,
			)
		else:
			# Column doesn't exist, query without it
			items_data = frappe.db.sql(
				"""
				SELECT 
					name as item_code,
					item_name,
					lead_time_days,
					NULL as custom_decoupled_lead_time,
					custom_buffer_flag
				FROM `tabItem`
				WHERE name IN %s
				""",
				(item_codes_tuple,),
				as_dict=True,
			)

		# Create a dictionary for quick lookup
		items_dict = {item["item_code"]: item for item in items_data}

		# Loop through BOM items in order and build data
		for bom_item in bom_doc.items:
			item_code = bom_item.item_code
			item_data = items_dict.get(item_code)

			if item_data:
				# Always calculate custom_decoupled_lead_time dynamically (like the UI does)
				# The UI always calculates it on-the-fly, so we do the same to ensure consistency
				try:
					decoupled_lead_time = calculate_decoupled_lead_time(item_code)
				except Exception as e:
					frappe.log_error(
						f"Error calculating decoupled lead time for item {item_code}: {str(e)}",
						"BOM Wise Buffer Details Report Error",
					)
					decoupled_lead_time = 0

				# Ensure it's a float
				decoupled_lead_time = flt(decoupled_lead_time or 0)

				row = {
					"item_code": item_code,
					"item_name": item_data.get("item_name") or "",
					"lead_time_days": flt(item_data.get("lead_time_days") or 0),
					"custom_decoupled_lead_time": decoupled_lead_time,
					"custom_buffer_flag": item_data.get("custom_buffer_flag") or "",
				}
				data.append(row)
			else:
				# Item doesn't exist, log and skip
				frappe.log_error(
					f"Item {item_code} does not exist in BOM {bom_name}",
					"BOM Wise Buffer Details Report Error",
				)

	except frappe.DoesNotExistError:
		frappe.throw(f"BOM {bom_name} does not exist")
	except Exception as e:
		frappe.log_error(f"Error processing BOM {bom_name}: {str(e)}", "BOM Wise Buffer Details Report Error")
		frappe.throw(f"Error processing BOM: {str(e)}")

	return data
