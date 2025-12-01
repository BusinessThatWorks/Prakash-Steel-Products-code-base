// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["BOM wise Buffer Details Report"] = {
	"filters": [
		{
			"fieldname": "bom",
			"label": __("BOM"),
			"fieldtype": "Link",
			"options": "BOM",
			"reqd": 1
		}
	],

	formatter: function (value, row, column, data, default_formatter) {
		// Format buffer impact column with icon
		if (column.fieldname === "buffer_impact") {
			if (value === "Yes") {
				return `<span class="indicator orange">●</span>`;
			}
			return "";
		}

		// Format buffer flag
		if (column.fieldname === "custom_buffer_flag") {
			if (value === "Yes") {
				return `<span style="color: green;">${value}</span>`;
			}
			return value || "No";
		}

		// Format item code - show only item code (item name is in separate column)
		if (column.fieldname === "item_code") {
			return default_formatter(value, row, column, data);
		}

		return default_formatter(value, row, column, data);
	}
};
