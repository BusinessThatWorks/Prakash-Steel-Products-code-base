# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class descsolverinsi(Document):
	pass


@frappe.whitelist()
def solve_desc_codes():
	# Get all SI items where custom_desc_code is missing, along with their item_code
	rows = frappe.db.sql(
		"""
		SELECT sii.name, sii.item_code
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE (sii.custom_desc_code IS NULL OR sii.custom_desc_code = '')
		  AND sii.item_code IS NOT NULL
		""",
		as_dict=True,
	)

	if not rows:
		return "No Sales Invoice items found with missing desc code."

	# Build a map of item_code -> custom_desc_code from Item master
	item_codes = list({r.item_code for r in rows})
	item_desc_map = {}
	for chunk_start in range(0, len(item_codes), 500):
		chunk = item_codes[chunk_start : chunk_start + 500]
		items = frappe.db.get_all(
			"Item",
			filters={"name": ["in", chunk]},
			fields=["name", "custom_desc_code"],
		)
		for item in items:
			if item.custom_desc_code:
				item_desc_map[item.name] = item.custom_desc_code

	updated = 0
	skipped = 0
	for row in rows:
		desc_code = item_desc_map.get(row.item_code)
		if desc_code:
			frappe.db.set_value(
				"Sales Invoice Item",
				row.name,
				"custom_desc_code",
				desc_code,
				update_modified=False,
			)
			updated += 1
		else:
			skipped += 1

	frappe.db.commit()

	msg = f"Updated <b>{updated}</b> rows."
	if skipped:
		msg += f" Skipped <b>{skipped}</b> rows (item has no desc code set in Item master)."
	return msg
