// All SKU types across all 4 combinations
const ALL_SKU_TYPES = ["PTA", "BOTA", "TRMTA", "PTO", "BOTO", "TRMTO", "BBMTA", "RBMTA", "BBMTO", "RBMTO"];

frappe.query_reports["PO Snapshot Daily View"] = {
	filters: [
		{
			fieldname: "snapshot_date",
			label: __("Snapshot Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "sku_type",
			label: __("SKU Type"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return ALL_SKU_TYPES
					.filter((s) => !txt || s.toLowerCase().includes(txt.toLowerCase()))
					.map((s) => ({ value: s, label: s, description: "" }));
			},
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "on_hand_colour" && data && data.on_hand_colour) {
			const colour = data.on_hand_colour;
			const map = {
				BLACK: { bg: "#000000", text: "#FFFFFF" },
				RED: { bg: "#FF0000", text: "#FFFFFF" },
				YELLOW: { bg: "#FFFF00", text: "#000000" },
				GREEN: { bg: "#00FF00", text: "#000000" },
				WHITE: { bg: "#FFFFFF", text: "#000000" },
			};
			const c = map[colour];
			if (c) {
				return `<div style="background-color:${c.bg};padding:4px;text-align:center;font-weight:bold;color:${c.text};">${colour}</div>`;
			}
		}

		if (["child_full_kit_status", "child_wip_open_po_full_kit_status"].includes(column.fieldname) && data) {
			const raw = data[column.fieldname] || "";
			const map = {
				"full-kit": { bg: "#4dff88", text: "#000000" },
				partial: { bg: "#ffff99", text: "#000000" },
				pending: { bg: "#ff9999", text: "#000000" },
			};
			const c = map[raw.toLowerCase()];
			if (c) {
				return `<div style="background-color:${c.bg};padding:4px;text-align:center;font-weight:bold;color:${c.text};">${raw}</div>`;
			}
		}

		return value;
	},
};
