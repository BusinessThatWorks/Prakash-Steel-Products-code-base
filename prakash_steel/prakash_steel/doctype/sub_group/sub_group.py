# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import hashlib
import re


class SubGroup(Document):
	def _generate_name_from_sub_group_name(self):
		"""Generate a unique name (ID) from sub_group_name that fits within 140 character limit
		The sub_group_name field keeps its full value, but the name (ID) is truncated if needed.
		"""
		if not self.sub_group_name:
			return None
			
		# Get the full sub_group_name value (this will be preserved in the field)
		original_name = self.sub_group_name.strip()
		
		# Generate the name (ID) from sub_group_name
		# Clean the name to make it valid for Frappe (remove invalid characters)
		# frappe.scrub converts to lowercase and replaces spaces/special chars with hyphens
		name = frappe.scrub(original_name)
		
		# Replace multiple dashes/underscores with single one
		name = re.sub(r'[-_]+', '-', name)
		# Remove leading/trailing dashes
		name = name.strip('-')
		
		# If name is too long, truncate and add hash for uniqueness
		if len(name) > 130:
			# Truncate to 100 chars and add hash of full original name for uniqueness
			truncated = name[:100]
			name_hash = hashlib.md5(original_name.encode()).hexdigest()[:8]
			name = f"{truncated}-{name_hash}"
		
		# Final safety check - ensure it doesn't exceed 140 characters
		if len(name) > 140:
			name = name[:132] + "-" + hashlib.md5(original_name.encode()).hexdigest()[:7]
		
		# Check if name already exists, if so append a counter
		base_name = name
		counter = 1
		while frappe.db.exists("Sub Group", name):
			# If base name is long, truncate more to make room for counter
			if len(base_name) > 130:
				name = f"{base_name[:120]}-{counter}"
			else:
				name = f"{base_name}-{counter}"
			counter += 1
			if counter > 9999:  # Safety limit
				# Use hash-based name if counter gets too high
				name = base_name[:100] + "-" + hashlib.md5(f"{original_name}{counter}".encode()).hexdigest()[:8]
				break
		
		return name
	
	def autoname(self):
		"""Override autoname to generate name from sub_group_name with length limit"""
		if self.sub_group_name:
			# Generate a valid name from sub_group_name
			self.name = self._generate_name_from_sub_group_name()
	
	def validate(self):
		"""Ensure name is set correctly during validation"""
		if self.sub_group_name and not self.name:
			# Generate a valid name from sub_group_name
			self.name = self._generate_name_from_sub_group_name()
