# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from prakash_steel.utils.lead_time import update_decoupled_lead_time_for_item, get_default_bom


def update_decoupled_lead_time_on_item_save(doc, method=None):
	"""
	Update decoupled lead time when Item is saved.
	This ensures the value is always saved to the database.

	Args:
		doc: Item document
		method: Method name (for compatibility with doc_events)
	"""
	# Only update if item_code exists (not a new item being created)
	if not doc.name:
		return

	# Always update to ensure database has latest calculated value
	# This is safe because the calculation is idempotent
	try:
		update_decoupled_lead_time_for_item(doc.name)

		# If lead_time_days or custom_buffer_flag changed, also update parent items
		# (because this item's change affects parent items that use it in their BOM)
		if doc.has_value_changed("lead_time_days") or doc.has_value_changed("custom_buffer_flag"):
			_update_parent_items_lead_time(doc.name)
	except Exception as e:
		frappe.log_error(
			f"Error updating decoupled lead time for item {doc.name} on save: {str(e)}",
			"Item Lead Time Update Error",
		)


def update_decoupled_lead_time_on_bom_save(doc, method=None):
	"""
	Update decoupled lead time when BOM is saved/submitted.
	When BOM changes, the item's decoupled lead time needs to be recalculated.

	Args:
		doc: BOM document
		method: Method name (for compatibility with doc_events)
	"""
	# Only process submitted BOMs
	if doc.docstatus != 1:
		return

	# Update the main item's decoupled lead time
	if doc.item:
		try:
			update_decoupled_lead_time_for_item(doc.item)

			# Also update parent items that use this item in their BOM
			_update_parent_items_lead_time(doc.item)
		except Exception as e:
			frappe.log_error(
				f"Error updating decoupled lead time for item {doc.item} when BOM {doc.name} changed: {str(e)}",
				"BOM Lead Time Update Error",
			)


def _update_parent_items_lead_time(item_code):
	"""
	Update decoupled lead time for all parent items that use this item in their BOM.
	This is needed because when a child item's lead time changes, parent items are affected.

	Args:
		item_code: Item code whose parents need to be updated
	"""
	try:
		# Find all BOMs that use this item
		parent_boms = frappe.db.sql(
			"""
			SELECT DISTINCT b.item
			FROM `tabBOM` b
			INNER JOIN `tabBOM Item` bi ON b.name = bi.parent
			WHERE bi.item_code = %s
			AND b.is_active = 1
			AND b.docstatus = 1
			""",
			(item_code,),
			as_dict=True,
		)

		# Update each parent item
		for bom in parent_boms:
			parent_item = bom.item
			if parent_item:
				try:
					update_decoupled_lead_time_for_item(parent_item)
				except Exception as e:
					frappe.log_error(
						f"Error updating parent item {parent_item} lead time: {str(e)}",
						"Parent Item Lead Time Update Error",
					)
	except Exception as e:
		frappe.log_error(
			f"Error finding parent items for {item_code}: {str(e)}",
			"Parent Item Lead Time Update Error",
		)
