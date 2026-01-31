// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["SKU wise Sales History and Total Sales Trend"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -12),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "calculation_mode",
			"label": __("Calculation Mode"),
			"fieldtype": "Select",
			"options": ["Monthly", "Weekly"],
			"default": "Monthly",
			"reqd": 1
		}
	]
};
