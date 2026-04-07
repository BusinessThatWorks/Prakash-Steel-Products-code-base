// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["Item Wise Stock Balance"] = {
	"filters": [
		{
			"fieldname": "include_zero_stock",
			"label": __("Include Zero Stock Items"),
			"fieldtype": "Check",
			"default": 0
		}
	]
};
