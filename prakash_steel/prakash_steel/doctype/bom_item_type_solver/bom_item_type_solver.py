# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BomItemtypesolver(Document):
	pass


@frappe.whitelist()
def solve_bom_item_types():
	"""
	For every BOM (all statuses including submitted/cancelled):
	  1. Fetch custom_item_type from the BOM's own item field -> update BOM.custom_item_type
	  2. For every row in BOM Items child table -> fetch custom_item_type from item_code -> update row
	Direct DB writes are used so submitted documents can be patched without re-submission.
	"""
	frappe.logger().info("BIT Solver: Starting solve_bom_item_types")

	# ── Step 1: build a map of item_code -> custom_item_type from Item master ──
	item_type_map = {}
	items = frappe.db.get_all(
		"Item",
		fields=["item_code", "custom_item_type"],
		filters=[["custom_item_type", "is", "set"]],
	)
	frappe.logger().info(f"BIT Solver: Found {len(items)} items with custom_item_type set")
	for row in items:
		item_type_map[row.item_code] = row.custom_item_type

	# ── Step 2: update BOM parent (custom_item_type comes from the 'item' field) ──
	boms = frappe.db.get_all("BOM", fields=["name", "item", "custom_item_type"])
	frappe.logger().info(f"BIT Solver: Total BOMs found: {len(boms)}")

	parent_updated = 0
	parent_skipped = 0

	for bom in boms:
		item_type = item_type_map.get(bom.item)
		if not item_type:
			frappe.logger().debug(
				f"BIT Solver: BOM {bom.name} -> item '{bom.item}' has no custom_item_type in Item master, skipping parent"
			)
			parent_skipped += 1
			continue

		if bom.custom_item_type == item_type:
			frappe.logger().debug(
				f"BIT Solver: BOM {bom.name} parent already has custom_item_type='{item_type}', skipping"
			)
			parent_skipped += 1
			continue

		frappe.logger().info(
			f"BIT Solver: BOM {bom.name} parent: '{bom.custom_item_type}' -> '{item_type}'"
		)
		frappe.db.set_value("BOM", bom.name, "custom_item_type", item_type, update_modified=False)
		parent_updated += 1

	frappe.logger().info(
		f"BIT Solver: BOM parent update done. Updated={parent_updated}, Skipped={parent_skipped}"
	)

	# ── Step 3: update BOM Item child rows ──
	bom_items = frappe.db.get_all(
		"BOM Item",
		fields=["name", "parent", "item_code", "custom_item_type"],
	)
	frappe.logger().info(f"BIT Solver: Total BOM Item rows found: {len(bom_items)}")

	child_updated = 0
	child_skipped = 0

	for row in bom_items:
		item_type = item_type_map.get(row.item_code)
		if not item_type:
			frappe.logger().debug(
				f"BIT Solver: BOM Item row {row.name} (parent={row.parent}) -> item_code '{row.item_code}' has no custom_item_type, skipping"
			)
			child_skipped += 1
			continue

		if row.custom_item_type == item_type:
			frappe.logger().debug(
				f"BIT Solver: BOM Item row {row.name} already has custom_item_type='{item_type}', skipping"
			)
			child_skipped += 1
			continue

		frappe.logger().info(
			f"BIT Solver: BOM Item row {row.name} (parent={row.parent}, item_code={row.item_code}): '{row.custom_item_type}' -> '{item_type}'"
		)
		frappe.db.set_value("BOM Item", row.name, "custom_item_type", item_type, update_modified=False)
		child_updated += 1

	frappe.db.commit()
	frappe.logger().info(
		f"BIT Solver: BOM Item child update done. Updated={child_updated}, Skipped={child_skipped}"
	)

	summary = {
		"parent_updated": parent_updated,
		"parent_skipped": parent_skipped,
		"child_updated": child_updated,
		"child_skipped": child_skipped,
	}
	frappe.logger().info(f"BIT Solver: Completed. Summary: {summary}")
	return summary
