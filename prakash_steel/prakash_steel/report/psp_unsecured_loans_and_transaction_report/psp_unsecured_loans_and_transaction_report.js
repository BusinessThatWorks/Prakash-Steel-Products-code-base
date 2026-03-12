// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["Unsecured Loans Interest Report"] = {
	filters: [
		{
			fieldname: "financial_year",
			label: __("Financial Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1,
			on_change: function () {
					frappe.query_report.set_filter_value("month", "");
				frappe.query_report.set_filter_value("account_head", "");
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				"",
				"January",
				"February",
				"March",
				"April",
				"May",
				"June",
				"July",
				"August",
				"September",
				"October",
				"November",
				"December",
			].join("\n"),
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "account_head",
			label: __("Account Head"),
			fieldtype: "Link",
			options: "Unsecured Loans and Transaction",
			get_query: function () {
				return {
					filters: {}
				};
			},
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
	],
};