// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt





frappe.query_reports["Testing report"] = {
	"filters": [
		{
			"fieldname": "bom",
			"label": __("BOM"),
			"fieldtype": "Link",
			"options": "BOM",
			"reqd": 1
		}
	]
};
