// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["PSP Unsecured Loans and Transaction Report"] = {
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
				"April",
				"May",
				"June",
				"July",
				"August",
				"September",
				"October",
				"November",
				"December",
				"January",
				"February",
				"March",
			].join("\n"),
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "account_head",
			label: __("Account Head"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				return {
					filters: [
						["parent_account", "in", [
							"Loan From Director - PSPL",
							"Loan From Shareholders - PSPL",
							"Unsecured Loan - PSPL"
						]],
						["is_group", "=", 0]
					]
				};
			},
			on_change: function () {
				frappe.query_report.refresh();
			},
		},
	],
};