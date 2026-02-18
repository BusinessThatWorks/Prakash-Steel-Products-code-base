# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FinishWeight(Document):
	def on_submit(self):
		"""Create Stock Entry on submit"""
		try:
			# Validate required fields
			if not self.item_code:
				frappe.throw(_("Item Code is required to create Stock Entry"))

			if not self.finish_weight or self.finish_weight <= 0:
				frappe.throw(_("Finish Weight must be greater than 0"))

			if not self.fg_target_warehouse:
				frappe.throw(_("FG Target Warehouse is required to create Stock Entry"))

			# Get company from warehouse
			warehouse_doc = frappe.get_doc("Warehouse", self.fg_target_warehouse)
			company = warehouse_doc.company

			# Get item details for UOM
			item_doc = frappe.get_doc("Item", self.item_code)
			stock_uom = item_doc.stock_uom or "Nos"

			# Get posting_date from Production Plan
			posting_date = self.posting_date or frappe.utils.today()
			if self.production_plan:
				production_plan_doc = frappe.get_doc("Production Plan", self.production_plan)
				posting_date = production_plan_doc.posting_date or self.posting_date or frappe.utils.today()

			# Create Stock Entry
			stock_entry = frappe.get_doc(
				{
					"doctype": "Stock Entry",
					"stock_entry_type": "Material Receipt",
					"company": company,
					"set_posting_time": 1,  # Enable custom posting date/time
					"posting_date": posting_date,
					"posting_time": frappe.utils.nowtime(),
					"items": [
						{
							"item_code": self.item_code,
							"qty": self.finish_weight,
							"t_warehouse": self.fg_target_warehouse,
							"stock_uom": stock_uom,
							"uom": stock_uom,
							"conversion_factor": 1.0,
						}
					],
				}
			)

			# Explicitly set set_posting_time and posting_date to ensure they're not overridden
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = posting_date
			stock_entry.insert()

			# Submit the stock entry
			# Ensure set_posting_time and posting_date are set before submit
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = posting_date
			stock_entry.submit()
			
			# Final check - if posting_date was changed, force set it via SQL
			if stock_entry.posting_date != posting_date:
				frappe.db.sql(
					"UPDATE `tabStock Entry` SET posting_date = %s WHERE name = %s",
					(posting_date, stock_entry.name)
				)
				frappe.db.commit()
				stock_entry.reload()

			frappe.msgprint(
				_("Stock Entry {0} created and submitted successfully").format(frappe.bold(stock_entry.name)),
				indicator="green",
				alert=True,
			)

		except Exception as e:
			frappe.log_error(
				f"Error creating Stock Entry from Finish Weight {self.name}: {str(e)}",
				"Finish Weight Stock Entry Creation Error",
			)
			frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))
