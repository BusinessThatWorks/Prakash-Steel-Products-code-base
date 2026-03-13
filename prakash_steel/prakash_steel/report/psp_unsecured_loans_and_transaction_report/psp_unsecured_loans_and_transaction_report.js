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
			reqd: 1,
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

	// Ensure Total row only shows totals for specific columns
	formatter: function (value, row, column, data, default_formatter) {
		// Let Frappe format everything first
		let formatted_value = default_formatter(value, row, column, data);

		// If this is the Total row, blank out all columns
		// except Month (label) and the three amount fields
		if (data && data.name === "Total") {
			const allowed_fields = ["month", "interest_amount", "tds_10", "total_amount"];

			if (!allowed_fields.includes(column.fieldname)) {
				return "";
			}

			// Force the Month column to show the label "Total"
			if (column.fieldname === "month") {
				return __("Total");
			}
		}

		return formatted_value;
	},
};