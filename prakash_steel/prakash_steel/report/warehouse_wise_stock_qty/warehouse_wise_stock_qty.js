// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["Warehouse wise stock qty"] = {
	"filters": [
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"default": "",
			"reqd": 0
		}
	]
};
