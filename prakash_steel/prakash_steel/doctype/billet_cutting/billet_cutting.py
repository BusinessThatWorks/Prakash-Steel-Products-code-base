# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt


class BilletCutting(Document):
	def validate(self):
		"""Validate Billet Cutting document before save/submit"""
		self.validate_miss_billet_weight()
		self.validate_calculations()

	def validate_miss_billet_weight(self):
		"""Validate that miss_billet_weight is provided when miss_billet_pcs > 0"""
		miss_billet_pcs = flt(self.miss_billet_pcs) or 0
		miss_billet_weight = flt(self.miss_billet_weight) or 0

		if miss_billet_pcs > 0:
			if not miss_billet_weight or miss_billet_weight <= 0:
				frappe.throw(
					_("Miss Billet Weight is required when Miss Billet Pcs is greater than 0."),
					title=_("Validation Error"),
				)

	def validate_calculations(self):
		"""Validate calculated fields"""
		billet_weight = flt(self.billet_weight) or 0
		total_billet_cutting_pcs = flt(self.total_billet_cutting_pcs) or 0
		miss_billet_pcs = flt(self.miss_billet_pcs) or 0

		# Validate cutting_weight_per_pcs
		if billet_weight > 0 and total_billet_cutting_pcs > 0:
			expected_cutting_weight = billet_weight / total_billet_cutting_pcs
			actual_cutting_weight = flt(self.cutting_weight_per_pcs) or 0

			# Allow small floating point differences (0.01 tolerance)
			if abs(expected_cutting_weight - actual_cutting_weight) > 0.01:
				self.cutting_weight_per_pcs = expected_cutting_weight

		# Validate total_raw_material_pcs
		expected_total = total_billet_cutting_pcs + miss_billet_pcs
		actual_total = flt(self.total_raw_material_pcs) or 0

		if abs(expected_total - actual_total) > 0.01:
			self.total_raw_material_pcs = expected_total

	def on_submit(self):
		"""Create Stock Entry on submit"""
		try:
			# Validate required fields
			if not self.billet_size:
				frappe.throw(_("Billet Size is required to create Stock Entry"))

			if not self.billet_weight or self.billet_weight <= 0:
				frappe.throw(_("Billet Weight must be greater than 0"))

			if not self.rm_source_warehouse:
				frappe.throw(_("RM Source Warehouse is required to create Stock Entry"))

			# Get company from warehouse
			warehouse_doc = frappe.get_doc("Warehouse", self.rm_source_warehouse)
			company = warehouse_doc.company

			# Get item details for UOM
			item_doc = frappe.get_doc("Item", self.billet_size)
			stock_uom = item_doc.stock_uom or "Nos"

			# Get posting_date from Production Plan
			posting_date = self.posting_date or frappe.utils.today()
			if self.production_plan:
				production_plan_doc = frappe.get_doc("Production Plan", self.production_plan)
				posting_date = production_plan_doc.posting_date or self.posting_date or frappe.utils.today()

			# Create Stock Entry
			stock_entry_data = {
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Issue",
				"company": company,
				"set_posting_time": 1,  # Enable custom posting date/time
				"posting_date": posting_date,
				"posting_time": frappe.utils.nowtime(),
				"items": [
					{
						"item_code": self.billet_size,
						"qty": self.billet_weight,
						"s_warehouse": self.rm_source_warehouse,
						"stock_uom": stock_uom,
						"uom": stock_uom,
						"conversion_factor": 1.0,
					}
				],
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
				f"Error creating Stock Entry from Billet Cutting {self.name}: {str(e)}",
				"Billet Cutting Stock Entry Creation Error",
			)
			frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))
