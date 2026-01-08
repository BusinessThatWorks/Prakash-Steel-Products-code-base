# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FinishWeight(Document):
	def on_submit(self):
		"""Create Stock Entry on submit"""
		print("=" * 50)
		print("Finish Weight on_submit called")
		print(f"Finish Weight Document: {self.name}")
		print(f"Item Code: {self.item_code}")
		print(f"Finish Weight (qty): {self.finish_weight}")
		print(f"FG Target Warehouse: {self.fg_target_warehouse}")
		print("=" * 50)
		
		try:
			# Validate required fields
			if not self.item_code:
				frappe.throw(_("Item Code is required to create Stock Entry"))
			
			if not self.finish_weight or self.finish_weight <= 0:
				frappe.throw(_("Finish Weight must be greater than 0"))
			
			if not self.fg_target_warehouse:
				frappe.throw(_("FG Target Warehouse is required to create Stock Entry"))
			
			print("All validations passed, creating Stock Entry...")
			
			# Get company from warehouse
			warehouse_doc = frappe.get_doc("Warehouse", self.fg_target_warehouse)
			company = warehouse_doc.company
			
			print(f"Company from warehouse: {company}")
			
			# Get item details for UOM
			item_doc = frappe.get_doc("Item", self.item_code)
			stock_uom = item_doc.stock_uom or "Nos"
			
			print(f"Item Stock UOM: {stock_uom}")
			
			# Create Stock Entry
			stock_entry = frappe.get_doc({
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": company,
				"posting_date": self.posting_date or frappe.utils.today(),
				"posting_time": frappe.utils.nowtime(),
				"items": [
					{
						"item_code": self.item_code,
						"qty": self.finish_weight,
						"t_warehouse": self.fg_target_warehouse,
						"stock_uom": stock_uom,
						"uom": stock_uom,
						"conversion_factor": 1.0
					}
				]
			})
			
			print("Stock Entry document created, inserting...")
			stock_entry.insert()
			print(f"Stock Entry inserted: {stock_entry.name}")
			
			# Submit the stock entry
			stock_entry.submit()
			print(f"Stock Entry submitted: {stock_entry.name}")
			
			print(f"Stock Entry {stock_entry.name} created from Finish Weight {self.name}")
			
			frappe.msgprint(
				_("Stock Entry {0} created and submitted successfully").format(
					frappe.bold(stock_entry.name)
				),
				indicator="green",
				alert=True
			)
			
			print("=" * 50)
			print("Stock Entry creation completed successfully")
			print("=" * 50)
			
		except Exception as e:
			print("=" * 50)
			print(f"ERROR in Finish Weight on_submit: {str(e)}")
			print(f"Error type: {type(e).__name__}")
			import traceback
			print(traceback.format_exc())
			print("=" * 50)
			frappe.log_error(
				f"Error creating Stock Entry from Finish Weight {self.name}: {str(e)}",
				"Finish Weight Stock Entry Creation Error"
			)
			frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))
