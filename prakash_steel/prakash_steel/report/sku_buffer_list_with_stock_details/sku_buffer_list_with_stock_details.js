// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["SKU Buffer List With Stock Details"] = {
	"filters": [
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
			width: "120",
		},
		{
			fieldname: "sku_type",
			label: __("SKU Type"),
			fieldtype: "MultiSelectList",
			width: "120",
			get_data: function (txt) {
				let sku_types = [
					"BBMTA", "RBMTA", "BBMTO", "RBMTO",
					"BOTA", "BOTO", "PTA", "PTO",
					"TRMTA", "TRMTO"
				];
				let options = [];
				for (let sku of sku_types) {
					if (!txt || sku.toLowerCase().includes(txt.toLowerCase())) {
						options.push({
							value: sku,
							label: __(sku),
							description: "",
						});
					}
				}
				return options;
			},
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
			width: "120",
		},
		{
			fieldname: "category_name",
			label: __("Category Name"),
			fieldtype: "Data",
			width: "120",
			hidden: 1,
		},
		{
			fieldname: "item_type",
			label: __("Item Type"),
			fieldtype: "MultiSelectList",
			width: "120",
			get_data: function (txt) {
				let item_types = ["BB", "RB", "BO", "RM", "Traded"];
				let options = [];
				for (let item_type of item_types) {
					if (!txt || item_type.toLowerCase().includes(txt.toLowerCase())) {
						options.push({
							value: item_type,
							label: __(item_type),
							description: "",
						});
					}
				}
				return options;
			},
		},
		{
			fieldname: "buffer_flag",
			label: __("Buffer Flag"),
			fieldtype: "Select",
			options: "\nBuffer\nNon-Buffer",
			width: "120",
		},
	]
};
