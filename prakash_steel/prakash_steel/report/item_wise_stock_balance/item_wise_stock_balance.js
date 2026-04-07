// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["Item Wise Stock Balance"] = {
	"filters": [
		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "category_name",
			"label": __("Category Name"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "include_zero_stock",
			"label": __("Include Zero Stock Items"),
			"fieldtype": "Check",
			"default": 0
		}
	]
};
