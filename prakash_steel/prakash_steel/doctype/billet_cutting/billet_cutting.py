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
		print("=" * 50)
		print("Billet Cutting on_submit called")
		print(f"Billet Cutting Document: {self.name}")
		print(f"Billet Size (item_code): {self.billet_size}")
		print(f"Billet Weight (qty): {self.billet_weight}")
		print(f"RM Source Warehouse (s_warehouse): {self.rm_source_warehouse}")
		print(f"Posting Date: {self.posting_date}")
		print("=" * 50)

		# STOCK ENTRY CREATION COMMENTED OUT - WILL BE ENABLED LATER
		try:
			# Validate required fields
			if not self.billet_size:
				print("ERROR: billet_size is missing")
				frappe.throw(_("Billet Size is required to create Stock Entry"))

			if not self.billet_weight or self.billet_weight <= 0:
				print("ERROR: billet_weight is missing or invalid")
				frappe.throw(_("Billet Weight must be greater than 0"))

			if not self.rm_source_warehouse:
				print("ERROR: rm_source_warehouse is missing")
				frappe.throw(_("RM Source Warehouse is required to create Stock Entry"))

			print("All validations passed, creating Stock Entry...")

			# Get company from warehouse
			print(f"Getting company from warehouse: {self.rm_source_warehouse}")
			warehouse_doc = frappe.get_doc("Warehouse", self.rm_source_warehouse)
			company = warehouse_doc.company
			print(f"Company from warehouse: {company}")

			# Get item details for UOM
			print(f"Getting item details for: {self.billet_size}")
			item_doc = frappe.get_doc("Item", self.billet_size)
			stock_uom = item_doc.stock_uom or "Nos"
			print(f"Item Stock UOM: {stock_uom}")

			# Create Stock Entry
			print("Creating Stock Entry document...")
			stock_entry_data = {
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Issue",
				"company": company,
				"posting_date": self.posting_date or frappe.utils.today(),
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
			print(f"Stock Entry data: {stock_entry_data}")

			stock_entry = frappe.get_doc(stock_entry_data)
			print("Stock Entry document created, inserting...")
			stock_entry.insert()
			print(f"Stock Entry inserted: {stock_entry.name}")

			# Submit the stock entry
			print("Submitting Stock Entry...")
			stock_entry.submit()
			print(f"Stock Entry submitted: {stock_entry.name}")

			print(f"Stock Entry {stock_entry.name} created from Billet Cutting {self.name}")

			frappe.msgprint(
				_("Stock Entry {0} created and submitted successfully").format(frappe.bold(stock_entry.name)),
				indicator="green",
				alert=True,
			)

			print("=" * 50)
			print("Stock Entry creation completed successfully")
			print("=" * 50)

		except Exception as e:
			print("=" * 50)
			print(f"ERROR in Billet Cutting on_submit: {str(e)}")
			print(f"Error type: {type(e).__name__}")
			import traceback

			print(traceback.format_exc())
			print("=" * 50)
			frappe.log_error(
				f"Error creating Stock Entry from Billet Cutting {self.name}: {str(e)}",
				"Billet Cutting Stock Entry Creation Error",
			)
			frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))

		print("Stock Entry creation is currently commented out")
		print("=" * 50)
