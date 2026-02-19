# Copyright (c) 2026, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BrightBarProduction(Document):
	def on_submit(self):
		"""Create Stock Entry on submit"""
		try:
			# Validate required fields
			if not self.raw_material:
				frappe.throw(_("Raw Material is required to create Stock Entry"))

			if not self.actual_rm_consumption or self.actual_rm_consumption <= 0:
				frappe.throw(_("Actual RM Consumption must be greater than 0"))

			if not self.rm_source_warehouse:
				frappe.throw(_("RM Source Warehouse is required to create Stock Entry"))

			if not self.finished_good:
				frappe.throw(_("Finished Good is required to create Stock Entry"))

			if not self.fg_weight or self.fg_weight <= 0:
				frappe.throw(_("FG Weight must be greater than 0"))

			if not self.fg_target_warehouse:
				frappe.throw(_("FG Target Warehouse is required to create Stock Entry"))

			# Get company from source warehouse
			warehouse_doc = frappe.get_doc("Warehouse", self.rm_source_warehouse)
			company = warehouse_doc.company

			# Get item details for Raw Material UOM
			rm_item_doc = frappe.get_doc("Item", self.raw_material)
			rm_stock_uom = rm_item_doc.stock_uom or "Kg"

			# Get item details for Finished Good UOM
			fg_item_doc = frappe.get_doc("Item", self.finished_good)
			fg_stock_uom = fg_item_doc.stock_uom or "Kg"

			# Get posting_date from Production Plan
			production_plan_doc = frappe.get_doc("Production Plan", self.production_plan)
			posting_date = production_plan_doc.posting_date or self.production_date

			# Create Stock Entry with Manufacture type
			items = [
				{
					"item_code": self.raw_material,
					"qty": self.actual_rm_consumption,
					"s_warehouse": self.rm_source_warehouse,
					"t_warehouse": "",
					"stock_uom": rm_stock_uom,
					"uom": rm_stock_uom,
					"conversion_factor": 1.0,
					"is_finished_item": 0,
				},
				{
					"item_code": self.finished_good,
					"qty": self.fg_weight,
					"s_warehouse": "",
					"t_warehouse": self.fg_target_warehouse,
					"stock_uom": fg_stock_uom,
					"uom": fg_stock_uom,
					"conversion_factor": 1.0,
					"is_finished_item": 1,
				},
			]

			# Add End Cutting item (scrap/by-product) back to RM Source Warehouse, if provided
			if getattr(self, "end_cutting_item", None) and flt(getattr(self, "end_cutting_weight", 0)) > 0:
				items.append(
					{
						"item_code": self.end_cutting_item,
						"qty": flt(self.end_cutting_weight),
						"s_warehouse": "",
						"t_warehouse": self.fg_target_warehouse,
						"stock_uom": rm_stock_uom,
						"uom": rm_stock_uom,
						"conversion_factor": 1.0,
						"is_finished_item": 0,
					}
				)

			stock_entry_data = {
				"doctype": "Stock Entry",
				"stock_entry_type": "Manufacture",
				"company": company,
				"set_posting_time": 1,  # Enable custom posting date/time
				"posting_date": posting_date,
				"posting_time": frappe.utils.nowtime(),
				"items": items,
			}

			stock_entry = frappe.get_doc(stock_entry_data)
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
					(posting_date, stock_entry.name),
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
				f"Error creating Stock Entry from Bright Bar Production {self.name}: {str(e)}",
				"Bright Bar Production Stock Entry Creation Error",
			)
			frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))
