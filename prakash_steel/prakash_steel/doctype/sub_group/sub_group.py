# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class SubGroup(Document):
	def autoname(self):
		self.name = self.sub_group_id
