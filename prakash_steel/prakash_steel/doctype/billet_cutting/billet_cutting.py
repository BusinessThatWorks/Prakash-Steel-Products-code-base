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
					title=_("Validation Error")
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
