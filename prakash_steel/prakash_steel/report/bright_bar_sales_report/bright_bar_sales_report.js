// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["Bright Bar Sales report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 0
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 0
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 0
		},
		{
			"fieldname": "item_code",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item",
			"reqd": 0
		},
		{
			"fieldname": "category_name",
			"label": __("Category Name"),
			"fieldtype": "Data",
			"reqd": 0
		}
	]
};
