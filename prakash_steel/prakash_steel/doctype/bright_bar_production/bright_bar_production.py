# Copyright (c) 2026, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BrightBarProduction(Document):
	def on_submit(self):
		"""Create Stock Entry on submit"""
		print("=" * 50)
		print("Bright Bar Production on_submit called")
		print(f"Bright Bar Production Document: {self.name}")
		print(f"Raw Material: {self.raw_material}")
		print(f"Actual RM Consumption: {self.actual_rm_consumption}")
		print(f"RM Source Warehouse: {self.rm_source_warehouse}")
		print(f"Finished Good: {self.finished_good}")
		print(f"FG Weight: {self.fg_weight}")
		print(f"FG Target Warehouse: {self.fg_target_warehouse}")
		print(f"Production Date: {self.production_date}")
		print("=" * 50)

		# STOCK ENTRY CREATION COMMENTED OUT - WILL BE ENABLED LATER
		# try:
		# 	# Validate required fields
		# 	if not self.raw_material:
		# 		print("ERROR: raw_material is missing")
		# 		frappe.throw(_("Raw Material is required to create Stock Entry"))

		# 	if not self.actual_rm_consumption or self.actual_rm_consumption <= 0:
		# 		print("ERROR: actual_rm_consumption is missing or invalid")
		# 		frappe.throw(_("Actual RM Consumption must be greater than 0"))

		# 	if not self.rm_source_warehouse:
		# 		print("ERROR: rm_source_warehouse is missing")
		# 		frappe.throw(_("RM Source Warehouse is required to create Stock Entry"))

		# 	if not self.finished_good:
		# 		print("ERROR: finished_good is missing")
		# 		frappe.throw(_("Finished Good is required to create Stock Entry"))

		# 	if not self.fg_weight or self.fg_weight <= 0:
		# 		print("ERROR: fg_weight is missing or invalid")
		# 		frappe.throw(_("FG Weight must be greater than 0"))

		# 	if not self.fg_target_warehouse:
		# 		print("ERROR: fg_target_warehouse is missing")
		# 		frappe.throw(_("FG Target Warehouse is required to create Stock Entry"))

		# 	print("All validations passed, creating Stock Entry...")

		# 	# Get company from source warehouse
		# 	print(f"Getting company from warehouse: {self.rm_source_warehouse}")
		# 	warehouse_doc = frappe.get_doc("Warehouse", self.rm_source_warehouse)
		# 	company = warehouse_doc.company
		# 	print(f"Company from warehouse: {company}")

		# 	# Get item details for Raw Material UOM
		# 	print(f"Getting item details for raw material: {self.raw_material}")
		# 	rm_item_doc = frappe.get_doc("Item", self.raw_material)
		# 	rm_stock_uom = rm_item_doc.stock_uom or "Kg"
		# 	print(f"Raw Material Stock UOM: {rm_stock_uom}")

		# 	# Get item details for Finished Good UOM
		# 	print(f"Getting item details for finished good: {self.finished_good}")
		# 	fg_item_doc = frappe.get_doc("Item", self.finished_good)
		# 	fg_stock_uom = fg_item_doc.stock_uom or "Kg"
		# 	print(f"Finished Good Stock UOM: {fg_stock_uom}")

		# 	# Create Stock Entry with Manufacture type
		# 	print("Creating Stock Entry document...")
		# 	stock_entry_data = {
		# 		"doctype": "Stock Entry",
		# 		"stock_entry_type": "Manufacture",
		# 		"company": company,
		# 		"posting_date": self.production_date or frappe.utils.today(),
		# 		"posting_time": frappe.utils.nowtime(),
		# 		"items": [
		# 			{
		# 				"item_code": self.raw_material,
		# 				"qty": self.actual_rm_consumption,
		# 				"s_warehouse": self.rm_source_warehouse,
		# 				"t_warehouse": "",
		# 				"stock_uom": rm_stock_uom,
		# 				"uom": rm_stock_uom,
		# 				"conversion_factor": 1.0,
		# 				"is_finished_item": 0,
		# 			},
		# 			{
		# 				"item_code": self.finished_good,
		# 				"qty": self.fg_weight,
		# 				"s_warehouse": "",
		# 				"t_warehouse": self.fg_target_warehouse,
		# 				"stock_uom": fg_stock_uom,
		# 				"uom": fg_stock_uom,
		# 				"conversion_factor": 1.0,
		# 				"is_finished_item": 1,
		# 			},
		# 		],
		# 	}
		# 	print(f"Stock Entry data: {stock_entry_data}")

		# 	stock_entry = frappe.get_doc(stock_entry_data)
		# 	print("Stock Entry document created, inserting...")
		# 	stock_entry.insert()
		# 	print(f"Stock Entry inserted: {stock_entry.name}")

		# 	# Submit the stock entry
		# 	print("Submitting Stock Entry...")
		# 	stock_entry.submit()
		# 	print(f"Stock Entry submitted: {stock_entry.name}")

		# 	print(f"Stock Entry {stock_entry.name} created from Bright Bar Production {self.name}")

		# 	frappe.msgprint(
		# 		_("Stock Entry {0} created and submitted successfully").format(frappe.bold(stock_entry.name)),
		# 		indicator="green",
		# 		alert=True,
		# 	)

		# 	print("=" * 50)
		# 	print("Stock Entry creation completed successfully")
		# 	print("=" * 50)

		# except Exception as e:
		# 	print("=" * 50)
		# 	print(f"ERROR in Bright Bar Production on_submit: {str(e)}")
		# 	print(f"Error type: {type(e).__name__}")
		# 	import traceback

		# 	print(traceback.format_exc())
		# 	print("=" * 50)
		# 	frappe.log_error(
		# 		f"Error creating Stock Entry from Bright Bar Production {self.name}: {str(e)}",
		# 		"Bright Bar Production Stock Entry Creation Error",
		# 	)
		# 	frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))

		print("Stock Entry creation is currently commented out")
		print("=" * 50)
