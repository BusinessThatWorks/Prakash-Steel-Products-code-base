# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from prakash_steel.utils.lead_time import calculate_decoupled_lead_time


@frappe.whitelist()
def get_decoupled_lead_time(item_code):
	"""
	API method to get decoupled lead time for an item.
	This is called from the Item form to display the decoupled lead time.

	Args:
		item_code (str): Item code

	Returns:
		float: Decoupled lead time value
	"""
	if not item_code:
		return 0

	try:
		decoupled_lead_time = calculate_decoupled_lead_time(item_code)
		return decoupled_lead_time
	except Exception as e:
		frappe.log_error(
			f"Error calculating decoupled lead time for item {item_code}: {str(e)}",
			"Get Decoupled Lead Time Error",
		)
		return 0




