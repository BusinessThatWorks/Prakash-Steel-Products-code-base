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
		// Format buffer_img column - show image if path exists
		if (column.fieldname === "buffer_img") {
			if (value && value.trim() !== "") {
				// Render image with proper styling
				return `<img src="${value}" style="height: 20px; width: auto; max-width: 40px;" />`;
			}
			return "";
		}

		// Format buffer flag text
		if (column.fieldname === "custom_buffer_flag") {
			if (value === "Yes" || value === "Buffer") {
				return `<span style="color: green;">${value}</span>`;
			}
			return value || "No";
		}

		// Format item code - show only item code (item name is in separate column)
		if (column.fieldname === "item_code") {
			return default_formatter(value, row, column, data);
		}

		// Default formatter for other fields
		return default_formatter(value, row, column, data);
	}
};

