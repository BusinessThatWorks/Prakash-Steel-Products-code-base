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

		// Format item code with full name
		if (column.fieldname === "item_code") {
			let item_display = value;
			if (data.item_name) {
				item_display = `${value}: ${data.item_name}`;
			}
			return default_formatter(item_display, row, column, data);
		}

		return default_formatter(value, row, column, data);
	}
};
